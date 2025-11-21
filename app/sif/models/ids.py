"""Identification related models (IdOtro, IdOtroTercero)

Mirrors the `id_otro` and `id_otro_tercero` objects described in the Verifactu OpenAPI.
Includes strict patterns, max lengths and explanatory docstrings for audit purposes.
"""

from typing import Optional

from pydantic import BaseModel, Field


class IdOtro(BaseModel):
    """Identifier object alternative to NIF.

    Fields
    - codigo_pais: ISO3166-1 alpha-2 country code. Required except when id_type == '02'.
    - id_type: one of '02','03','04','05','06','07' describing the identifier type.
    - id: the identifier string (max 20 chars).
    """

    codigo_pais: Optional[str] = Field(
        None,
        description="ISO3166-1 alpha-2 country code. Required unless id_type == '02'.",
    )
    id_type: str = Field(
        ..., pattern=r"^(02|03|04|05|06|07)$", description="Identifier type."
    )
    id: str = Field(..., max_length=20, description="Identifier (max 20 chars).")


class IdOtroTercero(BaseModel):
    """Identifier for a third party (used when invoice is issued by a third)."""

    id_type: str = Field(..., pattern=r"^(02|03|04|05|06)$")
    codigo_pais: Optional[str] = Field(None)
    id: str = Field(...)
