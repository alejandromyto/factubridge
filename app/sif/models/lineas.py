"""Line items for invoices (LineaFactura)

The AEAT API limits a maximum of 12 lines per invoice; each line groups items with the
same VAT rate. Fields use string/decimal formats in the API; here we map to Decimal but
accept strings.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class LineaFactura(BaseModel):
    """A single invoice line.

    Fields
    - base_imponible: base taxable amount (required)
    - tipo_impositivo: VAT rate or amount applied (optional)
    - cuota_repercutida: VAT amount (optional)
    - tipo_recargo_equivalencia: recargo equivalencia VAT rate (optional)
    - cuota_recargo_equivalencia: recargo equivalencia amount (optional)
    - operacion_exenta: 'S' when the operation is exempt (then no tipos/cuotas allowed)
    """

    base_imponible: Decimal = Field(
        ..., description=r"Base imponible. Pattern: (+|-)d{1,12}(\.d{0,2})?"
    )
    tipo_impositivo: Optional[Decimal] = Field(
        None, description="Tipo impositivo (si aplica)."
    )
    cuota_repercutida: Optional[Decimal] = Field(
        None, description="Cuota repercutida (si aplica)."
    )
    tipo_recargo_equivalencia: Optional[Decimal] = Field(
        None, description="Tipo recargo equivalencia (si aplica)."
    )
    cuota_recargo_equivalencia: Optional[Decimal] = Field(
        None, description="Cuota recargo equivalencia (si aplica)."
    )
    operacion_exenta: Optional[str] = Field(
        None, description="Mark 'S' when operation is exenta (exempt)."
    )
