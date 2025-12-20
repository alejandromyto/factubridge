from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from xsdata.models.datatype import XmlDateTime

from app.infrastructure.aeat.models.xmldsig_core_schema import Signature

__NAMESPACE__ = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd"


class CountryType2(str, Enum):
    AF = "AF"
    AL = "AL"
    DE = "DE"
    AD = "AD"
    AO = "AO"
    AI = "AI"
    AQ = "AQ"
    AG = "AG"
    SA = "SA"
    DZ = "DZ"
    AR = "AR"
    AM = "AM"
    AW = "AW"
    AU = "AU"
    AT = "AT"
    AZ = "AZ"
    BS = "BS"
    BH = "BH"
    BD = "BD"
    BB = "BB"
    BE = "BE"
    BZ = "BZ"
    BJ = "BJ"
    BM = "BM"
    BY = "BY"
    BO = "BO"
    BA = "BA"
    BW = "BW"
    BV = "BV"
    BR = "BR"
    BN = "BN"
    BG = "BG"
    BF = "BF"
    BI = "BI"
    BT = "BT"
    CV = "CV"
    KY = "KY"
    KH = "KH"
    CM = "CM"
    CA = "CA"
    CF = "CF"
    CC = "CC"
    CO = "CO"
    KM = "KM"
    CG = "CG"
    CD = "CD"
    CK = "CK"
    KP = "KP"
    KR = "KR"
    CI = "CI"
    CR = "CR"
    HR = "HR"
    CU = "CU"
    TD = "TD"
    CZ = "CZ"
    CL = "CL"
    CN = "CN"
    CY = "CY"
    CW = "CW"
    DK = "DK"
    DM = "DM"
    DO = "DO"
    EC = "EC"
    EG = "EG"
    AE = "AE"
    ER = "ER"
    SK = "SK"
    SI = "SI"
    ES = "ES"
    US = "US"
    EE = "EE"
    ET = "ET"
    FO = "FO"
    PH = "PH"
    FI = "FI"
    FJ = "FJ"
    FR = "FR"
    GA = "GA"
    GM = "GM"
    GE = "GE"
    GS = "GS"
    GH = "GH"
    GI = "GI"
    GD = "GD"
    GR = "GR"
    GL = "GL"
    GU = "GU"
    GT = "GT"
    GG = "GG"
    GN = "GN"
    GQ = "GQ"
    GW = "GW"
    GY = "GY"
    HT = "HT"
    HM = "HM"
    HN = "HN"
    HK = "HK"
    HU = "HU"
    IN = "IN"
    ID = "ID"
    IR = "IR"
    IQ = "IQ"
    IE = "IE"
    IM = "IM"
    IS = "IS"
    IL = "IL"
    IT = "IT"
    JM = "JM"
    JP = "JP"
    JE = "JE"
    JO = "JO"
    KZ = "KZ"
    KE = "KE"
    KG = "KG"
    KI = "KI"
    KW = "KW"
    LA = "LA"
    LS = "LS"
    LV = "LV"
    LB = "LB"
    LR = "LR"
    LY = "LY"
    LI = "LI"
    LT = "LT"
    LU = "LU"
    XG = "XG"
    MO = "MO"
    MK = "MK"
    MG = "MG"
    MY = "MY"
    MW = "MW"
    MV = "MV"
    ML = "ML"
    MT = "MT"
    FK = "FK"
    MP = "MP"
    MA = "MA"
    MH = "MH"
    MU = "MU"
    MR = "MR"
    YT = "YT"
    UM = "UM"
    MX = "MX"
    FM = "FM"
    MD = "MD"
    MC = "MC"
    MN = "MN"
    ME = "ME"
    MS = "MS"
    MZ = "MZ"
    MM = "MM"
    NA = "NA"
    NR = "NR"
    CX = "CX"
    NP = "NP"
    NI = "NI"
    NE = "NE"
    NG = "NG"
    NU = "NU"
    NF = "NF"
    NO = "NO"
    NC = "NC"
    NZ = "NZ"
    IO = "IO"
    OM = "OM"
    NL = "NL"
    BQ = "BQ"
    PK = "PK"
    PW = "PW"
    PA = "PA"
    PG = "PG"
    PY = "PY"
    PE = "PE"
    PN = "PN"
    PF = "PF"
    PL = "PL"
    PT = "PT"
    PR = "PR"
    QA = "QA"
    GB = "GB"
    RW = "RW"
    RO = "RO"
    RU = "RU"
    SB = "SB"
    SV = "SV"
    WS = "WS"
    AS = "AS"
    KN = "KN"
    SM = "SM"
    SX = "SX"
    PM = "PM"
    VC = "VC"
    SH = "SH"
    LC = "LC"
    ST = "ST"
    SN = "SN"
    RS = "RS"
    SC = "SC"
    SL = "SL"
    SG = "SG"
    SY = "SY"
    SO = "SO"
    LK = "LK"
    SZ = "SZ"
    ZA = "ZA"
    SD = "SD"
    SS = "SS"
    SE = "SE"
    CH = "CH"
    SR = "SR"
    TH = "TH"
    TW = "TW"
    TZ = "TZ"
    TJ = "TJ"
    PS = "PS"
    TF = "TF"
    TL = "TL"
    TG = "TG"
    TK = "TK"
    TO = "TO"
    TT = "TT"
    TN = "TN"
    TC = "TC"
    TM = "TM"
    TR = "TR"
    TV = "TV"
    UA = "UA"
    UG = "UG"
    UY = "UY"
    UZ = "UZ"
    VU = "VU"
    VA = "VA"
    VE = "VE"
    VN = "VN"
    VG = "VG"
    VI = "VI"
    WF = "WF"
    YE = "YE"
    DJ = "DJ"
    ZM = "ZM"
    ZW = "ZW"
    QU = "QU"
    XB = "XB"
    XU = "XU"
    XN = "XN"


@dataclass(kw_only=True)
class IdfacturaExpedidaHuellaType:
    """
    Datos de encadenamiento.
    """

    class Meta:
        name = "IDFacturaExpedidaHuellaType"

    idemisor_factura: str = field(
        metadata={
            "name": "IDEmisorFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "length": 9,
        }
    )
    num_serie_factura: str = field(
        metadata={
            "name": "NumSerieFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 60,
        }
    )
    fecha_expedicion_factura: str = field(
        metadata={
            "name": "FechaExpedicionFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "length": 10,
            "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
        }
    )
    huella: str = field(
        metadata={
            "name": "Huella",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 64,
        }
    )


@dataclass(kw_only=True)
class IdfacturaExpedidaType:
    """
    Datos de identificación de factura expedida para operaciones de
    consulta.
    """

    class Meta:
        name = "IDFacturaExpedidaType"

    idemisor_factura: str = field(
        metadata={
            "name": "IDEmisorFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "length": 9,
        }
    )
    num_serie_factura: str = field(
        metadata={
            "name": "NumSerieFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 60,
        }
    )
    fecha_expedicion_factura: str = field(
        metadata={
            "name": "FechaExpedicionFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "length": 10,
            "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
        }
    )


@dataclass(kw_only=True)
class PersonaFisicaJuridicaEstype:
    """
    Datos de una persona física o jurídica Española con un NIF asociado.
    """

    class Meta:
        name = "PersonaFisicaJuridicaESType"

    nombre_razon: str = field(
        metadata={
            "name": "NombreRazon",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 120,
        }
    )
    nif: str = field(
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "length": 9,
        }
    )


class PersonaFisicaJuridicaIdtypeType(str, Enum):
    """
    :cvar VALUE_02: NIF-IVA
    :cvar VALUE_03: Pasaporte
    :cvar VALUE_04: IDEnPaisResidencia
    :cvar VALUE_05: Certificado Residencia
    :cvar VALUE_06: Otro documento Probatorio
    :cvar VALUE_07: No Censado
    """

    VALUE_02 = "02"
    VALUE_03 = "03"
    VALUE_04 = "04"
    VALUE_05 = "05"
    VALUE_06 = "06"
    VALUE_07 = "07"


class SiNoType(str, Enum):
    S = "S"
    N = "N"


class TercerosOdestinatarioType(str, Enum):
    """
    :cvar D: Destinatario
    :cvar T: Tercero
    """

    D = "D"
    T = "T"


class TipoAnomaliaType(str, Enum):
    """
    :cvar VALUE_01: Integridad-huella
    :cvar VALUE_02: Integridad-firma
    :cvar VALUE_03: Integridad - Otros
    :cvar VALUE_04: Trazabilidad-cadena-registro - Reg. no primero pero
        con reg. anterior no anotado o inexistente
    :cvar VALUE_05: Trazabilidad-cadena-registro - Reg. no último pero
        con reg. posterior no anotado o inexistente
    :cvar VALUE_06: Trazabilidad-cadena-registro - Otros
    :cvar VALUE_07: Trazabilidad-cadena-huella - Huella del reg. no se
        corresponde con la 'huella del reg. anterior' almacenada en el
        registro posterior
    :cvar VALUE_08: Trazabilidad-cadena-huella - Campo 'huella del reg.
        anterior' no se corresponde con la huella del reg. anterior
    :cvar VALUE_09: Trazabilidad-cadena-huella - Otros
    :cvar VALUE_10: Trazabilidad-cadena - Otros
    :cvar VALUE_11: Trazabilidad-fechas - Fecha-hora anterior a la fecha
        del reg. anterior
    :cvar VALUE_12: Trazabilidad-fechas - Fecha-hora posterior a la
        fecha del reg. posterior
    :cvar VALUE_13: Trazabilidad-fechas - Reg. con fecha-hora de
        generación posterior a la fecha-hora actual del sistema
    :cvar VALUE_14: Trazabilidad-fechas - Otros
    :cvar VALUE_15: Trazabilidad - Otros
    :cvar VALUE_90: Otros
    """

    VALUE_01 = "01"
    VALUE_02 = "02"
    VALUE_03 = "03"
    VALUE_04 = "04"
    VALUE_05 = "05"
    VALUE_06 = "06"
    VALUE_07 = "07"
    VALUE_08 = "08"
    VALUE_09 = "09"
    VALUE_10 = "10"
    VALUE_11 = "11"
    VALUE_12 = "12"
    VALUE_13 = "13"
    VALUE_14 = "14"
    VALUE_15 = "15"
    VALUE_90 = "90"


class TipoEventoType(str, Enum):
    """
    :cvar VALUE_01: Inicio del funcionamiento del sistema informático
        como «NO VERI*FACTU».
    :cvar VALUE_02: Fin del funcionamiento del sistema informático como
        «NO VERI*FACTU».
    :cvar VALUE_03: Lanzamiento del proceso de detección de anomalías en
        los registros de facturación.
    :cvar VALUE_04: Detección de anomalías en la integridad,
        inalterabilidad y trazabilidad de registros de facturación.
    :cvar VALUE_05: Lanzamiento del proceso de detección de anomalías en
        los registros de evento.
    :cvar VALUE_06: Detección de anomalías en la integridad,
        inalterabilidad y trazabilidad de registros de evento.
    :cvar VALUE_07: Restauración de copia de seguridad, cuando ésta se
        gestione desde el propio sistema informático de facturación.
    :cvar VALUE_08: Exportación de registros de facturación generados en
        un periodo.
    :cvar VALUE_09: Exportación de registros de evento generados en un
        periodo.
    :cvar VALUE_10: Registro resumen de eventos
    :cvar VALUE_90: Otros tipos de eventos a registrar voluntariamente
        por la persona o entidad productora del sistema informático.
    """

    VALUE_01 = "01"
    VALUE_02 = "02"
    VALUE_03 = "03"
    VALUE_04 = "04"
    VALUE_05 = "05"
    VALUE_06 = "06"
    VALUE_07 = "07"
    VALUE_08 = "08"
    VALUE_09 = "09"
    VALUE_10 = "10"
    VALUE_90 = "90"


class TipoHuellaType(str, Enum):
    """
    :cvar VALUE_01: SHA-256
    """

    VALUE_01 = "01"


class VersionType(str, Enum):
    VALUE_1_0 = "1.0"


@dataclass(kw_only=True)
class DeteccionAnomaliasRegFacturacionType:
    tipo_anomalia: TipoAnomaliaType = field(
        metadata={
            "name": "TipoAnomalia",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    otros_datos_anomalia: None | str = field(
        default=None,
        metadata={
            "name": "OtrosDatosAnomalia",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "max_length": 100,
        },
    )
    registro_facturacion_anomalo: None | IdfacturaExpedidaType = field(
        default=None,
        metadata={
            "name": "RegistroFacturacionAnomalo",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )


@dataclass(kw_only=True)
class ExportacionRegFacturacionPeriodoType:
    """
    :ivar fecha_hora_huso_inicio_periodo_export: Formato: YYYY-MM-
        DDThh:mm:ssTZD (ej: 2024-01-01T19:20:30+01:00) (ISO 8601)
    :ivar fecha_hora_huso_fin_periodo_export: Formato: YYYY-MM-
        DDThh:mm:ssTZD (ej: 2024-01-01T19:20:30+01:00) (ISO 8601)
    :ivar registro_facturacion_inicial_periodo:
    :ivar registro_facturacion_final_periodo:
    :ivar numero_de_registros_facturacion_alta_exportados:
    :ivar suma_cuota_total_alta:
    :ivar suma_importe_total_alta:
    :ivar numero_de_registros_facturacion_anulacion_exportados:
    :ivar registros_facturacion_exportados_dejan_de_conservarse:
    """

    fecha_hora_huso_inicio_periodo_export: XmlDateTime = field(
        metadata={
            "name": "FechaHoraHusoInicioPeriodoExport",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    fecha_hora_huso_fin_periodo_export: XmlDateTime = field(
        metadata={
            "name": "FechaHoraHusoFinPeriodoExport",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    registro_facturacion_inicial_periodo: IdfacturaExpedidaHuellaType = field(
        metadata={
            "name": "RegistroFacturacionInicialPeriodo",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    registro_facturacion_final_periodo: IdfacturaExpedidaHuellaType = field(
        metadata={
            "name": "RegistroFacturacionFinalPeriodo",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    numero_de_registros_facturacion_alta_exportados: str = field(
        metadata={
            "name": "NumeroDeRegistrosFacturacionAltaExportados",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 9,
            "pattern": r"\d{1,9}",
        }
    )
    suma_cuota_total_alta: str = field(
        metadata={
            "name": "SumaCuotaTotalAlta",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        }
    )
    suma_importe_total_alta: str = field(
        metadata={
            "name": "SumaImporteTotalAlta",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        }
    )
    numero_de_registros_facturacion_anulacion_exportados: str = field(
        metadata={
            "name": "NumeroDeRegistrosFacturacionAnulacionExportados",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 9,
            "pattern": r"\d{1,9}",
        }
    )
    registros_facturacion_exportados_dejan_de_conservarse: SiNoType = field(
        metadata={
            "name": "RegistrosFacturacionExportadosDejanDeConservarse",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class IdotroType:
    """
    Identificador de persona Física o jurídica distinto del NIF (Código
    pais, Tipo de Identificador, y hasta 15 caractéres) No se permite
    CodigoPais=ES e IDType=01-NIFContraparte para ese caso, debe utilizarse
    NIF en lugar de IDOtro.
    """

    class Meta:
        name = "IDOtroType"

    codigo_pais: None | CountryType2 = field(
        default=None,
        metadata={
            "name": "CodigoPais",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )
    idtype: PersonaFisicaJuridicaIdtypeType = field(
        metadata={
            "name": "IDType",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    id: str = field(
        metadata={
            "name": "ID",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 20,
        }
    )


@dataclass(kw_only=True)
class LanzamientoProcesoDeteccionAnomaliasRegEventoType:
    realizado_proceso_sobre_integridad_huellas_reg_evento: SiNoType = field(
        metadata={
            "name": "RealizadoProcesoSobreIntegridadHuellasRegEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    numero_de_registros_evento_procesados_sobre_integridad_huellas: None | str = field(
        default=None,
        metadata={
            "name": "NumeroDeRegistrosEventoProcesadosSobreIntegridadHuellas",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "max_length": 5,
            "pattern": r"\d{1,5}",
        },
    )
    realizado_proceso_sobre_integridad_firmas_reg_evento: SiNoType = field(
        metadata={
            "name": "RealizadoProcesoSobreIntegridadFirmasRegEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    numero_de_registros_evento_procesados_sobre_integridad_firmas: None | str = field(
        default=None,
        metadata={
            "name": "NumeroDeRegistrosEventoProcesadosSobreIntegridadFirmas",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "max_length": 5,
            "pattern": r"\d{1,5}",
        },
    )
    realizado_proceso_sobre_trazabilidad_cadena_reg_evento: SiNoType = field(
        metadata={
            "name": "RealizadoProcesoSobreTrazabilidadCadenaRegEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    numero_de_registros_evento_procesados_sobre_trazabilidad_cadena: None | str = field(
        default=None,
        metadata={
            "name": "NumeroDeRegistrosEventoProcesadosSobreTrazabilidadCadena",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "max_length": 5,
            "pattern": r"\d{1,5}",
        },
    )
    realizado_proceso_sobre_trazabilidad_fechas_reg_evento: SiNoType = field(
        metadata={
            "name": "RealizadoProcesoSobreTrazabilidadFechasRegEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    numero_de_registros_evento_procesados_sobre_trazabilidad_fechas: None | str = field(
        default=None,
        metadata={
            "name": "NumeroDeRegistrosEventoProcesadosSobreTrazabilidadFechas",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "max_length": 5,
            "pattern": r"\d{1,5}",
        },
    )


@dataclass(kw_only=True)
class LanzamientoProcesoDeteccionAnomaliasRegFacturacionType:
    realizado_proceso_sobre_integridad_huellas_reg_facturacion: SiNoType = field(
        metadata={
            "name": "RealizadoProcesoSobreIntegridadHuellasRegFacturacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    numero_de_registros_facturacion_procesados_sobre_integridad_huellas: None | str = (
        field(
            default=None,
            metadata={
                "name": "NumeroDeRegistrosFacturacionProcesadosSobreIntegridadHuellas",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
                "max_length": 7,
                "pattern": r"\d{1,7}",
            },
        )
    )
    realizado_proceso_sobre_integridad_firmas_reg_facturacion: SiNoType = field(
        metadata={
            "name": "RealizadoProcesoSobreIntegridadFirmasRegFacturacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    numero_de_registros_facturacion_procesados_sobre_integridad_firmas: None | str = (
        field(
            default=None,
            metadata={
                "name": "NumeroDeRegistrosFacturacionProcesadosSobreIntegridadFirmas",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
                "max_length": 7,
                "pattern": r"\d{1,7}",
            },
        )
    )
    realizado_proceso_sobre_trazabilidad_cadena_reg_facturacion: SiNoType = field(
        metadata={
            "name": "RealizadoProcesoSobreTrazabilidadCadenaRegFacturacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    numero_de_registros_facturacion_procesados_sobre_trazabilidad_cadena: None | str = (
        field(
            default=None,
            metadata={
                "name": "NumeroDeRegistrosFacturacionProcesadosSobreTrazabilidadCadena",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
                "max_length": 7,
                "pattern": r"\d{1,7}",
            },
        )
    )
    realizado_proceso_sobre_trazabilidad_fechas_reg_facturacion: SiNoType = field(
        metadata={
            "name": "RealizadoProcesoSobreTrazabilidadFechasRegFacturacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    numero_de_registros_facturacion_procesados_sobre_trazabilidad_fechas: None | str = (
        field(
            default=None,
            metadata={
                "name": "NumeroDeRegistrosFacturacionProcesadosSobreTrazabilidadFechas",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
                "max_length": 7,
                "pattern": r"\d{1,7}",
            },
        )
    )


@dataclass(kw_only=True)
class RegEventoAntType:
    """
    :ivar tipo_evento:
    :ivar fecha_hora_huso_gen_evento: Formato: YYYY-MM-DDThh:mm:ssTZD
        (ej: 2024-01-01T19:20:30+01:00) (ISO 8601)
    :ivar huella_evento:
    """

    tipo_evento: TipoEventoType = field(
        metadata={
            "name": "TipoEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    fecha_hora_huso_gen_evento: XmlDateTime = field(
        metadata={
            "name": "FechaHoraHusoGenEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    huella_evento: str = field(
        metadata={
            "name": "HuellaEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 64,
        }
    )


@dataclass(kw_only=True)
class RegEventoType:
    """
    :ivar tipo_evento:
    :ivar fecha_hora_huso_evento: Formato: YYYY-MM-DDThh:mm:ssTZD (ej:
        2024-01-01T19:20:30+01:00) (ISO 8601)
    :ivar huella_evento:
    """

    tipo_evento: TipoEventoType = field(
        metadata={
            "name": "TipoEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    fecha_hora_huso_evento: XmlDateTime = field(
        metadata={
            "name": "FechaHoraHusoEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    huella_evento: str = field(
        metadata={
            "name": "HuellaEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 64,
        }
    )


@dataclass(kw_only=True)
class TipoEventoAgrType:
    tipo_evento: TipoEventoType = field(
        metadata={
            "name": "TipoEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    numero_de_eventos: str = field(
        metadata={
            "name": "NumeroDeEventos",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 4,
            "pattern": r"\d{1,4}",
        }
    )


@dataclass(kw_only=True)
class DeteccionAnomaliasRegEventoType:
    tipo_anomalia: TipoAnomaliaType = field(
        metadata={
            "name": "TipoAnomalia",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    otros_datos_anomalia: None | str = field(
        default=None,
        metadata={
            "name": "OtrosDatosAnomalia",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "max_length": 100,
        },
    )
    reg_evento_anomalo: None | RegEventoType = field(
        default=None,
        metadata={
            "name": "RegEventoAnomalo",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )


@dataclass(kw_only=True)
class EncadenamientoType:
    primer_evento: None | str = field(
        default=None,
        metadata={
            "name": "PrimerEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "max_length": 1,
        },
    )
    evento_anterior: None | RegEventoAntType = field(
        default=None,
        metadata={
            "name": "EventoAnterior",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )


@dataclass(kw_only=True)
class ExportacionRegEventoPeriodoType:
    """
    :ivar fecha_hora_huso_inicio_periodo_export: Formato: YYYY-MM-
        DDThh:mm:ssTZD (ej: 2024-01-01T19:20:30+01:00) (ISO 8601)
    :ivar fecha_hora_huso_fin_periodo_export: Formato: YYYY-MM-
        DDThh:mm:ssTZD (ej: 2024-01-01T19:20:30+01:00) (ISO 8601)
    :ivar registro_evento_inicial_periodo:
    :ivar registro_evento_final_periodo:
    :ivar numero_de_reg_evento_exportados:
    :ivar reg_evento_exportados_dejan_de_conservarse:
    """

    fecha_hora_huso_inicio_periodo_export: XmlDateTime = field(
        metadata={
            "name": "FechaHoraHusoInicioPeriodoExport",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    fecha_hora_huso_fin_periodo_export: XmlDateTime = field(
        metadata={
            "name": "FechaHoraHusoFinPeriodoExport",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    registro_evento_inicial_periodo: RegEventoType = field(
        metadata={
            "name": "RegistroEventoInicialPeriodo",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    registro_evento_final_periodo: RegEventoType = field(
        metadata={
            "name": "RegistroEventoFinalPeriodo",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    numero_de_reg_evento_exportados: str = field(
        metadata={
            "name": "NumeroDeRegEventoExportados",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 7,
            "pattern": r"\d{1,7}",
        }
    )
    reg_evento_exportados_dejan_de_conservarse: SiNoType = field(
        metadata={
            "name": "RegEventoExportadosDejanDeConservarse",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class PersonaFisicaJuridicaType:
    """
    Datos de una persona física o jurídica Española o Extranjera.
    """

    nombre_razon: str = field(
        metadata={
            "name": "NombreRazon",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 120,
        }
    )
    nif: None | str = field(
        default=None,
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "length": 9,
        },
    )
    idotro: None | IdotroType = field(
        default=None,
        metadata={
            "name": "IDOtro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )


@dataclass(kw_only=True)
class ResumenEventosType:
    tipo_evento: list[TipoEventoAgrType] = field(
        default_factory=list,
        metadata={
            "name": "TipoEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "min_occurs": 1,
            "max_occurs": 20,
        },
    )
    registro_facturacion_inicial_periodo: None | IdfacturaExpedidaHuellaType = field(
        default=None,
        metadata={
            "name": "RegistroFacturacionInicialPeriodo",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )
    registro_facturacion_final_periodo: None | IdfacturaExpedidaHuellaType = field(
        default=None,
        metadata={
            "name": "RegistroFacturacionFinalPeriodo",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )
    numero_de_registros_facturacion_alta_generados: str = field(
        metadata={
            "name": "NumeroDeRegistrosFacturacionAltaGenerados",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 6,
            "pattern": r"\d{1,6}",
        }
    )
    suma_cuota_total_alta: str = field(
        metadata={
            "name": "SumaCuotaTotalAlta",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        }
    )
    suma_importe_total_alta: str = field(
        metadata={
            "name": "SumaImporteTotalAlta",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        }
    )
    numero_de_registros_facturacion_anulacion_generados: str = field(
        metadata={
            "name": "NumeroDeRegistrosFacturacionAnulacionGenerados",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 6,
            "pattern": r"\d{1,6}",
        }
    )


@dataclass(kw_only=True)
class SistemaInformaticoType:
    nombre_razon: str = field(
        metadata={
            "name": "NombreRazon",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 120,
        }
    )
    nif: None | str = field(
        default=None,
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "length": 9,
        },
    )
    idotro: None | IdotroType = field(
        default=None,
        metadata={
            "name": "IDOtro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )
    nombre_sistema_informatico: None | str = field(
        default=None,
        metadata={
            "name": "NombreSistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "max_length": 30,
        },
    )
    id_sistema_informatico: str = field(
        metadata={
            "name": "IdSistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 2,
        }
    )
    version: str = field(
        metadata={
            "name": "Version",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 50,
        }
    )
    numero_instalacion: str = field(
        metadata={
            "name": "NumeroInstalacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 100,
        }
    )
    tipo_uso_posible_solo_verifactu: None | SiNoType = field(
        default=None,
        metadata={
            "name": "TipoUsoPosibleSoloVerifactu",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )
    tipo_uso_posible_multi_ot: None | SiNoType = field(
        default=None,
        metadata={
            "name": "TipoUsoPosibleMultiOT",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )
    indicador_multiples_ot: None | SiNoType = field(
        default=None,
        metadata={
            "name": "IndicadorMultiplesOT",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )


@dataclass(kw_only=True)
class DatosPropiosEventoType:
    lanzamiento_proceso_deteccion_anomalias_reg_facturacion: (
        None | LanzamientoProcesoDeteccionAnomaliasRegFacturacionType
    ) = field(
        default=None,
        metadata={
            "name": "LanzamientoProcesoDeteccionAnomaliasRegFacturacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )
    deteccion_anomalias_reg_facturacion: None | DeteccionAnomaliasRegFacturacionType = (
        field(
            default=None,
            metadata={
                "name": "DeteccionAnomaliasRegFacturacion",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            },
        )
    )
    lanzamiento_proceso_deteccion_anomalias_reg_evento: (
        None | LanzamientoProcesoDeteccionAnomaliasRegEventoType
    ) = field(
        default=None,
        metadata={
            "name": "LanzamientoProcesoDeteccionAnomaliasRegEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )
    deteccion_anomalias_reg_evento: None | DeteccionAnomaliasRegEventoType = field(
        default=None,
        metadata={
            "name": "DeteccionAnomaliasRegEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )
    exportacion_reg_facturacion_periodo: None | ExportacionRegFacturacionPeriodoType = (
        field(
            default=None,
            metadata={
                "name": "ExportacionRegFacturacionPeriodo",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            },
        )
    )
    exportacion_reg_evento_periodo: None | ExportacionRegEventoPeriodoType = field(
        default=None,
        metadata={
            "name": "ExportacionRegEventoPeriodo",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )
    resumen_eventos: None | ResumenEventosType = field(
        default=None,
        metadata={
            "name": "ResumenEventos",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )


@dataclass(kw_only=True)
class EventoType:
    """
    :ivar sistema_informatico:
    :ivar obligado_emision: Obligado a expedir la factura.
    :ivar emitida_por_tercero_odestinatario:
    :ivar tercero_odestinatario:
    :ivar fecha_hora_huso_gen_evento: Formato: YYYY-MM-DDThh:mm:ssTZD
        (ej: 2024-01-01T19:20:30+01:00) (ISO 8601)
    :ivar tipo_evento:
    :ivar datos_propios_evento:
    :ivar otros_datos_evento:
    :ivar encadenamiento:
    :ivar tipo_huella:
    :ivar huella_evento:
    :ivar signature:
    """

    sistema_informatico: SistemaInformaticoType = field(
        metadata={
            "name": "SistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    obligado_emision: PersonaFisicaJuridicaEstype = field(
        metadata={
            "name": "ObligadoEmision",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    emitida_por_tercero_odestinatario: None | TercerosOdestinatarioType = field(
        default=None,
        metadata={
            "name": "EmitidaPorTerceroODestinatario",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )
    tercero_odestinatario: None | PersonaFisicaJuridicaType = field(
        default=None,
        metadata={
            "name": "TerceroODestinatario",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )
    fecha_hora_huso_gen_evento: XmlDateTime = field(
        metadata={
            "name": "FechaHoraHusoGenEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    tipo_evento: TipoEventoType = field(
        metadata={
            "name": "TipoEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    datos_propios_evento: None | DatosPropiosEventoType = field(
        default=None,
        metadata={
            "name": "DatosPropiosEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
        },
    )
    otros_datos_evento: None | str = field(
        default=None,
        metadata={
            "name": "OtrosDatosEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "max_length": 100,
        },
    )
    encadenamiento: EncadenamientoType = field(
        metadata={
            "name": "Encadenamiento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    tipo_huella: TipoHuellaType = field(
        metadata={
            "name": "TipoHuella",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
        }
    )
    huella_evento: str = field(
        metadata={
            "name": "HuellaEvento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd",
            "required": True,
            "max_length": 64,
        }
    )
    signature: Signature = field(
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class RegistroEvento:
    class Meta:
        namespace = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/EventosSIF.xsd"

    idversion: VersionType = field(
        metadata={
            "name": "IDVersion",
            "type": "Element",
            "required": True,
        }
    )
    evento: EventoType = field(
        metadata={
            "name": "Evento",
            "type": "Element",
            "required": True,
        }
    )
