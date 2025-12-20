from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from xsdata.models.datatype import XmlDateTime

from app.infrastructure.aeat.models.xmldsig_core_schema import Signature

__NAMESPACE__ = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"


class CalificacionOperacionType(str, Enum):
    """
    :cvar S1: OPERACIÓN SUJETA Y NO EXENTA - SIN INVERSIÓN DEL SUJETO
        PASIVO.
    :cvar S2: OPERACIÓN SUJETA Y NO EXENTA - CON INVERSIÓN DEL SUJETO
        PASIVO
    :cvar N1: OPERACIÓN NO SUJETA ARTÍCULO 7, 14, OTROS.
    :cvar N2: OPERACIÓN NO SUJETA POR REGLAS DE LOCALIZACIÓN
    """

    S1 = "S1"
    S2 = "S2"
    N1 = "N1"
    N2 = "N2"


class ClaveTipoFacturaType(str, Enum):
    """
    :cvar F1: FACTURA (ART. 6, 7.2 Y 7.3 DEL RD 1619/2012)
    :cvar F2: FACTURA SIMPLIFICADA Y FACTURAS SIN IDENTIFICACIÓN DEL
        DESTINATARIO ART. 6.1.D) RD 1619/2012
    :cvar R1: FACTURA RECTIFICATIVA (Art 80.1 y 80.2 y error fundado en
        derecho)
    :cvar R2: FACTURA RECTIFICATIVA (Art. 80.3)
    :cvar R3: FACTURA RECTIFICATIVA (Art. 80.4)
    :cvar R4: FACTURA RECTIFICATIVA (Resto)
    :cvar R5: FACTURA RECTIFICATIVA EN FACTURAS SIMPLIFICADAS
    :cvar F3: FACTURA EMITIDA EN SUSTITUCIÓN DE FACTURAS SIMPLIFICADAS
        FACTURADAS Y DECLARADAS
    """

    F1 = "F1"
    F2 = "F2"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    R5 = "R5"
    F3 = "F3"


class ClaveTipoRectificativaType(str, Enum):
    """
    :cvar S: SUSTITUTIVA
    :cvar I: INCREMENTAL
    """

    S = "S"
    I = "I"


class CompletaSinDestinatarioType(str, Enum):
    S = "S"
    N = "N"


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


class CuponType(str, Enum):
    S = "S"
    N = "N"


@dataclass(kw_only=True)
class DatosPresentacion2Type:
    nifpresentador: str = field(
        metadata={
            "name": "NIFPresentador",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 9,
        }
    )
    timestamp_presentacion: XmlDateTime = field(
        metadata={
            "name": "TimestampPresentacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    id_peticion: str = field(
        metadata={
            "name": "IdPeticion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 20,
        }
    )


@dataclass(kw_only=True)
class DatosPresentacionType:
    nifpresentador: str = field(
        metadata={
            "name": "NIFPresentador",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 9,
        }
    )
    timestamp_presentacion: XmlDateTime = field(
        metadata={
            "name": "TimestampPresentacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class DesgloseRectificacionType:
    """
    Desglose de Base y Cuota sustituida en las Facturas Rectificativas
    sustitutivas.
    """

    base_rectificada: str = field(
        metadata={
            "name": "BaseRectificada",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        }
    )
    cuota_rectificada: str = field(
        metadata={
            "name": "CuotaRectificada",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        }
    )
    cuota_recargo_rectificado: None | str = field(
        default=None,
        metadata={
            "name": "CuotaRecargoRectificado",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        },
    )


@dataclass(kw_only=True)
class EncadenamientoFacturaAnteriorType:
    """
    Datos de encadenamiento.

    :ivar idemisor_factura: NIF del obligado a expedir la factura a que
        se refiere el registro de facturación anterior
    :ivar num_serie_factura:
    :ivar fecha_expedicion_factura:
    :ivar huella:
    """

    idemisor_factura: str = field(
        metadata={
            "name": "IDEmisorFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 9,
        }
    )
    num_serie_factura: str = field(
        metadata={
            "name": "NumSerieFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 60,
        }
    )
    fecha_expedicion_factura: str = field(
        metadata={
            "name": "FechaExpedicionFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 10,
            "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
        }
    )
    huella: str = field(
        metadata={
            "name": "Huella",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 64,
        }
    )


class EstadoRegistroSftype(str, Enum):
    """
    :cvar CORRECTA: El registro se ha almacenado sin errores
    :cvar ACEPTADA_CON_ERRORES: El registro que se ha almacenado tiene
        algunos errores. Ver detalle del error
    :cvar ANULADA: El registro almacenado ha sido anulado
    """

    CORRECTA = "Correcta"
    ACEPTADA_CON_ERRORES = "AceptadaConErrores"
    ANULADA = "Anulada"


class FinRequerimientoType(str, Enum):
    S = "S"
    N = "N"


class GeneradoPorType(str, Enum):
    """
    :cvar E: Expedidor (obligado a Expedir la factura anulada).
    :cvar D: Destinatario
    :cvar T: Tercero
    """

    E = "E"
    D = "D"
    T = "T"


@dataclass(kw_only=True)
class IdfacturaArtype:
    """
    Datos de identificación de factura sustituida o rectificada.

    El NIF se cogerá del NIF indicado en el bloque IDFactura.

    :ivar idemisor_factura: NIF del obligado
    :ivar num_serie_factura: Nº Serie+Nº Factura de la factura
    :ivar fecha_expedicion_factura: Fecha de emisión de la factura
        sustituida o rectificada
    """

    class Meta:
        name = "IDFacturaARType"

    idemisor_factura: str = field(
        metadata={
            "name": "IDEmisorFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 9,
        }
    )
    num_serie_factura: str = field(
        metadata={
            "name": "NumSerieFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "min_length": 1,
            "max_length": 60,
        }
    )
    fecha_expedicion_factura: str = field(
        metadata={
            "name": "FechaExpedicionFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 10,
            "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
        }
    )


@dataclass(kw_only=True)
class IdfacturaExpedidaBctype:
    """
    Datos de identificación de factura expedida para operaciones de
    consulta.

    :ivar idemisor_factura:
    :ivar num_serie_factura: Nº Serie+Nº Factura de la Factura del
        Emisor.
    :ivar fecha_expedicion_factura: Fecha de emisión de la factura
    """

    class Meta:
        name = "IDFacturaExpedidaBCType"

    idemisor_factura: str = field(
        metadata={
            "name": "IDEmisorFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 9,
        }
    )
    num_serie_factura: str = field(
        metadata={
            "name": "NumSerieFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "min_length": 1,
            "max_length": 60,
        }
    )
    fecha_expedicion_factura: str = field(
        metadata={
            "name": "FechaExpedicionFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 10,
            "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
        }
    )


@dataclass(kw_only=True)
class IdfacturaExpedidaBajaType:
    """
    Datos de identificación de factura que se anula para operaciones de
    baja.

    :ivar idemisor_factura_anulada: NIF del obligado
    :ivar num_serie_factura_anulada: Nº Serie+Nº Factura de la Factura
        que se anula.
    :ivar fecha_expedicion_factura_anulada: Fecha de emisión de la
        factura que se anula
    """

    class Meta:
        name = "IDFacturaExpedidaBajaType"

    idemisor_factura_anulada: str = field(
        metadata={
            "name": "IDEmisorFacturaAnulada",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 9,
        }
    )
    num_serie_factura_anulada: str = field(
        metadata={
            "name": "NumSerieFacturaAnulada",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "min_length": 1,
            "max_length": 60,
        }
    )
    fecha_expedicion_factura_anulada: str = field(
        metadata={
            "name": "FechaExpedicionFacturaAnulada",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 10,
            "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
        }
    )


@dataclass(kw_only=True)
class IdfacturaExpedidaType:
    """
    Datos de identificación de factura.

    :ivar idemisor_factura: NIF del obligado
    :ivar num_serie_factura: Nº Serie+Nº Factura de la Factura del
        Emisor
    :ivar fecha_expedicion_factura: Fecha de emisión de la factura
    """

    class Meta:
        name = "IDFacturaExpedidaType"

    idemisor_factura: str = field(
        metadata={
            "name": "IDEmisorFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 9,
        }
    )
    num_serie_factura: str = field(
        metadata={
            "name": "NumSerieFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "min_length": 1,
            "max_length": 60,
        }
    )
    fecha_expedicion_factura: str = field(
        metadata={
            "name": "FechaExpedicionFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 10,
            "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
        }
    )


class IdOperacionesTrascendenciaTributariaType(str, Enum):
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
    VALUE_14 = "14"
    VALUE_15 = "15"
    VALUE_17 = "17"
    VALUE_18 = "18"
    VALUE_19 = "19"
    VALUE_20 = "20"
    VALUE_21 = "21"


class ImpuestoType(str, Enum):
    """
    :cvar VALUE_01: Impuesto sobre el Valor Añadido (IVA)
    :cvar VALUE_02: Impuesto sobre la Producción, los Servicios y la
        Importación (IPSI) de Ceuta y Melilla
    :cvar VALUE_03: Impuesto General Indirecto Canario (IGIC)
    :cvar VALUE_05: Otros
    """

    VALUE_01 = "01"
    VALUE_02 = "02"
    VALUE_03 = "03"
    VALUE_05 = "05"


class IncidenciaType(str, Enum):
    S = "S"
    N = "N"


class IndicadorRepresentanteType(str, Enum):
    S = "S"


class MacrodatoType(str, Enum):
    S = "S"
    N = "N"


class MostrarNombreRazonEmisorType(str, Enum):
    S = "S"
    N = "N"


class MostrarSistemaInformaticoType(str, Enum):
    S = "S"
    N = "N"


@dataclass(kw_only=True)
class ObligadoEmisionConsultaType:
    """
    Datos de una persona física o jurídica Española con un NIF asociado.
    """

    nombre_razon: str = field(
        metadata={
            "name": "NombreRazon",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 120,
        }
    )
    nif: str = field(
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 9,
        }
    )


@dataclass(kw_only=True)
class ObligadoGeneracionType:
    nombre_razon: str = field(
        metadata={
            "name": "NombreRazon",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 120,
        }
    )
    nif: str = field(
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 9,
        }
    )


class OperacionExentaType(str, Enum):
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    E4 = "E4"
    E5 = "E5"
    E6 = "E6"
    E7 = "E7"
    E8 = "E8"


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
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 120,
        }
    )
    nif: str = field(
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
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


class PrimerRegistroCadenaType(str, Enum):
    S = "S"


@dataclass(kw_only=True)
class RangoFechaExpedicionType:
    """
    Rango de fechas de expedicion.
    """

    desde: None | str = field(
        default=None,
        metadata={
            "name": "Desde",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "length": 10,
            "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
        },
    )
    hasta: None | str = field(
        default=None,
        metadata={
            "name": "Hasta",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "length": 10,
            "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
        },
    )


class RechazoPrevioAnulacionType(str, Enum):
    S = "S"
    N = "N"


class RechazoPrevioType(str, Enum):
    """
    :cvar N: No ha habido rechazo previo por la AEAT.
    :cvar S: Ha habido rechazo previo por la AEAT.
    :cvar X: Independientemente de si ha habido o no algún rechazo
        previo por la AEAT, el registro de facturación no existe en la
        AEAT (registro existente en ese SIF o en algún SIF del obligado
        tributario y que no se remitió a la AEAT, por ejemplo, al
        acogerse a Veri*factu desde no Veri*factu). No deberían existir
        operaciones de alta (N,X), por lo que no se admiten.
    """

    N = "N"
    S = "S"
    X = "X"


class SiNoType(str, Enum):
    S = "S"
    N = "N"


class SimplificadaCualificadaType(str, Enum):
    S = "S"
    N = "N"


class SinRegistroPrevioType(str, Enum):
    S = "S"
    N = "N"


class SubsanacionType(str, Enum):
    S = "S"
    N = "N"


class TercerosOdestinatarioType(str, Enum):
    """
    :cvar D: Destinatario
    :cvar T: Tercero
    """

    D = "D"
    T = "T"


class TipoHuellaType(str, Enum):
    """
    :cvar VALUE_01: SHA-256
    """

    VALUE_01 = "01"


class TipoOperacionType(str, Enum):
    """
    :cvar ALTA: La operación realizada ha sido un alta
    :cvar ANULACION: La operación realizada ha sido una anulación
    """

    ALTA = "Alta"
    ANULACION = "Anulacion"


class TipoPeriodoType(str, Enum):
    """
    Período de la factura.

    :cvar VALUE_01: Enero
    :cvar VALUE_02: Febrero
    :cvar VALUE_03: Marzo
    :cvar VALUE_04: Abril
    :cvar VALUE_05: Mayo
    :cvar VALUE_06: Junio
    :cvar VALUE_07: Julio
    :cvar VALUE_08: Agosto
    :cvar VALUE_09: Septiembre
    :cvar VALUE_10: Octubre
    :cvar VALUE_11: Noviembre
    :cvar VALUE_12: Diciembre
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


class VersionType(str, Enum):
    VALUE_1_0 = "1.0"


@dataclass(kw_only=True)
class CabeceraConsultaSf:
    """
    Cabecera de la Cobnsulta.

    :ivar idversion:
    :ivar obligado_emision: Obligado a la emision de los registros de
        facturacion
    :ivar destinatario: Destinatario (a veces también denominado
        contraparte, es decir, el cliente) de la operación
    :ivar indicador_representante: Flag opcional que tendrá valor S si
        quien realiza la cosulta es el representante/asesor del obligado
        tributario. Permite, a quien realiza la cosulta, obtener los
        registros de facturación en los que figura como representante.
        Este flag solo se puede cumplimentar cuando esté informado el
        obligado tributario en la consulta
    """

    idversion: VersionType = field(
        metadata={
            "name": "IDVersion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    obligado_emision: None | ObligadoEmisionConsultaType = field(
        default=None,
        metadata={
            "name": "ObligadoEmision",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    destinatario: None | PersonaFisicaJuridicaEstype = field(
        default=None,
        metadata={
            "name": "Destinatario",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    indicador_representante: None | IndicadorRepresentanteType = field(
        default=None,
        metadata={
            "name": "IndicadorRepresentante",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )


@dataclass(kw_only=True)
class CabeceraType:
    """
    Datos de cabecera.

    :ivar obligado_emision: Obligado a expedir la factura.
    :ivar representante: Representante del obligado tributario. A
        rellenar solo en caso de que los registros de facturación
        remitdos hayan sido generados por un representante/asesor del
        obligado tributario.
    :ivar remision_voluntaria:
    :ivar remision_requerimiento:
    """

    obligado_emision: PersonaFisicaJuridicaEstype = field(
        metadata={
            "name": "ObligadoEmision",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    representante: None | PersonaFisicaJuridicaEstype = field(
        default=None,
        metadata={
            "name": "Representante",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    remision_voluntaria: None | CabeceraType.RemisionVoluntaria = field(
        default=None,
        metadata={
            "name": "RemisionVoluntaria",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    remision_requerimiento: None | CabeceraType.RemisionRequerimiento = field(
        default=None,
        metadata={
            "name": "RemisionRequerimiento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )

    @dataclass(kw_only=True)
    class RemisionVoluntaria:
        fecha_fin_veri_factu: None | str = field(
            default=None,
            metadata={
                "name": "FechaFinVeriFactu",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
                "length": 10,
                "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
            },
        )
        incidencia: None | IncidenciaType = field(
            default=None,
            metadata={
                "name": "Incidencia",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            },
        )

    @dataclass(kw_only=True)
    class RemisionRequerimiento:
        ref_requerimiento: str = field(
            metadata={
                "name": "RefRequerimiento",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
                "required": True,
                "max_length": 18,
            }
        )
        fin_requerimiento: None | FinRequerimientoType = field(
            default=None,
            metadata={
                "name": "FinRequerimiento",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            },
        )


@dataclass(kw_only=True)
class DetalleType:
    impuesto: None | ImpuestoType = field(
        default=None,
        metadata={
            "name": "Impuesto",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    clave_regimen: None | IdOperacionesTrascendenciaTributariaType = field(
        default=None,
        metadata={
            "name": "ClaveRegimen",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    calificacion_operacion: None | CalificacionOperacionType = field(
        default=None,
        metadata={
            "name": "CalificacionOperacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    operacion_exenta: None | OperacionExentaType = field(
        default=None,
        metadata={
            "name": "OperacionExenta",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    tipo_impositivo: None | str = field(
        default=None,
        metadata={
            "name": "TipoImpositivo",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "pattern": r"\d{1,3}(\.\d{0,2})?",
        },
    )
    base_imponible_oimporte_no_sujeto: str = field(
        metadata={
            "name": "BaseImponibleOimporteNoSujeto",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        }
    )
    base_imponible_acoste: None | str = field(
        default=None,
        metadata={
            "name": "BaseImponibleACoste",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        },
    )
    cuota_repercutida: None | str = field(
        default=None,
        metadata={
            "name": "CuotaRepercutida",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        },
    )
    tipo_recargo_equivalencia: None | str = field(
        default=None,
        metadata={
            "name": "TipoRecargoEquivalencia",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "pattern": r"\d{1,3}(\.\d{0,2})?",
        },
    )
    cuota_recargo_equivalencia: None | str = field(
        default=None,
        metadata={
            "name": "CuotaRecargoEquivalencia",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        },
    )


@dataclass(kw_only=True)
class FechaExpedicionConsultaType:
    fecha_expedicion_factura: None | str = field(
        default=None,
        metadata={
            "name": "FechaExpedicionFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "length": 10,
            "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
        },
    )
    rango_fecha_expedicion: None | RangoFechaExpedicionType = field(
        default=None,
        metadata={
            "name": "RangoFechaExpedicion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
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
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    idtype: PersonaFisicaJuridicaIdtypeType = field(
        metadata={
            "name": "IDType",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    id: str = field(
        metadata={
            "name": "ID",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 20,
        }
    )


@dataclass(kw_only=True)
class OperacionType:
    tipo_operacion: TipoOperacionType = field(
        metadata={
            "name": "TipoOperacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    subsanacion: None | SubsanacionType = field(
        default=None,
        metadata={
            "name": "Subsanacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    rechazo_previo: None | RechazoPrevioType = field(
        default=None,
        metadata={
            "name": "RechazoPrevio",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    sin_registro_previo: None | SinRegistroPrevioType = field(
        default=None,
        metadata={
            "name": "SinRegistroPrevio",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )


@dataclass(kw_only=True)
class PeriodoImputacionType:
    ejercicio: str = field(
        metadata={
            "name": "Ejercicio",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "length": 4,
            "pattern": r"\d{4,4}",
        }
    )
    periodo: TipoPeriodoType = field(
        metadata={
            "name": "Periodo",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class RegistroDuplicadoType:
    """
    :ivar id_peticion_registro_duplicado: IdPeticion asociado a la
        factura registrada previamente en el sistema. Solo se suministra
        si la factura enviada es rechazada por estar duplicada
    :ivar estado_registro_duplicado: Estado del registro duplicado
        almacenado en el sistema. Los estados posibles son: Correcta,
        AceptadaConErrores y Anulada. Solo se suministra si la factura
        enviada es rechazada por estar duplicada
    :ivar codigo_error_registro: Código del error de registro duplicado
        almacenado en el sistema, en su caso.
    :ivar descripcion_error_registro: Descripción detallada del error de
        registro duplicado almacenado en el sistema, en su caso.
    """

    id_peticion_registro_duplicado: str = field(
        metadata={
            "name": "IdPeticionRegistroDuplicado",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 20,
        }
    )
    estado_registro_duplicado: EstadoRegistroSftype = field(
        metadata={
            "name": "EstadoRegistroDuplicado",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    codigo_error_registro: None | int = field(
        default=None,
        metadata={
            "name": "CodigoErrorRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    descripcion_error_registro: None | str = field(
        default=None,
        metadata={
            "name": "DescripcionErrorRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "max_length": 500,
        },
    )


@dataclass(kw_only=True)
class ContraparteConsultaType:
    """
    Datos de una persona física o jurídica Española o Extranjera.
    """

    nombre_razon: str = field(
        metadata={
            "name": "NombreRazon",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 120,
        }
    )
    nif: None | str = field(
        default=None,
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "length": 9,
        },
    )
    idotro: None | IdotroType = field(
        default=None,
        metadata={
            "name": "IDOtro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )


@dataclass(kw_only=True)
class DesgloseType:
    detalle_desglose: list[DetalleType] = field(
        default_factory=list,
        metadata={
            "name": "DetalleDesglose",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "min_occurs": 1,
            "max_occurs": 12,
        },
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
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 120,
        }
    )
    nif: None | str = field(
        default=None,
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "length": 9,
        },
    )
    idotro: None | IdotroType = field(
        default=None,
        metadata={
            "name": "IDOtro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )


@dataclass(kw_only=True)
class SistemaInformaticoConsultaType:
    nombre_razon: str = field(
        metadata={
            "name": "NombreRazon",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 120,
        }
    )
    nif: None | str = field(
        default=None,
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "length": 9,
        },
    )
    idotro: None | IdotroType = field(
        default=None,
        metadata={
            "name": "IDOtro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    nombre_sistema_informatico: None | str = field(
        default=None,
        metadata={
            "name": "NombreSistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "max_length": 30,
        },
    )
    id_sistema_informatico: str = field(
        metadata={
            "name": "IdSistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 2,
        }
    )
    version: None | str = field(
        default=None,
        metadata={
            "name": "Version",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "max_length": 50,
        },
    )
    numero_instalacion: str = field(
        metadata={
            "name": "NumeroInstalacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 100,
        }
    )
    tipo_uso_posible_solo_verifactu: None | SiNoType = field(
        default=None,
        metadata={
            "name": "TipoUsoPosibleSoloVerifactu",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    tipo_uso_posible_multi_ot: None | SiNoType = field(
        default=None,
        metadata={
            "name": "TipoUsoPosibleMultiOT",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    indicador_multiples_ot: None | SiNoType = field(
        default=None,
        metadata={
            "name": "IndicadorMultiplesOT",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )


@dataclass(kw_only=True)
class SistemaInformaticoType:
    nombre_razon: str = field(
        metadata={
            "name": "NombreRazon",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 120,
        }
    )
    nif: None | str = field(
        default=None,
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "length": 9,
        },
    )
    idotro: None | IdotroType = field(
        default=None,
        metadata={
            "name": "IDOtro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    nombre_sistema_informatico: str = field(
        metadata={
            "name": "NombreSistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 30,
        }
    )
    id_sistema_informatico: str = field(
        metadata={
            "name": "IdSistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 2,
        }
    )
    version: str = field(
        metadata={
            "name": "Version",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 50,
        }
    )
    numero_instalacion: str = field(
        metadata={
            "name": "NumeroInstalacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 100,
        }
    )
    tipo_uso_posible_solo_verifactu: SiNoType = field(
        metadata={
            "name": "TipoUsoPosibleSoloVerifactu",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    tipo_uso_posible_multi_ot: SiNoType = field(
        metadata={
            "name": "TipoUsoPosibleMultiOT",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    indicador_multiples_ot: SiNoType = field(
        metadata={
            "name": "IndicadorMultiplesOT",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class RegistroFacturacionAltaType:
    """
    Datos correspondientes al registro de facturacion de alta.

    :ivar idversion:
    :ivar idfactura:
    :ivar ref_externa:
    :ivar nombre_razon_emisor:
    :ivar subsanacion:
    :ivar rechazo_previo:
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
    :ivar signature:
    """

    idversion: VersionType = field(
        metadata={
            "name": "IDVersion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    idfactura: IdfacturaExpedidaType = field(
        metadata={
            "name": "IDFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    ref_externa: None | str = field(
        default=None,
        metadata={
            "name": "RefExterna",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "max_length": 60,
        },
    )
    nombre_razon_emisor: str = field(
        metadata={
            "name": "NombreRazonEmisor",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 120,
        }
    )
    subsanacion: None | SubsanacionType = field(
        default=None,
        metadata={
            "name": "Subsanacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    rechazo_previo: None | RechazoPrevioType = field(
        default=None,
        metadata={
            "name": "RechazoPrevio",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    tipo_factura: ClaveTipoFacturaType = field(
        metadata={
            "name": "TipoFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    tipo_rectificativa: None | ClaveTipoRectificativaType = field(
        default=None,
        metadata={
            "name": "TipoRectificativa",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    facturas_rectificadas: None | RegistroFacturacionAltaType.FacturasRectificadas = (
        field(
            default=None,
            metadata={
                "name": "FacturasRectificadas",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            },
        )
    )
    facturas_sustituidas: None | RegistroFacturacionAltaType.FacturasSustituidas = (
        field(
            default=None,
            metadata={
                "name": "FacturasSustituidas",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            },
        )
    )
    importe_rectificacion: None | DesgloseRectificacionType = field(
        default=None,
        metadata={
            "name": "ImporteRectificacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    fecha_operacion: None | str = field(
        default=None,
        metadata={
            "name": "FechaOperacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "length": 10,
            "pattern": r"\d{2,2}-\d{2,2}-\d{4,4}",
        },
    )
    descripcion_operacion: str = field(
        metadata={
            "name": "DescripcionOperacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 500,
        }
    )
    factura_simplificada_art7273: None | SimplificadaCualificadaType = field(
        default=None,
        metadata={
            "name": "FacturaSimplificadaArt7273",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    factura_sin_identif_destinatario_art61d: None | CompletaSinDestinatarioType = field(
        default=None,
        metadata={
            "name": "FacturaSinIdentifDestinatarioArt61d",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    macrodato: None | MacrodatoType = field(
        default=None,
        metadata={
            "name": "Macrodato",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    emitida_por_tercero_odestinatario: None | TercerosOdestinatarioType = field(
        default=None,
        metadata={
            "name": "EmitidaPorTerceroODestinatario",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    tercero: None | PersonaFisicaJuridicaType = field(
        default=None,
        metadata={
            "name": "Tercero",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    destinatarios: None | RegistroFacturacionAltaType.Destinatarios = field(
        default=None,
        metadata={
            "name": "Destinatarios",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    cupon: None | CuponType = field(
        default=None,
        metadata={
            "name": "Cupon",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    desglose: DesgloseType = field(
        metadata={
            "name": "Desglose",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    cuota_total: str = field(
        metadata={
            "name": "CuotaTotal",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        }
    )
    importe_total: str = field(
        metadata={
            "name": "ImporteTotal",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "pattern": r"(\+|-)?\d{1,12}(\.\d{0,2})?",
        }
    )
    encadenamiento: RegistroFacturacionAltaType.Encadenamiento = field(
        metadata={
            "name": "Encadenamiento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    sistema_informatico: SistemaInformaticoType = field(
        metadata={
            "name": "SistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    fecha_hora_huso_gen_registro: XmlDateTime = field(
        metadata={
            "name": "FechaHoraHusoGenRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    num_registro_acuerdo_facturacion: None | str = field(
        default=None,
        metadata={
            "name": "NumRegistroAcuerdoFacturacion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "max_length": 15,
        },
    )
    id_acuerdo_sistema_informatico: None | str = field(
        default=None,
        metadata={
            "name": "IdAcuerdoSistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "max_length": 16,
        },
    )
    tipo_huella: TipoHuellaType = field(
        metadata={
            "name": "TipoHuella",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    huella: str = field(
        metadata={
            "name": "Huella",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 64,
        }
    )
    signature: None | Signature = field(
        default=None,
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
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
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
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
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
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
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
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
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            },
        )
        registro_anterior: None | EncadenamientoFacturaAnteriorType = field(
            default=None,
            metadata={
                "name": "RegistroAnterior",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            },
        )


@dataclass(kw_only=True)
class RegistroFacturacionAnulacionType:
    """
    Datos correspondientes al registro de facturacion de anulacion.
    """

    idversion: VersionType = field(
        metadata={
            "name": "IDVersion",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    idfactura: IdfacturaExpedidaBajaType = field(
        metadata={
            "name": "IDFactura",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    ref_externa: None | str = field(
        default=None,
        metadata={
            "name": "RefExterna",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "max_length": 60,
        },
    )
    sin_registro_previo: None | SinRegistroPrevioType = field(
        default=None,
        metadata={
            "name": "SinRegistroPrevio",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    rechazo_previo: None | RechazoPrevioAnulacionType = field(
        default=None,
        metadata={
            "name": "RechazoPrevio",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    generado_por: None | GeneradoPorType = field(
        default=None,
        metadata={
            "name": "GeneradoPor",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    generador: None | PersonaFisicaJuridicaType = field(
        default=None,
        metadata={
            "name": "Generador",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
        },
    )
    encadenamiento: RegistroFacturacionAnulacionType.Encadenamiento = field(
        metadata={
            "name": "Encadenamiento",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    sistema_informatico: SistemaInformaticoType = field(
        metadata={
            "name": "SistemaInformatico",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    fecha_hora_huso_gen_registro: XmlDateTime = field(
        metadata={
            "name": "FechaHoraHusoGenRegistro",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    tipo_huella: TipoHuellaType = field(
        metadata={
            "name": "TipoHuella",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
        }
    )
    huella: str = field(
        metadata={
            "name": "Huella",
            "type": "Element",
            "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            "required": True,
            "max_length": 64,
        }
    )
    signature: None | Signature = field(
        default=None,
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        },
    )

    @dataclass(kw_only=True)
    class Encadenamiento:
        primer_registro: None | PrimerRegistroCadenaType = field(
            default=None,
            metadata={
                "name": "PrimerRegistro",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            },
        )
        registro_anterior: None | EncadenamientoFacturaAnteriorType = field(
            default=None,
            metadata={
                "name": "RegistroAnterior",
                "type": "Element",
                "namespace": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd",
            },
        )


@dataclass(kw_only=True)
class RegistroAlta(RegistroFacturacionAltaType):
    class Meta:
        namespace = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"


@dataclass(kw_only=True)
class RegistroAnulacion(RegistroFacturacionAnulacionType):
    class Meta:
        namespace = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
