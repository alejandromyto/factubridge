"""Identification related models (IdOtro, IdOtroTercero)

Mirrors the `id_otro` and `id_otro_tercero` objects described in the Verifactu OpenAPI.
Includes strict patterns, max lengths and explanatory docstrings for audit purposes.
"""

from typing import Optional

from pydantic import BaseModel, Field

from app.aeat.models.suministro_informacion import (
    CountryType2,
    PersonaFisicaJuridicaIdtypeType,
)


class IdOtro(BaseModel):
    """Identifier object alternative to NIF.

    Fields
    - codigo_pais: ISO3166-1 alpha-2 country code. Required except when id_type == '02'.
    - id_type:
        - VALUE_02: NIF-IVA
        - VALUE_03: Pasaporte
        - VALUE_04: IDEnPaisResidencia
        - VALUE_05: Certificado Residencia
        - VALUE_06: Otro documento Probatorio
        - VALUE_07: No Censado
    - id: the identifier string (max 20 chars).
    """

    codigo_pais: Optional[CountryType2] = Field(
        None,
        description="ISO3166-1 alpha-2 country code. Required unless id_type == '02'.",
    )
    id_type: Optional[PersonaFisicaJuridicaIdtypeType] = Field(
        None,
        description="Identifier type.",
    )
    id: str = Field(..., max_length=20, description="Identifier (max 20 chars).")


class IdOtroTercero(BaseModel):
    """Identifier for a third party (used when invoice is issued by a third)."""

    id_type: str = Field(..., pattern=r"^(02|03|04|05|06)$")
    codigo_pais: Optional[str] = Field(None)
    id: str = Field(...)
