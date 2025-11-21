"""Cancel model for invoice annulment.

For cancellations the payload is similar to create/modify but semantics differ
(sin_registro_previo, rechazo_previo, etc).
This module provides a focused schema for cancellation requests.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from .ids import IdOtro
from .lineas import LineaFactura
from .validators import parse_dd_mm_yyyy


class FacturaCancelInput(BaseModel):
    serie: str = Field(..., max_length=60)
    numero: str = Field(..., max_length=60)
    fecha_expedicion: date
    tipo_factura: str = Field(..., pattern=r"^(F1|F2|R1|R2|R3|R4|R5|F3)$")
    descripcion: Optional[str] = Field(None, max_length=500)
    lineas: Optional[List[LineaFactura]] = None
    importe_total: Optional[Decimal] = None

    fecha_operacion: Optional[date] = None
    nif: Optional[str] = None
    id_otro: Optional[IdOtro] = None
    nombre: Optional[str] = Field(None, max_length=120)

    rechazo_previo: Optional[str] = Field(None, pattern=r"^(N|S|X)$")
    sin_registro_previo: Optional[str] = Field(None, pattern=r"^(S|N)$")

    @field_validator("fecha_expedicion", "fecha_operacion", mode="before")
    def parse_date(cls, v: str | date | None) -> date | None:
        if isinstance(v, str):
            return parse_dd_mm_yyyy(v)
        return v

    @model_validator(mode="after")
    def business_validations(self) -> Self:
        # For cancellation, ensure fecha_expedicion not future
        if self.fecha_expedicion > date.today():
            raise ValueError("FechaExpedicion no puede ser futura")
        return self
