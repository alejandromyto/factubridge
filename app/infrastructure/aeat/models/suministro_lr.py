from __future__ import annotations

from dataclasses import dataclass, field

from app.infrastructure.aeat.models.suministro_informacion import (
    CabeceraType,
    RegistroAlta,
    RegistroAnulacion,
)

__NAMESPACE__ = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd"


@dataclass(kw_only=True)
class RegistroFacturaType:
    """
    Datos correspondientes a los registros de facturacion.
    """

    registro_alta: None | RegistroAlta = field(
        default=None,
        metadata={
            "name": "RegistroAlta",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    registro_anulacion: None | RegistroAnulacion = field(
        default=None,
        metadata={
            "name": "RegistroAnulacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )


@dataclass(kw_only=True)
class RegFactuSistemaFacturacion:
    class Meta:
        namespace = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd"

    cabecera: CabeceraType = field(
        metadata={
            "name": "Cabecera",
            "type": "Element",
            "required": True,
        }
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
