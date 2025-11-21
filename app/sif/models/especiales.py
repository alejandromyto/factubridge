"""Special fields container used in facture 'especial' object.

Contains flags and fields that are conditional depending on tipo_factura (e.g. cupon,
factura_simplificada_art_7273).
"""

from typing import Optional

from pydantic import BaseModel, Field

from .ids import IdOtroTercero


class Especial(BaseModel):
    """Holds optional special indicators and third-party issuer information.

    Many fields are permitted only for specific invoice types (see OpenAPI). All
    constraints should be enforced at business validation stage where context
    (tipo_factura) is available.
    """

    cupon: Optional[str] = Field(
        None, pattern="^S$", description="Only 'S' allowed when present."
    )
    factura_simplificada_art_7273: Optional[str] = Field(None, pattern="^S$")
    factura_sin_identif_destinatario_art_61d: Optional[str] = Field(None, pattern="^S$")
    emitida_por_tercero_o_destinatario: Optional[str] = Field(None, pattern="^(T|D)$")
    nombre_tercero: Optional[str] = Field(None, max_length=120)
    nif_tercero: Optional[str] = Field(None)
    id_otro_tercero: Optional[IdOtroTercero] = Field(None)
