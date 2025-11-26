import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verificar_api_key
from app.config import settings
from app.core.huella import calcular_huella
from app.core.qr_generator import generar_qr
from app.database import get_db
from app.models import InstalacionSIF, RegistroFacturacion
from app.schemas import ErrorResponse, FacturaInput, FacturaResponse
from app.workers.queue_service import enqueue_registro

router = APIRouter()
logger = logging.getLogger(__name__)


def date_to_str(d: date) -> str:
    """Convierte date a string dd-mm-yyyy para AEAT"""
    return d.strftime("%d-%m-%Y")


def calcular_cuota_total(lineas: List[Dict[str, Any]]) -> Decimal:
    """Calcula la cuota total de las líneas"""
    total = Decimal("0.00")
    for linea in lineas:
        if linea.get("cuota_repercutida"):
            total += Decimal(linea["cuota_repercutida"])
        if linea.get("cuota_recargo_equivalencia"):
            total += Decimal(linea["cuota_recargo_equivalencia"])
    return total


@router.post(
    "/create",
    response_model=FacturaResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Crear factura nueva",
    description="Crea un registro de facturación nuevo."
    " Responde inmediatamente con el QR.",
)
async def crear_factura(
    request: Request,
    factura_input: FacturaInput,
    instalacion: InstalacionSIF = Depends(verificar_api_key),
    db: AsyncSession = Depends(get_db),
) -> FacturaResponse:
    """
    Endpoint principal: POST /v1/create

    Responde INMEDIATAMENTE con:
    - UUID del registro
    - QR en base64
    - URL del QR
    - Estado: "pendiente"
    - Huella

    El procesamiento real (XML, firma?, envío AEAT) se hace en background.
    """
    try:
        obligado = instalacion.obligado

        # Verificar duplicados (SIF + serie + numero + fecha_expedicion)
        stmt_dup = select(RegistroFacturacion).where(
            and_(
                RegistroFacturacion.instalacion_sif_id == instalacion.id,
                RegistroFacturacion.serie == factura_input.serie,
                RegistroFacturacion.numero == factura_input.numero,
                RegistroFacturacion.fecha_expedicion == factura_input.fecha_expedicion,
            )
        )
        result_dup = await db.execute(stmt_dup)
        duplicado = result_dup.scalar_one_or_none()

        if duplicado:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Factura duplicada: {factura_input.serie}/{factura_input.numero} "
                    f"({factura_input.fecha_expedicion})"
                ),
            )

        # Calcular totales
        cuota_total = calcular_cuota_total(
            [linea.model_dump() for linea in factura_input.lineas],
        )
        importe_total = Decimal(factura_input.importe_total)
        if factura_input.tipo_factura == "F2":
            if importe_total >= Decimal("3000"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Factura simplificada (F2) supera "
                        "importe máximo permitido (3.000)."
                    ),
                )
        # Obtener huella anterior (última del NIF)
        stmt_anterior = (
            select(RegistroFacturacion)
            .where(
                RegistroFacturacion.instalacion_sif_id == instalacion.id,
                # 🔑 FILTRO CRUCIAL: Solo registros válidos para el encadenamiento
                # RegistroFacturacion.estado.in_(
                #     [
                #         EstadoRegistroFacturacion.CORRECTO,
                #         EstadoRegistroFacturacion.ACEPTADO_CON_ERRORES,
                #     ]
                # ),
            )
            .order_by(RegistroFacturacion.created_at.desc())
            .limit(1)
            # 🔒 CLÁUSULA DE BLOQUEO PARA CONTROL DE CONCURRENCIA
            # Esto garantiza atomicidad, impidiendo que otra tarea inserte un CORRECTO
            # en el gap que transcurre entre esta consulta y el envío del xml a la AEAT.
            .with_for_update()
        )
        result_anterior = await db.execute(stmt_anterior)
        factura_anterior = result_anterior.scalar_one_or_none()

        anterior_huella = factura_anterior.huella if factura_anterior else None

        # Calcular huella
        try:
            huella = calcular_huella(
                nif_emisor=obligado.nif,
                numero_serie=f"{factura_input.serie}{factura_input.numero}",
                fecha_expedicion=date_to_str(factura_input.fecha_expedicion),
                tipo_factura=factura_input.tipo_factura.value,
                cuota_total=cuota_total,
                importe_total=importe_total,
                huella_anterior=anterior_huella,
            )
        except Exception as e:
            logger.error(f"Error calculando huella: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error calculando huella: {str(e)}",
            )

        # Generar URL del QR según especificación AEAT
        # IMPORTANTE: Aplicar URL encoding a los parámetros
        # (especialmente numserie puede tener &)
        from urllib.parse import quote

        num_serie = f"{factura_input.serie}{factura_input.numero}"

        # URL base según entorno y tipo de sistema
        base_url = (
            "https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQR"
            if settings.env != "production"
            else "https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQR"
        )

        # Construir URL con parámetros codificados
        qr_url = (
            f"{base_url}"
            f"?nif={quote(obligado.nif)}"
            f"&numserie={quote(num_serie)}"
            f"&fecha={quote(date_to_str(factura_input.fecha_expedicion))}"
            f"&importe={factura_input.importe_total}"
        )

        # Generar QR en base64
        try:
            qr_base64 = generar_qr(qr_url)
        except Exception as e:
            logger.error(f"Error generando QR: {e}")
            qr_base64 = ""

        # Crear registro

        registro = RegistroFacturacion(
            instalacion_sif_id=instalacion.id,
            serie=factura_input.serie,
            numero=factura_input.numero,
            fecha_expedicion=factura_input.fecha_expedicion,
            fecha_operacion=factura_input.fecha_operacion,
            destinatario_nif=factura_input.nif,
            destinatario_nombre=factura_input.nombre,
            operacion="Alta",
            tipo_factura=factura_input.tipo_factura,
            factura_json=factura_input.model_dump(mode="json"),
            importe_total=importe_total,
            cuota_total=cuota_total,
            descripcion=factura_input.descripcion,
            huella=huella,
            anterior_huella=(
                factura_anterior.anterior_huella if factura_anterior else None
            ),
            anterior_serie=factura_anterior.serie if factura_anterior else None,
            anterior_numero=factura_anterior.numero if factura_anterior else None,
            anterior_fecha_expedicion=(
                factura_anterior.fecha_expedicion if factura_anterior else None
            ),
            qr_data=qr_url,
            estado="pendiente",
        )

        db.add(registro)
        await db.commit()
        await db.refresh(registro)

        logger.info(
            f"Factura creada: "
            f"({registro.id} - {factura_input.serie}{factura_input.numero})"
        )

        # 🔑 Enlace al worker
        enqueue_registro(registro.id)

        return FacturaResponse(
            uuid=registro.id,
            estado="pendiente",
            url=qr_url,
            qr=qr_base64,
            huella=huella,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando factura: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) if settings.debug else "Error interno del servidor",
        )
