import logging
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_nif
from app.config import settings
from app.core.huella import calcular_huella
from app.core.qr_generator import generar_qr
from app.database import get_db
from app.models import ObligadoTributario, RegistroFacturacion
from app.schemas import ErrorResponse, FacturaInput, FacturaResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def parsear_fecha(fecha_str: str) -> datetime:
    """Convierte dd-mm-yyyy a datetime"""
    return datetime.strptime(fecha_str, "%d-%m-%Y")


def calcular_cuota_total(lineas: list) -> Decimal:
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
    description="Crea un registro de facturación nuevo. Responde inmediatamente con el QR.",
)
async def crear_factura(
    request: Request,
    factura_input: FacturaInput,
    nif: str = Depends(get_current_nif),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint principal: POST /v1/create

    Responde INMEDIATAMENTE con:
    - UUID del registro
    - QR en base64
    - URL del QR
    - Estado: "Pendiente"
    - Huella

    El procesamiento real (XML, firma, envío AEAT) se hace en background.
    """

    try:
        # Verificar obligado tributario activo
        stmt = select(ObligadoTributario).where(
            ObligadoTributario.nif == nif, ObligadoTributario.activo == True
        )
        result = await db.execute(stmt)
        obligado = result.scalar_one_or_none()

        if not obligado:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Obligado tributario no encontrado o inactivo",
            )

        # Parsear fechas
        fecha_expedicion = parsear_fecha(factura_input.fecha_expedicion)
        fecha_operacion = None
        if factura_input.fecha_operacion:
            fecha_operacion = parsear_fecha(factura_input.fecha_operacion)

        # Verificar duplicados (NIF + serie + numero + fecha_expedicion)
        stmt_dup = select(RegistroFacturacion).where(
            RegistroFacturacion.nif_emisor == nif,
            RegistroFacturacion.serie == factura_input.serie,
            RegistroFacturacion.numero == factura_input.numero,
            RegistroFacturacion.fecha_expedicion == fecha_expedicion,
        )
        result_dup = await db.execute(stmt_dup)
        duplicado = result_dup.scalar_one_or_none()

        if duplicado:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un registro con serie {factura_input.serie}, número {factura_input.numero} y fecha {factura_input.fecha_expedicion}",
            )

        # Calcular totales
        cuota_total = calcular_cuota_total(
            [linea.model_dump() for linea in factura_input.lineas]
        )
        importe_total = Decimal(factura_input.importe_total)

        # Obtener huella anterior (última del NIF)
        stmt_anterior = (
            select(RegistroFacturacion)
            .where(
                RegistroFacturacion.nif_emisor == nif,
                RegistroFacturacion.estado.in_(["correcto", "aceptado_con_errores"]),
            )
            .order_by(RegistroFacturacion.created_at.desc())
            .limit(1)
        )
        result_anterior = await db.execute(stmt_anterior)
        factura_anterior = result_anterior.scalar_one_or_none()

        huella_anterior = factura_anterior.huella if factura_anterior else None

        # Calcular huella
        try:
            huella = calcular_huella(
                nif_emisor=nif,
                numero_serie=f"{factura_input.serie}{factura_input.numero}",
                fecha_expedicion=factura_input.fecha_expedicion,
                tipo_factura=factura_input.tipo_factura,
                cuota_total=cuota_total,
                importe_total=importe_total,
                huella_anterior=huella_anterior,
            )
        except Exception as e:
            logger.error(f"Error calculando huella: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error calculando huella: {str(e)}",
            )

        # Generar URL del QR según especificación AEAT
        # IMPORTANTE: Aplicar URL encoding a los parámetros (especialmente numserie puede tener &)
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
            f"?nif={quote(nif)}"
            f"&numserie={quote(num_serie)}"
            f"&fecha={quote(factura_input.fecha_expedicion)}"
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
            nif_emisor=nif,
            serie=factura_input.serie,
            numero=factura_input.numero,
            fecha_expedicion=fecha_expedicion,
            fecha_operacion=fecha_operacion,
            operacion="Alta",
            tipo_factura=factura_input.tipo_factura,
            factura_json=factura_input.model_dump(mode="json"),
            importe_total=importe_total,
            cuota_total=cuota_total,
            descripcion=factura_input.descripcion,
            huella=huella,
            huella_anterior=huella_anterior,
            qr_data=qr_url,
            estado="pendiente_envio",
        )

        db.add(registro)
        await db.commit()
        await db.refresh(registro)

        logger.info(
            f"Factura creada: {registro.id} - {factura_input.serie}{factura_input.numero}"
        )

        # TODO: Encolar para procesamiento en background
        # await enqueue_registro(registro.id)

        return FacturaResponse(
            uuid=registro.id,
            estado="Pendiente",
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
