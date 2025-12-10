from datetime import date, datetime
from typing import Any, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import ErrorResponse, HealthOut, RegistroEstado, RegistroOut
from app.config.settings import settings
from app.domain.models.models import InstalacionSIF, RegistroFacturacion
from app.infrastructure.database import get_db
from app.infrastructure.security.auth import verificar_api_key

router = APIRouter()


def formatear_fecha(dt: date) -> str:
    """Convierte date a dd-mm-yyyy"""
    return dt.strftime("%d-%m-%Y") if dt else ""


@router.get(
    "/status",
    response_model=RegistroEstado,
    responses={404: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Estado registro",
    description="Consulta el estado de un registro de facturación por UUID",
)
async def consultar_estado_registro(
    uuid: UUID = Query(..., description="UUID del registro"),
    instalacion: InstalacionSIF = Depends(verificar_api_key),
    db: AsyncSession = Depends(get_db),
) -> RegistroEstado:
    """
    GET /v1/status?uuid=...

    Devuelve el estado actual del registro de facturación.
    """
    stmt = select(RegistroFacturacion).where(RegistroFacturacion.id == uuid)
    result = await db.execute(stmt)
    registro = result.scalar_one_or_none()

    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado"
        )

    # Verificar que pertenece al NIF autenticado
    if registro.instalacion_sif_id != instalacion.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para consultar este registro",
        )

    # Mapear estados internos a estados de API
    estado_api = {
        "pendiente": "Pendiente",
        "correcto": "Correcto",
        "aceptado_con_errores": "Aceptado con errores",
        "incorrecto": "Incorrecto",
        "duplicado": "Duplicado",
        "anulado": "Anulado",
        "factura_inexistente": "Factura inexistente",
        "no_registrado": "No registrado",
        "error_servidor_aeat": "Error servidor AEAT",
    }.get(registro.estado, registro.estado)

    return RegistroEstado(
        nif=registro.instalacion_sif.obligado.nif,
        serie=registro.serie,
        numero=registro.numero,
        fecha_expedicion=registro.fecha_expedicion,
        operacion=registro.operacion,
        estado=estado_api,
        url=registro.qr_data,
        qr=None,  # No devolver QR en consultas (para ahorrar bandwidth)
        codigo_error=registro.aeat_codigo_error,
        mensaje_error=registro.aeat_descripcion_error,
        estado_registro_duplicado=None,
    )


class FechaRango(BaseModel):
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None

    @field_validator("fecha_desde", "fecha_hasta", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> date | None:
        if v is None:
            return None
        if isinstance(v, str):
            return datetime.strptime(v, "%d-%m-%Y").date()
        if isinstance(v, date):
            return v
        # Opcional: lanzar error si el tipo es inesperado
        raise ValueError(f"Valor no válido para fecha: {v}")


@router.get(
    "/registros",
    response_model=list[RegistroOut],
    summary="Listar registros",
    description="Lista los registros de facturación del NIF autenticado",
)
async def listar_registros(
    instalacion: InstalacionSIF = Depends(verificar_api_key),
    db: AsyncSession = Depends(get_db),
    limite: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    estado: str = Query(None),
    fecha_desde: str = Query(None, pattern=r"\d{2}-\d{2}-\d{4}"),
    fecha_hasta: str = Query(None, pattern=r"\d{2}-\d{2}-\d{4}"),
) -> list[RegistroOut]:
    """
    GET /v1/registros

    Lista registros con paginación y filtros.
    """
    stmt = select(RegistroFacturacion).where(
        RegistroFacturacion.instalacion_sif_id == instalacion.id
    )

    if estado:
        stmt = stmt.where(RegistroFacturacion.estado == estado)

    fechas = FechaRango.model_validate(
        {"fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta}
    )

    if fechas.fecha_desde:
        stmt = stmt.where(RegistroFacturacion.fecha_expedicion >= fechas.fecha_desde)

    if fechas.fecha_hasta:
        stmt = stmt.where(RegistroFacturacion.fecha_expedicion <= fechas.fecha_hasta)

    stmt = (
        stmt.order_by(RegistroFacturacion.created_at.desc())
        .limit(limite)
        .offset(offset)
    )

    result = await db.execute(stmt)
    registros = result.scalars().all()

    return [
        RegistroOut(
            uuid=str(r.id),
            serie=r.serie,
            numero=r.numero,
            fecha_expedicion=formatear_fecha(r.fecha_expedicion),
            operacion=r.operacion,
            estado=r.estado,
            importe_total=str(r.importe_total) if r.importe_total else None,
            huella=r.huella,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in registros
    ]


@router.get(
    "/health",
    summary="Estado API",
    description="Estado de la API key e información del NIF",
)
async def health_check(
    instalacion: InstalacionSIF = Depends(verificar_api_key),
) -> HealthOut:
    """
    GET /v1/health

    Devuelve estado, NIF y entorno.
    """
    return HealthOut(estado="OK", nif=instalacion.obligado.nif, entorno=settings.env)


class ConsultaFacturaInput(BaseModel):
    """Consulta estado factura en AEAT (POST /status)"""

    serie: str
    numero: str
    fecha_expedicion: date
    fecha_operacion: Optional[date] = None

    @field_validator("fecha_expedicion", "fecha_operacion", mode="before")
    def parse_date(cls, v: Union[str, date, None]) -> Optional[date]:
        if isinstance(v, str):
            return datetime.strptime(v, "%d-%m-%Y").date()
        return v
