from dataclasses import dataclass, field
from typing import Optional

from schemas.suministro_informacion import (
    CabeceraConsultaSf,
    ContraparteConsultaType,
    FechaExpedicionConsultaType,
    IdfacturaExpedidaBctype,
    MostrarNombreRazonEmisorType,
    MostrarSistemaInformaticoType,
    PeriodoImputacionType,
    SistemaInformaticoConsultaType,
)

__NAMESPACE__ = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd"


@dataclass
class DatosAdicionalesRespuestaType:
    """
    :ivar mostrar_nombre_razon_emisor: Indicador que especifica si se
        quiere obtener en la respuesta el campo NombreRazonEmisor en la
        información del registro se facturacion. Si el Valor es S
        aumenta el tiempo de respuesta en la cosulta por detinatario
    :ivar mostrar_sistema_informatico: Indicador que especifica si se
        quiere obtener en la respuesta el bloque SistemaInformatico en
        la información del registro se facturacion. Si el Valor es S
        aumenta el tiempo de respuesta en la cosulta. Si se consulta por
        Destinatario el valor del campo MostrarSistemaInformatico debe
        ser 'N' o no estar cumplimentado
    """

    mostrar_nombre_razon_emisor: Optional[MostrarNombreRazonEmisorType] = field(
        default=None,
        metadata={
            "name": "MostrarNombreRazonEmisor",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd",
        },
    )
    mostrar_sistema_informatico: Optional[MostrarSistemaInformaticoType] = field(
        default=None,
        metadata={
            "name": "MostrarSistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd",
        },
    )


@dataclass
class LrfiltroRegFacturacionType:
    """
    :ivar periodo_imputacion:
    :ivar num_serie_factura: Nº Serie+Nº Factura de la Factura del
        Emisor.
    :ivar contraparte: Contraparte del NIF de la cabecera que realiza la
        consulta. Obligado si la cosulta la realiza el Destinatario de
        los registros de facturacion. Destinatario si la cosulta la
        realiza el Obligado dde los registros de facturacion.
    :ivar fecha_expedicion_factura:
    :ivar sistema_informatico:
    :ivar ref_externa:
    :ivar clave_paginacion:
    """

    class Meta:
        name = "LRFiltroRegFacturacionType"

    periodo_imputacion: Optional[PeriodoImputacionType] = field(
        default=None,
        metadata={
            "name": "PeriodoImputacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd",
            "required": True,
        },
    )
    num_serie_factura: Optional[str] = field(
        default=None,
        metadata={
            "name": "NumSerieFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd",
            "min_length": 1,
            "max_length": 60,
        },
    )
    contraparte: Optional[ContraparteConsultaType] = field(
        default=None,
        metadata={
            "name": "Contraparte",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd",
        },
    )
    fecha_expedicion_factura: Optional[FechaExpedicionConsultaType] = field(
        default=None,
        metadata={
            "name": "FechaExpedicionFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd",
        },
    )
    sistema_informatico: Optional[SistemaInformaticoConsultaType] = field(
        default=None,
        metadata={
            "name": "SistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd",
        },
    )
    ref_externa: Optional[str] = field(
        default=None,
        metadata={
            "name": "RefExterna",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd",
            "max_length": 60,
        },
    )
    clave_paginacion: Optional[IdfacturaExpedidaBctype] = field(
        default=None,
        metadata={
            "name": "ClavePaginacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd",
        },
    )


@dataclass
class ConsultaFactuSistemaFacturacionType:
    cabecera: Optional[CabeceraConsultaSf] = field(
        default=None,
        metadata={
            "name": "Cabecera",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd",
            "required": True,
        },
    )
    filtro_consulta: Optional[LrfiltroRegFacturacionType] = field(
        default=None,
        metadata={
            "name": "FiltroConsulta",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd",
            "required": True,
        },
    )
    datos_adicionales_respuesta: Optional[DatosAdicionalesRespuestaType] = field(
        default=None,
        metadata={
            "name": "DatosAdicionalesRespuesta",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd",
        },
    )


@dataclass
class ConsultaFactuSistemaFacturacion(ConsultaFactuSistemaFacturacionType):
    """
    Servicio de consulta Registros Facturacion.
    """

    class Meta:
        namespace = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd"
