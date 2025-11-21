"""sif json models package

Modular Pydantic v2 models and validators for sif json (create/modify/cancel).
This package is designed to be auditable: each module contains exhaustive docstrings
and inline comments that map to the OpenAPI specification supplied by Verifacti.
"""

from .factura_cancel import FacturaCancelInput
from .factura_create import FacturaInput
from .factura_modify import FacturaModifyInput

__all__ = [
    "FacturaInput",
    "FacturaModifyInput",
    "FacturaCancelInput",
]
