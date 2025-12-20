from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from xsdata.models.datatype import XmlDateTime

from app.infrastructure.aeat.models.suministro_informacion import (
    CabeceraConsultaSf,
    ClaveTipoFacturaType,
    ClaveTipoRectificativaType,
    CompletaSinDestinatarioType,
    CuponType,
    DatosPresentacion2Type,
    DesgloseRectificacionType,
    DesgloseType,
    EncadenamientoFacturaAnteriorType,
    GeneradoPorType,
    IdfacturaArtype,
    IdfacturaExpedidaBctype,
    IdfacturaExpedidaType,
    IncidenciaType,
    MacrodatoType,
    PersonaFisicaJuridicaType,
    PrimerRegistroCadenaType,
    RechazoPrevioType,
    SimplificadaCualificadaType,
    SinRegistroPrevioType,
    SistemaInformaticoType,
    SubsanacionType,
    TercerosOdestinatarioType,
    TipoHuellaType,
    TipoPeriodoType,
)

__NAMESPACE__ = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd"


class EstadoRegistroType(str, Enum):
    """
    :cvar CORRECTO: El registro se almacenado sin errores
    :cvar ACEPTADO_CON_ERRORES: El registro se almacenado tiene algunos
        errores. Ver detalle del error
    :cvar ANULADO: El registro almacenado ha sido anulado
    """

    CORRECTO = "Correcto"
    ACEPTADO_CON_ERRORES = "AceptadoConErrores"
    ANULADO = "Anulado"


class IndicadorPaginacionType(str, Enum):
    S = "S"
    N = "N"


class ResultadoConsultaType(str, Enum):
    CON_DATOS = "ConDatos"
    SIN_DATOS = "SinDatos"


@dataclass(kw_only=True)
class EstadoRegFactuType:
    """
    :ivar timestamp_ultima_modificacion:
    :ivar estado_registro: Estado del registro almacenado en el sistema.
        Los estados posibles son: Correcta, AceptadaConErrores y Anulada
    :ivar codigo_error_registro: Código del error de registro, en su
        caso.
    :ivar descripcion_error_registro: Descripción detallada del error de
        registro, en su caso.
    """

    timestamp_ultima_modificacion: XmlDateTime = field(
        metadata={
            "name": "TimestampUltimaModificacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "required": True,
        }
    )
    estado_registro: EstadoRegistroType = field(
        metadata={
            "name": "EstadoRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "required": True,
        }
    )
    codigo_error_registro: None | int = field(
        default=None,
        metadata={
            "name": "CodigoErrorRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    descripcion_error_registro: None | str = field(
        default=None,
        metadata={
            "name": "DescripcionErrorRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "max_length": 500,
        },
    )


@dataclass(kw_only=True)
class RespuestaConsultaType:
    cabecera: CabeceraConsultaSf = field(
        metadata={
            "name": "Cabecera",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "required": True,
        }
    )
    periodo_imputacion: RespuestaConsultaType.PeriodoImputacion = field(
        metadata={
            "name": "PeriodoImputacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "required": True,
        }
    )
    indicador_paginacion: IndicadorPaginacionType = field(
        metadata={
            "name": "IndicadorPaginacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "required": True,
        }
    )
    resultado_consulta: ResultadoConsultaType = field(
        metadata={
            "name": "ResultadoConsulta",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class PeriodoImputacion:
        """
        Período al que corresponden los apuntes. todos los apuntes deben
        corresponder al mismo período impositivo.
        """

        ejercicio: str = field(
            metadata={
                "name": "Ejercicio",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
                "required": True,
                "length": 4,
                "pattern": r"\d{4,4}",
            }
        )
        periodo: TipoPeriodoType = field(
            metadata={
                "name": "Periodo",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
                "required": True,
            }
        )


@dataclass(kw_only=True)
class RespuestaDatosRegistroFacturacionType:
    """
    Apunte correspondiente al libro de facturas expedidas.

    :ivar nombre_razon_emisor: Solo se informa el campo
        NombreRazonEmisor si se realiza la consulta con valor S en el
        campo MostrarNombreRazonEmisor
    :ivar ref_externa:
    :ivar subsanacion:
    :ivar rechazo_previo:
    :ivar sin_registro_previo:
    :ivar generado_por:
    :ivar generador:
    :ivar tipo_factura: Clave del tipo de factura
    :ivar tipo_rectificativa: Identifica si el tipo de factura
        rectificativa es por sustitución o por diferencia
    :ivar facturas_rectificadas:
    :ivar facturas_sustituidas:
    :ivar importe_rectificacion:
    :ivar fecha_operacion:
    :ivar descripcion_operacion:
    :ivar factura_simplificada_art7273:
    :ivar factura_sin_identif_destinatario_art61d:
    :ivar macrodato:
    :ivar emitida_por_tercero_odestinatario:
    :ivar tercero: Tercero que expida la factura y/o genera el registro
        de alta.
    :ivar destinatarios:
    :ivar cupon:
    :ivar desglose:
    :ivar cuota_total:
    :ivar importe_total:
    :ivar encadenamiento:
    :ivar sistema_informatico:
    :ivar fecha_hora_huso_gen_registro:
    :ivar num_registro_acuerdo_facturacion:
    :ivar id_acuerdo_sistema_informatico:
    :ivar tipo_huella:
    :ivar huella:
    :ivar nif_representante:
    :ivar fecha_fin_veri_factu:
    :ivar incidencia:
    """

    nombre_razon_emisor: None | str = field(
        default=None,
        metadata={
            "name": "NombreRazonEmisor",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "max_length": 120,
        },
    )
    ref_externa: None | str = field(
        default=None,
        metadata={
            "name": "RefExterna",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "max_length": 60,
        },
    )
    subsanacion: None | SubsanacionType = field(
        default=None,
        metadata={
            "name": "Subsanacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    rechazo_previo: None | RechazoPrevioType = field(
        default=None,
        metadata={
            "name": "RechazoPrevio",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    sin_registro_previo: None | SinRegistroPrevioType = field(
        default=None,
        metadata={
            "name": "SinRegistroPrevio",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    generado_por: None | GeneradoPorType = field(
        default=None,
        metadata={
            "name": "GeneradoPor",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    generador: None | PersonaFisicaJuridicaType = field(
        default=None,
        metadata={
            "name": "Generador",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    tipo_factura: None | ClaveTipoFacturaType = field(
        default=None,
        metadata={
            "name": "TipoFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    tipo_rectificativa: None | ClaveTipoRectificativaType = field(
        default=None,
        metadata={
            "name": "TipoRectificativa",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    facturas_rectificadas: (
        None | RespuestaDatosRegistroFacturacionType.FacturasRectificadas
    ) = field(
        default=None,
        metadata={
            "name": "FacturasRectificadas",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    facturas_sustituidas: (
        None | RespuestaDatosRegistroFacturacionType.FacturasSustituidas
    ) = field(
        default=None,
        metadata={
            "name": "FacturasSustituidas",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    importe_rectificacion: None | DesgloseRectificacionType = field(
        default=None,
        metadata={
            "name": "ImporteRectificacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    fecha_operacion: None | str = field(
        default=None,
        metadata={
            "name": "FechaOperacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "length": 10,
            "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
        },
    )
    descripcion_operacion: None | str = field(
        default=None,
        metadata={
            "name": "DescripcionOperacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "max_length": 500,
        },
    )
    factura_simplificada_art7273: None | SimplificadaCualificadaType = field(
        default=None,
        metadata={
            "name": "FacturaSimplificadaArt7273",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    factura_sin_identif_destinatario_art61d: None | CompletaSinDestinatarioType = field(
        default=None,
        metadata={
            "name": "FacturaSinIdentifDestinatarioArt61d",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    macrodato: None | MacrodatoType = field(
        default=None,
        metadata={
            "name": "Macrodato",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    emitida_por_tercero_odestinatario: None | TercerosOdestinatarioType = field(
        default=None,
        metadata={
            "name": "EmitidaPorTerceroODestinatario",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    tercero: None | PersonaFisicaJuridicaType = field(
        default=None,
        metadata={
            "name": "Tercero",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    destinatarios: None | RespuestaDatosRegistroFacturacionType.Destinatarios = field(
        default=None,
        metadata={
            "name": "Destinatarios",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    cupon: None | CuponType = field(
        default=None,
        metadata={
            "name": "Cupon",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    desglose: None | DesgloseType = field(
        default=None,
        metadata={
            "name": "Desglose",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    cuota_total: None | str = field(
        default=None,
        metadata={
            "name": "CuotaTotal",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        },
    )
    importe_total: None | str = field(
        default=None,
        metadata={
            "name": "ImporteTotal",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        },
    )
    encadenamiento: None | RespuestaDatosRegistroFacturacionType.Encadenamiento = field(
        default=None,
        metadata={
            "name": "Encadenamiento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    sistema_informatico: None | SistemaInformaticoType = field(
        default=None,
        metadata={
            "name": "SistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    fecha_hora_huso_gen_registro: None | XmlDateTime = field(
        default=None,
        metadata={
            "name": "FechaHoraHusoGenRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    num_registro_acuerdo_facturacion: None | str = field(
        default=None,
        metadata={
            "name": "NumRegistroAcuerdoFacturacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "max_length": 15,
        },
    )
    id_acuerdo_sistema_informatico: None | str = field(
        default=None,
        metadata={
            "name": "IdAcuerdoSistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "max_length": 16,
        },
    )
    tipo_huella: None | TipoHuellaType = field(
        default=None,
        metadata={
            "name": "TipoHuella",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    huella: None | str = field(
        default=None,
        metadata={
            "name": "Huella",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "max_length": 64,
        },
    )
    nif_representante: None | str = field(
        default=None,
        metadata={
            "name": "NifRepresentante",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "length": 9,
        },
    )
    fecha_fin_veri_factu: None | str = field(
        default=None,
        metadata={
            "name": "FechaFinVeriFactu",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "length": 10,
            "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
        },
    )
    incidencia: None | IncidenciaType = field(
        default=None,
        metadata={
            "name": "Incidencia",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )

    @dataclass(kw_only=True)
    class FacturasRectificadas:
        """
        El ID de las facturas rectificadas, únicamente se rellena en el
        caso de rectificación de facturas.
        """

        idfactura_rectificada: list[IdfacturaArtype] = field(
            default_factory=list,
            metadata={
                "name": "IDFacturaRectificada",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
                "min_occurs": 1,
                "max_occurs": 1000,
            },
        )

    @dataclass(kw_only=True)
    class FacturasSustituidas:
        """
        El ID de las facturas sustituidas, únicamente se rellena en el caso
        de facturas sustituidas.
        """

        idfactura_sustituida: list[IdfacturaArtype] = field(
            default_factory=list,
            metadata={
                "name": "IDFacturaSustituida",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
                "min_occurs": 1,
                "max_occurs": 1000,
            },
        )

    @dataclass(kw_only=True)
    class Destinatarios:
        """
        Contraparte de la operación.

        Cliente.
        """

        iddestinatario: list[PersonaFisicaJuridicaType] = field(
            default_factory=list,
            metadata={
                "name": "IDDestinatario",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
                "min_occurs": 1,
                "max_occurs": 1000,
            },
        )

    @dataclass(kw_only=True)
    class Encadenamiento:
        primer_registro: None | PrimerRegistroCadenaType = field(
            default=None,
            metadata={
                "name": "PrimerRegistro",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            },
        )
        registro_anterior: None | EncadenamientoFacturaAnteriorType = field(
            default=None,
            metadata={
                "name": "RegistroAnterior",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            },
        )


@dataclass(kw_only=True)
class RegistroRespuestaConsultaRegFacturacionType:
    idfactura: IdfacturaExpedidaType = field(
        metadata={
            "name": "IDFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "required": True,
        }
    )
    datos_registro_facturacion: RespuestaDatosRegistroFacturacionType = field(
        metadata={
            "name": "DatosRegistroFacturacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "required": True,
        }
    )
    datos_presentacion: None | DatosPresentacion2Type = field(
        default=None,
        metadata={
            "name": "DatosPresentacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )
    estado_registro: EstadoRegFactuType = field(
        metadata={
            "name": "EstadoRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class RespuestaConsultaFactuSistemaFacturacionType(RespuestaConsultaType):
    registro_respuesta_consulta_factu_sistema_facturacion: list[
        RegistroRespuestaConsultaRegFacturacionType
    ] = field(
        default_factory=list,
        metadata={
            "name": "RegistroRespuestaConsultaFactuSistemaFacturacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
            "max_occurs": 10000,
        },
    )
    clave_paginacion: None | IdfacturaExpedidaBctype = field(
        default=None,
        metadata={
            "name": "ClavePaginacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd",
        },
    )


@dataclass(kw_only=True)
class RespuestaConsultaFactuSistemaFacturacion(
    RespuestaConsultaFactuSistemaFacturacionType
):
    """
    Servicio de consulta de regIstros de facturacion.
    """

    class Meta:
        namespace = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd"
