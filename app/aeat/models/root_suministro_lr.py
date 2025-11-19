from dataclasses import dataclass, field
from typing import List, Optional

from .suministro_lr import CabeceraType, RegistroFacturaType

__NAMESPACE__ = (
    "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/"
    "aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd"
)


@dataclass
class RegFactuSistemaFacturacionRoot:
    """
    Root element para envío LR (creado manualmente).

    Este wrapper es necesario porque el XSD define el elemento root como
    un element anónimo, no como un tipo global. xsdata NO lo genera
    automáticamente.
    """

    cabecera: Optional[CabeceraType] = field(
        default=None,
        metadata={
            "name": "Cabecera",
            "type": "Element",
            "required": True,
        },
    )

    registro_factura: List[RegistroFacturaType] = field(
        default_factory=list,
        metadata={
            "name": "RegistroFactura",
            "type": "Element",
            "min_occurs": 1,
            "max_occurs": 1000,
        },
    )

    class Meta:
        name = "RegFactuSistemaFacturacion"
        namespace = __NAMESPACE__
