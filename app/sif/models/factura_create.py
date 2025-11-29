"""Factura create model (FacturaInput) with business validations mirroring Verifacti.

The model implements:
- parsing of DD-MM-YYYY date strings
- business rules: destinatario presence/absence per tipo_factura
- F2 amount maximum check
- rectificativa rules (tipo_rectificativa, facturas_rectificadas)
- operation exenta checks per line
- importe_total vs sum of lines check (±10.00€)
- fecha_expedicion must not be future date
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.infrastructure.aeat.models.suministro_informacion import (
    ClaveTipoFacturaType,
    ClaveTipoRectificativaType,
)

from .especiales import Especial
from .ids import IdOtro
from .lineas import LineaFactura
from .validators import (
    importe_matches_total,
    parse_dd_mm_yyyy,
)


class IdFacturaArInput(BaseModel):
    nif_emisor: Optional[str] = Field(
        None,
        min_length=9,
        max_length=9,
        description="NIF del emisor. Si no se envía, se usará el NIF del emisor de la"
        " factura actual.",
    )
    serie: str = Field(..., max_length=20)
    numero: str = Field(..., max_length=20)
    fecha_expedicion: date


class FacturasRectificadasInput(BaseModel):
    """Lista de facturas rectificadas."""

    facturas: List[IdFacturaArInput] = Field(..., min_length=1, max_length=1000)


class FacturasSustituidasInput(BaseModel):
    """Lista de facturas sustituidas."""

    facturas: List[IdFacturaArInput] = Field(..., min_length=1, max_length=1000)


class ImporteRectificativaInput(BaseModel):
    """Validación de entrada para datos de rectificación.

    - base_rectificada: base imponible rectificada
    - cuota_rectificada: cuota repercutida rectificada
    - cuota_recargo_rectificado: cuota recargo equivalencia rectificada (opcional)
    """

    base_rectificada: Decimal = Field(..., max_digits=14, decimal_places=2)
    cuota_rectificada: Decimal = Field(..., max_digits=14, decimal_places=2)
    cuota_recargo_rectificado: Optional[Decimal] = Field(
        None, max_digits=14, decimal_places=2
    )


class FacturaInput(BaseModel):
    """Schema de entrada EXACTO para creación de facturas.

    Docstrings and comments intentionally verbose for auditability. For cross-checking,
    see the original Verifactu OpenAPI spec.
    """

    serie: str = Field(..., max_length=60)
    numero: str = Field(..., max_length=60)
    fecha_expedicion: date
    fecha_operacion: Optional[date] = None

    tipo_factura: ClaveTipoFacturaType = Field(...)
    descripcion: str = Field(..., min_length=1, max_length=500)

    lineas: List[LineaFactura] = Field(..., min_length=1, max_length=12)
    importe_total: Decimal = Field(...)

    nif: Optional[str] = Field(None)
    id_otro: Optional[IdOtro] = None
    nombre: Optional[str] = Field(None, max_length=120)

    validar_destinatario: bool = True
    tipo_rectificativa: Optional[ClaveTipoRectificativaType] = Field(None)
    importe_rectificativa: Optional[ImporteRectificativaInput] = None
    facturas_rectificadas: Optional[List[dict]] = None
    facturas_sustituidas: Optional[List[dict]] = None
    incidencia: Optional[str] = None
    especial: Optional[Especial] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "serie": "A",
                "numero": "234634",
                "fecha_expedicion": "15-11-2024",
                "tipo_factura": "F1",
                "descripcion": "Prestación de servicios",
                "nif": "A15022510",
                "nombre": "Cliente SL",
                "lineas": [
                    {
                        "base_imponible": "200.00",
                        "tipo_impositivo": "21",
                        "cuota_repercutida": "42.00",
                    }
                ],
                "importe_total": "242.00",
            }
        }
    )

    @field_validator("fecha_expedicion", "fecha_operacion", mode="before")
    def parse_date(cls, v: str | date | None) -> date | None:
        if isinstance(v, str):
            return parse_dd_mm_yyyy(v)
        return v

    @model_validator(mode="after")
    def business_validations(self) -> Self:
        """Apply business rules described in OpenAPI.

        Important rules:
        - F2/R5: no destinatario (nif/nombre/id_otro)
        - F2: importe_total must be <= 3010.00 (3.000 + 10 margin)
        - Rectificativas (R*): require tipo_rectificativa and related fields
        - For each line, if operacion_exenta == 'S' then no tipos/cuotas may be provided
        - importe_total must equal sum of lines +/- 10.00 (unless special regimes)
        - fecha_expedicion cannot be future date
        """
        SIN_DESTINATARIO = {
            ClaveTipoFacturaType.F2,
            ClaveTipoFacturaType.R5,
        }
        RECTIFICATIVAS = {
            ClaveTipoFacturaType.R1,
            ClaveTipoFacturaType.R2,
            ClaveTipoFacturaType.R3,
            ClaveTipoFacturaType.R4,
            ClaveTipoFacturaType.R5,
        }
        tipo = self.tipo_factura
        # 1) destinatarios según tipo
        if tipo in SIN_DESTINATARIO and (self.nif or self.nombre or self.id_otro):
            raise ValueError(f"Tipo {tipo.value}, no se permite informar destinatario")

        # 2) F2 importe máximo (3.000 + 10 margen)
        if tipo == ClaveTipoFacturaType.F2:
            importe = Decimal(str(self.importe_total))
            if importe > Decimal("3010"):
                raise ValueError(
                    "Factura simplificada (F2) supera importe permitido (3.000€ + 10€)"
                )

        # 3) Rx: require tipo_rectificativa and facturas_rectificadas when needed
        if tipo in RECTIFICATIVAS:
            if not self.tipo_rectificativa:
                raise ValueError(
                    f"Para {tipo.value} es obligatorio especificar tipo_rectificativa"
                )
            if (
                self.tipo_rectificativa == ClaveTipoRectificativaType.S
                and not self.facturas_rectificadas
            ):
                raise ValueError(
                    "Para rectificativa por sustitución se requieren facturas"
                    " rectificadas"
                )
            if not self.facturas_rectificadas:
                # Although optional in OpenAPI for some R types, keep conservative:
                # require at least empty list for traceability
                raise ValueError("Se requiere información de facturas rectificadas")

        # 4) impuestos/recargo validaciones por linea
        for ln in self.lineas:
            if getattr(ln, "operacion_exenta", None) == "S":  # TODO: REVISAR EXENTA
                if (
                    getattr(ln, "tipo_impositivo", None)
                    or getattr(ln, "cuota_repercutida", None)
                    or getattr(ln, "tipo_recargo_equivalencia", None)
                    or getattr(ln, "cuota_recargo_equivalencia", None)
                ):
                    raise ValueError(
                        "Cuando existe operación exenta no pueden informarse tipos"
                        " impositivo/recargos/cuotas"
                    )

        # 5) importe_total consistency (±10.00€)
        if not importe_matches_total(
            self.importe_total, self.lineas, allowed_margin=Decimal("10.00")
        ):
            raise ValueError(
                "Importe total no coincide con suma de líneas dentro del margen"
                " permitido (±10.00€)"
            )

        # 6) fecha_expedicion not future
        if self.fecha_expedicion > date.today():
            raise ValueError("FechaExpedicion no puede ser futura")

        return self
