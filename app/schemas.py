from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from decimal import Decimal


# ===== Schemas de entrada (SIF -> API) =====

class LineaFactura(BaseModel):
    """Línea de factura según especificación AEAT"""
    base_imponible: str = Field(..., pattern=r"(\+|-)?\d{1,12}(\.\d{0,2})?")
    tipo_impositivo: Optional[str] = Field(None, pattern=r"\d{1,3}(\.\d{0,2})?")
    cuota_repercutida: Optional[str] = Field(None, pattern=r"(\+|-)?\d{1,12}(\.\d{0,2})?")
    impuesto: Optional[str] = Field("01", pattern=r"^(01|02|03|05)$")
    calificacion_operacion: Optional[str] = Field("S1", pattern=r"^(S1|S2|N1|N2)$")
    clave_regimen: Optional[str] = None
    operacion_exenta: Optional[str] = None
    base_imponible_a_coste: Optional[str] = None
    tipo_recargo_equivalencia: Optional[str] = None
    cuota_recargo_equivalencia: Optional[str] = None


class IdOtro(BaseModel):
    """Identificador alternativo al NIF"""
    codigo_pais: Optional[str] = None
    id_type: str = Field(..., pattern=r"^(02|03|04|05|06|07)$")
    id: str = Field(..., max_length=20)


class FacturaInput(BaseModel):
    """Schema de entrada de una factura desde el SIF - VERSIÓN MÍNIMA"""
    serie: str = Field(..., max_length=60)
    numero: str = Field(..., max_length=60)
    fecha_expedicion: str = Field(..., pattern=r"\d{2}-\d{2}-\d{4}")
    fecha_operacion: Optional[str] = Field(None, pattern=r"\d{2}-\d{2}-\d{4}")
    
    tipo_factura: str = Field(..., pattern=r"^(F1|F2|R1|R2|R3|R4|R5|F3)$")
    descripcion: str = Field(..., min_length=1, max_length=500)
    
    lineas: List[LineaFactura] = Field(..., min_items=1, max_items=12)
    importe_total: str = Field(..., pattern=r"(\+|-)?\d{1,12}(\.\d{0,2})?")
    
    # Destinatario (opcional para F2/R5)
    nif: Optional[str] = Field(None, max_length=20)
    id_otro: Optional[IdOtro] = None
    nombre: Optional[str] = Field(None, max_length=120)
    
    # Opcionales
    validar_destinatario: bool = True
    tipo_rectificativa: Optional[str] = None
    importe_rectificativa: Optional[dict] = None
    facturas_rectificadas: Optional[List[dict]] = None
    facturas_sustituidas: Optional[List[dict]] = None
    incidencia: Optional[str] = None
    especial: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "serie": "A",
                "numero": "234634",
                "fecha_expedicion": "15-11-2024",
                "tipo_factura": "F1",
                "descripcion": "Prestación de servicios",
                "nif": "A15022510",
                "nombre": "Cliente SL",
                "lineas": [{
                    "base_imponible": "200.00",
                    "tipo_impositivo": "21",
                    "cuota_repercutida": "42.00"
                }],
                "importe_total": "242.00"
            }
        }


# ===== Schemas de respuesta =====

class FacturaResponse(BaseModel):
    """Respuesta inmediata al SIF tras recibir factura (igual que Verifactu)"""
    uuid: UUID = Field(..., description="Identificador único del registro")
    estado: str = Field(default="Pendiente", description="Estado del registro")
    url: str = Field(..., description="URL de verificación del código QR")
    qr: str = Field(..., description="Código QR en base64")
    huella: Optional[str] = Field(None, description="Huella o hash del registro")
    
    class Config:
        from_attributes = True


class RegistroEstado(BaseModel):
    """Estado de un registro de facturación (GET /status?uuid=...)"""
    nif: str
    serie: str
    numero: str
    fecha_expedicion: str
    operacion: str
    estado: str
    url: Optional[str] = None
    qr: Optional[str] = None
    codigo_error: Optional[str] = None
    mensaje_error: Optional[str] = None
    estado_registro_duplicado: Optional[str] = None
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Respuesta de error estándar"""
    error: str


# ===== Schemas para operaciones especiales =====

class SubsanacionInput(FacturaInput):
    """Subsanación de factura (PUT /modify)"""
    rechazo_previo: str = Field("N", pattern=r"^(N|S|X)$")


class AnulacionInput(BaseModel):
    """Anulación de factura (POST /cancel)"""
    serie: str
    numero: str
    fecha_expedicion: str = Field(..., pattern=r"\d{2}-\d{2}-\d{4}")
    rechazo_previo: str = Field("N", pattern=r"^(N|S)$")
    sin_registro_previo: str = Field("N", pattern=r"^(N|S)$")
    incidencia: Optional[str] = None


class ConsultaFacturaInput(BaseModel):
    """Consulta estado factura en AEAT (POST /status)"""
    serie: str
    numero: str
    fecha_expedicion: str = Field(..., pattern=r"\d{2}-\d{2}-\d{4}")
    fecha_operacion: Optional[str] = Field(None, pattern=r"\d{2}-\d{2}-\d{4}")


# ===== Schemas internos =====

class HuellaCalculo(BaseModel):
    """Datos para calcular la huella"""
    nif_emisor: str
    numero_factura: str
    fecha_expedicion: str
    tipo_factura: str
    cuota_total: Decimal
    importe_total: Decimal
    huella_anterior: Optional[str] = None


class WebhookPayload(BaseModel):
    """Payload enviado a los webhooks"""
    evento: str
    timestamp: datetime
    datos: dict