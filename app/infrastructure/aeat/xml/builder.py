# app/aeat/xml/builder.py
import logging
from datetime import date, datetime

from app.domain.dto.registro_alta_dto import RegistroAltaDTO
from app.domain.models.models import RegistroFacturacion
from app.infrastructure.aeat.models import RegistroFacturaType
from app.infrastructure.aeat.models.root_suministro_lr import (
    RegFactuSistemaFacturacionRoot,
)
from app.infrastructure.aeat.models.suministro_informacion import (
    CabeceraType,
    CalificacionOperacionType,
    ClaveTipoRectificativaType,
    DesgloseRectificacionType,
    DesgloseType,
    DetalleType,
    EncadenamientoFacturaAnteriorType,
    IdfacturaArtype,
    IdfacturaExpedidaType,
    IdOperacionesTrascendenciaTributariaType,
    IdotroType,
    OperacionExentaType,
    PersonaFisicaJuridicaEstype,
    PersonaFisicaJuridicaType,
    PrimerRegistroCadenaType,
    RechazoPrevioType,
    RegistroAlta,
    RegistroFacturacionAltaType,
    SiNoType,
    SistemaInformaticoType,
    SubsanacionType,
    TipoHuellaType,
    VersionType,
    XmlDateTime,
)
from app.sif.models.factura_create import (
    IdFacturaArInput,
)

logger = logging.getLogger(__name__)


# helper: parse dd-mm-YYYY -> datetime.date
def parse_date_ddmmyyyy(s: str) -> date:
    return datetime.strptime(s, "%d-%m-%Y").date()


def _build_idfactura_type(
    factura: IdFacturaArInput, nif_emisor_padre: str
) -> IdfacturaArtype:
    """Convierte un IdFacturaArInput a IdfacturaArtype xsdata."""
    return IdfacturaArtype(
        idemisor_factura=factura.nif_emisor or nif_emisor_padre,
        num_serie_factura=factura.serie + factura.numero,  # Ya validados por Pydantic
        fecha_expedicion_factura=factura.fecha_expedicion.strftime("%d-%m-%Y"),
    )


def build_registro_factura_from_json(
    r: RegistroFacturacion,
) -> RegFactuSistemaFacturacionRoot:
    """Crea el objeto raíz RegFactuSistemaFacturacionRoot con RegistroFactura"""
    instalacion_sif = r.instalacion_sif
    obligado = instalacion_sif.obligado
    cabecera = CabeceraType(
        obligado_emision=PersonaFisicaJuridicaEstype(
            nombre_razon=obligado.nombre_razon_social,
            nif=obligado.nif,
        ),
        representante=None,
        remision_voluntaria=None,
        remision_requerimiento=None,
    )
    # Distinguimos alta (RegistroAlta) o anulacion (RegistroAnulacion)
    registro_obj = RegistroFacturaType()
    try:
        ra = build_registro_alta(RegistroAltaDTO.to_dto_from_orm(r))
    except Exception as e:
        logger.error(f"Error building factura: {e}")
        raise

    registro_obj.registro_alta = ra

    #     # si en el futuro soportas anulaciones
    #     registro_obj.registro_anulacion = (
    #         RegistroAnulacion()
    #     )  # necesitarás rellenar campos

    # Empaquetar wrapper raíz
    root = RegFactuSistemaFacturacionRoot(
        cabecera=cabecera, registro_factura=[registro_obj]
    )
    return root


def build_registro_alta(dto: RegistroAltaDTO) -> RegistroAlta:
    """Crea el objeto RegistroAlta con RegistroAltaDTO."""
    fecha_expedicion_str = dto.fecha_expedicion.strftime("%d-%m-%Y")
    ra = RegistroAlta()
    ra.idversion = VersionType.VALUE_1_0
    ra.idfactura = IdfacturaExpedidaType(
        idemisor_factura=dto.emisor_nif,
        num_serie_factura=dto.serie + dto.numero,
        fecha_expedicion_factura=fecha_expedicion_str,
    )
    ra.ref_externa = str(dto.registro_id)
    ra.nombre_razon_emisor = dto.emisor_nombre
    ra.subsanacion = SubsanacionType.N
    ra.rechazo_previo = RechazoPrevioType.N
    ra.tipo_factura = dto.tipo_factura
    if dto.tipo_rectificativa and dto.importe_rectificativa:
        ra.tipo_rectificativa = ClaveTipoRectificativaType(dto.tipo_rectificativa)
        ra.importe_rectificacion = DesgloseRectificacionType(
            base_rectificada=str(dto.importe_rectificativa.base_rectificada),
            cuota_rectificada=str(dto.importe_rectificativa.cuota_rectificada),
            cuota_recargo_rectificado=(
                str(dto.importe_rectificativa.cuota_recargo_rectificado)
                if dto.importe_rectificativa.cuota_recargo_rectificado is not None
                else None
            ),
        )
    if dto.facturas_rectificadas:
        ra.facturas_rectificadas = RegistroFacturacionAltaType.FacturasRectificadas(
            idfactura_rectificada=[
                _build_idfactura_type(fr, dto.emisor_nif)
                for fr in dto.facturas_rectificadas.facturas
            ]
        )
    if dto.facturas_sustituidas:
        ra.facturas_sustituidas = RegistroFacturacionAltaType.FacturasSustituidas(
            idfactura_sustituida=[
                _build_idfactura_type(fs, dto.emisor_nif)
                for fs in dto.facturas_sustituidas.facturas
            ]
        )
    ra.fecha_operacion = (
        dto.fecha_operacion.strftime("%d-%m-%Y")
        if dto.fecha_operacion
        else fecha_expedicion_str
    )
    ra.descripcion_operacion = dto.descripcion or ""
    # ra.factura_simplificada_art7273 =
    # ra.factura_sin_identif_destinatario_art61d =
    # ra.macrodato =
    # ra.emitida_por_tercero_odestinatario =
    # ra.tercero =
    id_otro_object = None
    if dto.id_otro:
        id_otro_object = IdotroType(
            id=dto.id_otro.id,
            idtype=dto.id_otro.id_type,
            codigo_pais=dto.id_otro.codigo_pais,
        )
    destinatarios: list[PersonaFisicaJuridicaType] = []
    destinatarios.append(
        PersonaFisicaJuridicaType(
            nombre_razon=dto.destinatario_nombre or "",
            nif=dto.destinatario_nif or "",
            idotro=id_otro_object,
        )
    )
    ra.destinatarios = RegistroFacturacionAltaType.Destinatarios(destinatarios)

    # ra.cupon =

    detalle_desglose: list[DetalleType] = []
    for ln in dto.lineas:
        linea = DetalleType()
        linea.calificacion_operacion = CalificacionOperacionType.S1
        linea.base_imponible_oimporte_no_sujeto = str(ln.base_imponible)
        if ln.operacion_exenta is not None:
            linea.operacion_exenta = OperacionExentaType(ln.operacion_exenta)
        linea.clave_regimen = IdOperacionesTrascendenciaTributariaType.VALUE_01
        linea.tipo_impositivo = str(ln.tipo_impositivo or "0")
        linea.cuota_repercutida = str(ln.cuota_repercutida or "0")
        detalle_desglose.append(linea)
    ra.desglose = DesgloseType(detalle_desglose)

    ra.cuota_total = str(dto.cuota_total)
    ra.importe_total = str(dto.importe_total)

    if (
        dto.anterior_huella
        and dto.anterior_emisor_nif
        and dto.anterior_serie
        and dto.anterior_numero
        and dto.anterior_fecha_expedicion
    ):
        encadenamiento = RegistroFacturacionAltaType.Encadenamiento(
            registro_anterior=EncadenamientoFacturaAnteriorType(
                idemisor_factura=dto.anterior_emisor_nif,
                huella=dto.anterior_huella,
                num_serie_factura=dto.anterior_serie + dto.anterior_numero,
                fecha_expedicion_factura=dto.anterior_fecha_expedicion.strftime(
                    "%d-%m-%Y"
                ),
            )
        )
        ra.encadenamiento = encadenamiento
    else:
        encadenamiento = RegistroFacturacionAltaType.Encadenamiento(
            primer_registro=PrimerRegistroCadenaType.S
        )
    ra.encadenamiento = encadenamiento
    instalacion_sif = dto.instalacion_sif
    obligado = instalacion_sif.obligado
    ra.sistema_informatico = SistemaInformaticoType(
        nombre_razon=obligado.nombre_razon_social,
        nif=obligado.nif,
        idotro=None,  # o id_otro si aplica
        nombre_sistema_informatico=instalacion_sif.nombre_sistema_informatico,
        id_sistema_informatico=instalacion_sif.id_sistema_informatico,
        version=instalacion_sif.version_sistema_informatico,
        numero_instalacion=instalacion_sif.numero_instalacion,
        tipo_uso_posible_solo_verifactu=SiNoType.S,  # Si solo usas Verifactu
        tipo_uso_posible_multi_ot=SiNoType.S,  # Según tu caso
        indicador_multiples_ot=(
            SiNoType.S if instalacion_sif.indicador_multiples_ot else SiNoType.N
        ),
    )

    # Convertimos el objeto datetime de Python a XmlDateTime para satisfacer
    # el tipado estático. xsdata usará esto para generar el formato correcto.
    ra.fecha_hora_huso_gen_registro = XmlDateTime.from_datetime(dto.fecha_hora_huso)
    # ra.num_registro_acuerdo_facturacion =
    # ra.id_acuerdo_sistema_informatico =
    ra.tipo_huella = TipoHuellaType.VALUE_01
    ra.huella = dto.huella
    # ra.signature =
    return ra
