"""Subsanar / modify model.

The modify model shares fields with create but may include 'rechazo_previo'
defaulting to 'N'. Business validations are similar to create, but callers must set
'rechazo_previo' appropriately.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.sif.models.factura_create import FacturaInput

from .especiales import Especial
from .ids import IdOtro
from .lineas import LineaFactura
from .validators import importe_matches_total


class FacturaModifyInput(BaseModel):
    serie: str = Field(..., max_length=60)
    numero: str = Field(..., max_length=60)
    fecha_expedicion: date
    rechazo_previo: str = Field("N", pattern=r"^(N|S|X)$")
    tipo_factura: str = Field(..., pattern=r"^(F1|F2|R1|R2|R3|R4|R5|F3)$")
    descripcion: str = Field(..., min_length=1, max_length=500)
    lineas: List[LineaFactura] = Field(..., min_length=1, max_length=12)
    importe_total: Decimal = Field(...)
    fecha_operacion: Optional[date] = None
    nif: Optional[str] = None
    id_otro: Optional[IdOtro] = None
    nombre: Optional[str] = Field(None, max_length=120)
    validar_destinatario: bool = True
    tipo_rectificativa: Optional[str] = None
    incidencia: Optional[str] = None
    especial: Optional[Especial] = None

    model_config = ConfigDict()

    @field_validator("fecha_expedicion", "fecha_operacion", mode="before")
    @classmethod
    def parse_date(cls, v: str | date | None) -> date | None:
        if isinstance(v, str):
            return datetime.strptime(v, "%d-%m-%Y").date()
        return v

    @model_validator(mode="after")
    def business_validations(self) -> Self:
        # Basic validations similar to create
        tipo = (self.tipo_factura or "").upper()
        if tipo in ("F2", "R5"):
            if self.nif or self.nombre or self.id_otro:
                raise ValueError(
                    f"Para tipo {tipo} no se permite informar destinatario"
                )
        if not importe_matches_total(self.importe_total, self.lineas):
            raise ValueError("Importe total no coincide con suma de líneas")
        if self.fecha_expedicion > date.today():
            raise ValueError("FechaExpedicion no puede ser futura")
        return self


# ===== Schemas para operaciones especiales =====


class SubsanacionInput(FacturaInput):
    """Subsanación de factura (PUT /modify)"""

    rechazo_previo: str = Field("N", pattern=r"^(N|S|X)$")
