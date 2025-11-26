from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ===== Schemas de respuesta =====


class FacturaResponse(BaseModel):
    """Respuesta inmediata al SIF tras recibir factura (igual que Verifactu)"""

    uuid: UUID = Field(..., description="Identificador único del registro")
    estado: str = Field(default="Pendiente", description="Estado del registro")
    url: str = Field(..., description="URL de verificación del código QR")
    qr: str = Field(..., description="Código QR en base64")
    huella: Optional[str] = Field(None, description="Huella o hash del registro")

    model_config = ConfigDict(from_attributes=True)


class RegistroEstado(BaseModel):
    """Estado de un registro de facturación (GET /status?uuid=...)"""

    nif: str
    serie: str
    numero: str
    fecha_expedicion: date
    operacion: str
    estado: str
    url: Optional[str] = None
    qr: Optional[str] = None
    codigo_error: Optional[str] = None
    mensaje_error: Optional[str] = None
    estado_registro_duplicado: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Respuesta de error estándar"""

    error: str


class HealthOut(BaseModel):
    estado: str
    nif: str
    entorno: str


class RegistroOut(BaseModel):
    uuid: str
    serie: str
    numero: str
    fecha_expedicion: str
    operacion: str
    estado: str
    importe_total: Optional[str]
    huella: str
    created_at: Optional[str]
