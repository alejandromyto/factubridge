from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.aeat.models.suministro_informacion import (
    IdfacturaExpedidaType,
    OperacionType,
)

__NAMESPACE__ = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaValRegistNoVeriFactu.xsd"


class EstadoRegistroType(Enum):
    """
    :cvar CORRECTO: Correcto
    :cvar ACEPTADO_CON_ERRORES: Aceptado con Errores. Ver detalle del
        error
    :cvar INCORRECTO: Incorrecto
    """

    CORRECTO = "Correcto"
    ACEPTADO_CON_ERRORES = "AceptadoConErrores"
    INCORRECTO = "Incorrecto"


@dataclass
class RespuestaRegType:
    """
    Respuesta a un envío.

    :ivar idfactura: ID Factura Expedida
    :ivar operacion:
    :ivar ref_externa:
    :ivar estado_registro: Estado del registro. Correcto o Incorrecto
    :ivar codigo_error_registro: Código del error de registro, en su
        caso.
    :ivar descripcion_error_registro: Descripción detallada del error de
        registro, en su caso.
    """

    idfactura: Optional[IdfacturaExpedidaType] = field(
        default=None,
        metadata={
            "name": "IDFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaValRegistNoVeriFactu.xsd",
            "required": True,
        },
    )
    operacion: Optional[OperacionType] = field(
        default=None,
        metadata={
            "name": "Operacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaValRegistNoVeriFactu.xsd",
            "required": True,
        },
    )
    ref_externa: Optional[str] = field(
        default=None,
        metadata={
            "name": "RefExterna",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaValRegistNoVeriFactu.xsd",
            "max_length": 60,
        },
    )
    estado_registro: Optional[EstadoRegistroType] = field(
        default=None,
        metadata={
            "name": "EstadoRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaValRegistNoVeriFactu.xsd",
            "required": True,
        },
    )
    codigo_error_registro: Optional[int] = field(
        default=None,
        metadata={
            "name": "CodigoErrorRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaValRegistNoVeriFactu.xsd",
        },
    )
    descripcion_error_registro: Optional[str] = field(
        default=None,
        metadata={
            "name": "DescripcionErrorRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaValRegistNoVeriFactu.xsd",
            "max_length": 1500,
        },
    )


@dataclass
class RespuestaValContenidoFactuSistemaFacturacionType:
    """
    :ivar descripcion_error_formato_xml: Error a nivel de formato XML
    :ivar respuesta_validacion: Resultado de la validación si el formato
        del XML es correcto
    """

    descripcion_error_formato_xml: Optional[str] = field(
        default=None,
        metadata={
            "name": "DescripcionErrorFormatoXML",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaValRegistNoVeriFactu.xsd",
            "max_length": 1500,
        },
    )
    respuesta_validacion: Optional[RespuestaRegType] = field(
        default=None,
        metadata={
            "name": "RespuestaValidacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaValRegistNoVeriFactu.xsd",
        },
    )


@dataclass
class RespuestaValContenidoFactuSistemaFacturacion(
    RespuestaValContenidoFactuSistemaFacturacionType
):
    class Meta:
        namespace = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaValRegistNoVeriFactu.xsd"
