from dataclasses import dataclass, field
from typing import Optional

from app.infrastructure.aeat.models.suministro_informacion import (
    CabeceraType,
    RegistroAlta,
    RegistroAnulacion,
)

__NAMESPACE__ = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd"


@dataclass
class RegistroFacturaType:
    """
    Datos correspondientes a los registros de facturacion.
    """

    registro_alta: Optional[RegistroAlta] = field(
        default=None,
        metadata={
            "name": "RegistroAlta",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    registro_anulacion: Optional[RegistroAnulacion] = field(
        default=None,
        metadata={
            "name": "RegistroAnulacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )


@dataclass
class RegFactuSistemaFacturacion:
    class Meta:
        namespace = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd"

    cabecera: Optional[CabeceraType] = field(
        default=None,
        metadata={
            "name": "Cabecera",
            "type": "Element",
            "required": True,
        },
    )
    registro_factura: list[RegistroFacturaType] = field(
        default_factory=list,
        metadata={
            "name": "RegistroFactura",
            "type": "Element",
            "min_occurs": 1,
            "max_occurs": 1000,
        },
    )
