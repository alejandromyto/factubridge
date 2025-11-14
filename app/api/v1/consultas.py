from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_nif
from app.config import settings
from app.database import get_db
from app.models import RegistroFacturacion
from app.schemas import ErrorResponse, RegistroEstado

router = APIRouter()


def formatear_fecha(dt: datetime) -> str:
    """Convierte datetime a dd-mm-yyyy"""
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
    nif: str = Depends(get_current_nif),
    db: AsyncSession = Depends(get_db),
):
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
    if registro.nif_emisor != nif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para consultar este registro",
        )

    # Mapear estados internos a estados de API
    estado_api = {
        "pendiente_envio": "Pendiente",
        "enviando": "Pendiente",
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
        nif=registro.nif_emisor,
        serie=registro.serie,
        numero=registro.numero,
        fecha_expedicion=formatear_fecha(registro.fecha_expedicion),
        operacion=registro.operacion,
        estado=estado_api,
        url=registro.qr_data,
        qr=None,  # No devolver QR en consultas (para ahorrar bandwidth)
        codigo_error=registro.codigo_error,
        mensaje_error=registro.mensaje_error,
        estado_registro_duplicado=None,
    )


@router.get(
    "/registros",
    response_model=List[dict],
    summary="Listar registros",
    description="Lista los registros de facturación del NIF autenticado",
)
async def listar_registros(
    nif: str = Depends(get_current_nif),
    db: AsyncSession = Depends(get_db),
    limite: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    estado: str = Query(None),
    fecha_desde: str = Query(None, pattern=r"\d{2}-\d{2}-\d{4}"),
    fecha_hasta: str = Query(None, pattern=r"\d{2}-\d{2}-\d{4}"),
):
    """
    GET /v1/registros

    Lista registros con paginación y filtros.
    """
    stmt = select(RegistroFacturacion).where(RegistroFacturacion.nif_emisor == nif)

    if estado:
        stmt = stmt.where(RegistroFacturacion.estado == estado)

    if fecha_desde:
        fecha_dt = datetime.strptime(fecha_desde, "%d-%m-%Y")
        stmt = stmt.where(RegistroFacturacion.fecha_expedicion >= fecha_dt)

    if fecha_hasta:
        fecha_dt = datetime.strptime(fecha_hasta, "%d-%m-%Y")
        stmt = stmt.where(RegistroFacturacion.fecha_expedicion <= fecha_dt)

    stmt = (
        stmt.order_by(RegistroFacturacion.created_at.desc())
        .limit(limite)
        .offset(offset)
    )

    result = await db.execute(stmt)
    registros = result.scalars().all()

    return [
        {
            "uuid": str(r.id),
            "serie": r.serie,
            "numero": r.numero,
            "fecha_expedicion": formatear_fecha(r.fecha_expedicion),
            "operacion": r.operacion,
            "estado": r.estado,
            "importe_total": str(r.importe_total) if r.importe_total else None,
            "huella": r.huella,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in registros
    ]


@router.get(
    "/health",
    summary="Estado API",
    description="Estado de la API key y información del NIF",
)
async def health_check(
    nif: str = Depends(get_current_nif), db: AsyncSession = Depends(get_db)
):
    """
    GET /v1/health

    Devuelve estado, NIF y entorno.
    """
    return {"estado": "OK", "nif": nif, "entorno": settings.env}
