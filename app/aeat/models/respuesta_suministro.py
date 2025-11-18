from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.aeat.models.suministro_informacion import (
    CabeceraType,
    DatosPresentacionType,
    IdfacturaExpedidaType,
    OperacionType,
    RegistroDuplicadoType,
)

__NAMESPACE__ = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd"


class EstadoEnvioType(Enum):
    """
    :cvar CORRECTO: Correcto
    :cvar PARCIALMENTE_CORRECTO: Parcialmente correcto. Ver detalle de
        errores
    :cvar INCORRECTO: Incorrecto
    """

    CORRECTO = "Correcto"
    PARCIALMENTE_CORRECTO = "ParcialmenteCorrecto"
    INCORRECTO = "Incorrecto"


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
class RespuestaBaseType:
    """
    :ivar csv: CSV asociado al envío generado por AEAT. Solo se genera
        si no hay rechazo del envio
    :ivar datos_presentacion: Se devuelven datos de la presentacion
        realizada. Solo se genera si no hay rechazo del envio
    :ivar cabecera: Se devuelve la cabecera que se incluyó en el envío.
    :ivar tiempo_espera_envio:
    :ivar estado_envio: Estado del envío en conjunto. Si los datos de
        cabecera y todos los registros son correctos,el estado es
        correcto. En caso de estructura y cabecera correctos donde todos
        los registros son incorrectos, el estado es incorrecto En caso
        de estructura y cabecera correctos con al menos un registro
        incorrecto, el estado global es parcialmente correcto.
    """

    csv: Optional[str] = field(
        default=None,
        metadata={
            "name": "CSV",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd",
        },
    )
    datos_presentacion: Optional[DatosPresentacionType] = field(
        default=None,
        metadata={
            "name": "DatosPresentacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd",
        },
    )
    cabecera: Optional[CabeceraType] = field(
        default=None,
        metadata={
            "name": "Cabecera",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd",
            "required": True,
        },
    )
    tiempo_espera_envio: Optional[str] = field(
        default=None,
        metadata={
            "name": "TiempoEsperaEnvio",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd",
            "required": True,
            "pattern": r"\d{0,4}",
        },
    )
    estado_envio: Optional[EstadoEnvioType] = field(
        default=None,
        metadata={
            "name": "EstadoEnvio",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd",
            "required": True,
        },
    )


@dataclass
class RespuestaExpedidaType:
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
    :ivar registro_duplicado: Solo en el caso de que se rechace el
        registro por duplicado se devuelve este nodo con la informacion
        registrada en el sistema para este registro
    """

    idfactura: Optional[IdfacturaExpedidaType] = field(
        default=None,
        metadata={
            "name": "IDFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd",
            "required": True,
        },
    )
    operacion: Optional[OperacionType] = field(
        default=None,
        metadata={
            "name": "Operacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd",
            "required": True,
        },
    )
    ref_externa: Optional[str] = field(
        default=None,
        metadata={
            "name": "RefExterna",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd",
            "max_length": 60,
        },
    )
    estado_registro: Optional[EstadoRegistroType] = field(
        default=None,
        metadata={
            "name": "EstadoRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd",
            "required": True,
        },
    )
    codigo_error_registro: Optional[int] = field(
        default=None,
        metadata={
            "name": "CodigoErrorRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd",
        },
    )
    descripcion_error_registro: Optional[str] = field(
        default=None,
        metadata={
            "name": "DescripcionErrorRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd",
            "max_length": 1500,
        },
    )
    registro_duplicado: Optional[RegistroDuplicadoType] = field(
        default=None,
        metadata={
            "name": "RegistroDuplicado",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd",
        },
    )


@dataclass
class RespuestaRegFactuSistemaFacturacionType(RespuestaBaseType):
    """
    Respuesta a un envío de registro de facturacion.

    :ivar respuesta_linea: Estado detallado de cada línea del
        suministro.
    """

    respuesta_linea: list[RespuestaExpedidaType] = field(
        default_factory=list,
        metadata={
            "name": "RespuestaLinea",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd",
            "max_occurs": 1000,
        },
    )


@dataclass
class RespuestaRegFactuSistemaFacturacion(RespuestaRegFactuSistemaFacturacionType):
    class Meta:
        namespace = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd"
