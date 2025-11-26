# app/aeat/xml/builder.py
import logging
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List

from app.aeat.models import RegistroFacturaType
from app.aeat.models.root_suministro_lr import RegFactuSistemaFacturacionRoot
from app.aeat.models.suministro_informacion import (
    CabeceraType,
    CalificacionOperacionType,
    ClaveTipoFacturaType,
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
from app.models import InstalacionSIF
from app.sif.models.factura_create import (
    FacturasRectificadasInput,
    FacturasSustituidasInput,
    IdFacturaArInput,
    ImporteRectificativaInput,
)
from app.sif.models.ids import IdOtro
from app.sif.models.lineas import LineaFactura

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
    registro_facturacion_id: uuid.UUID,
    instalacion_sif: InstalacionSIF,
    nif_emisor: str,
    nombre_emisor: str,
    serie: str,
    numero: str,
    fecha_expedicion: date,
    fecha_operacion: date | None,
    fecha_hora_huso_: datetime,
    destinatario_nif: str | None,
    destinatario_nombre: str | None,
    id_otro: IdOtro | None,
    tipo_factura: ClaveTipoFacturaType,
    tipo_rectificativa: str | None,
    importe_rectificativa: ImporteRectificativaInput | None,
    facturas_rectificadas: FacturasRectificadasInput | None,
    facturas_sustituidas: FacturasSustituidasInput | None,
    operacion: str,
    descripcion: str | None,
    importe_total: Decimal,
    cuota_total: Decimal,
    huella: str,
    anterior_huella: str | None,
    anterior_emisor_nif: str | None,
    anterior_serie: str | None,
    anterior_numero: str | None,
    anterior_fecha_expedicion: date | None,
    lineas: List[LineaFactura],
) -> RegFactuSistemaFacturacionRoot:
    """Crea el objeto raíz RegFactuSistemaFacturacionRoot con RegistroFactura"""
    obligado = instalacion_sif.obligado
    cabecera = CabeceraType(
        obligado_emision=PersonaFisicaJuridicaEstype(
            nombre_razon=nombre_emisor,
            nif=nif_emisor,
        ),
        representante=None,
        remision_voluntaria=None,
        remision_requerimiento=None,
    )
    # Distinguimos alta (RegistroAlta) o anulacion (RegistroAnulacion)
    registro_obj = RegistroFacturaType()
    try:
        fecha_expedicion_str = fecha_expedicion.strftime("%d-%m-%Y")

        # Construir RegistroAlta (xsdata class RegistroAlta)
        ra = RegistroAlta()
        ra.idversion = VersionType.VALUE_1_0
        ra.idfactura = IdfacturaExpedidaType(
            idemisor_factura=nif_emisor,
            num_serie_factura=serie + numero,
            fecha_expedicion_factura=fecha_expedicion_str,
        )
        ra.ref_externa = str(registro_facturacion_id)
        ra.nombre_razon_emisor = nombre_emisor
        ra.subsanacion = SubsanacionType.N
        ra.rechazo_previo = RechazoPrevioType.N
        ra.tipo_factura = tipo_factura
        if tipo_rectificativa and importe_rectificativa:
            ra.tipo_rectificativa = ClaveTipoRectificativaType(tipo_rectificativa)
            ra.importe_rectificacion = DesgloseRectificacionType(
                base_rectificada=str(importe_rectificativa.base_rectificada),
                cuota_rectificada=str(importe_rectificativa.cuota_rectificada),
                cuota_recargo_rectificado=(
                    str(importe_rectificativa.cuota_recargo_rectificado)
                    if importe_rectificativa.cuota_recargo_rectificado is not None
                    else None
                ),
            )
        if facturas_rectificadas:
            ra.facturas_rectificadas = RegistroFacturacionAltaType.FacturasRectificadas(
                idfactura_rectificada=[
                    _build_idfactura_type(fr, nif_emisor)
                    for fr in facturas_rectificadas.facturas
                ]
            )
        if facturas_sustituidas:
            ra.facturas_sustituidas = RegistroFacturacionAltaType.FacturasSustituidas(
                idfactura_sustituida=[
                    _build_idfactura_type(fs, nif_emisor)
                    for fs in facturas_sustituidas.facturas
                ]
            )
        ra.fecha_operacion = (
            fecha_operacion.strftime("%d-%m-%Y")
            if fecha_operacion
            else fecha_expedicion_str
        )
        ra.descripcion_operacion = descripcion or ""
        # ra.factura_simplificada_art7273 =
        # ra.factura_sin_identif_destinatario_art61d =
        # ra.macrodato =
        # ra.emitida_por_tercero_odestinatario =
        # ra.tercero =
        id_otro_object = None
        if id_otro:
            id_otro_object = IdotroType(
                id=id_otro.id,
                idtype=id_otro.id_type,
                codigo_pais=id_otro.codigo_pais,
            )
        destinatarios: list[PersonaFisicaJuridicaType] = []
        destinatarios.append(
            PersonaFisicaJuridicaType(
                nombre_razon=destinatario_nombre or "",
                nif=destinatario_nif or "",
                idotro=id_otro_object,
            )
        )
        ra.destinatarios = RegistroFacturacionAltaType.Destinatarios(destinatarios)

        # ra.cupon =

        detalle_desglose: list[DetalleType] = []
        for ln in lineas:
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

        ra.cuota_total = str(cuota_total)
        ra.importe_total = str(importe_total)

        if (
            anterior_huella
            and anterior_emisor_nif
            and anterior_serie
            and anterior_numero
            and anterior_fecha_expedicion
        ):
            encadenamiento = RegistroFacturacionAltaType.Encadenamiento(
                registro_anterior=EncadenamientoFacturaAnteriorType(
                    idemisor_factura=anterior_emisor_nif,
                    huella=anterior_huella,
                    num_serie_factura=anterior_serie + anterior_numero,
                    fecha_expedicion_factura=anterior_fecha_expedicion.strftime(
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
        ra.fecha_hora_huso_gen_registro = XmlDateTime.from_datetime(fecha_hora_huso_)
        # ra.num_registro_acuerdo_facturacion =
        # ra.id_acuerdo_sistema_informatico =
        ra.tipo_huella = TipoHuellaType.VALUE_01
        ra.huella = huella
        # ra.signature =

    except Exception as e:
        logger.error(f"Error building factura: {e}")
        raise

    registro_obj.registro_alta = ra

    # else:
    #     # si en el futuro soportas anulaciones
    #     registro_obj.registro_anulacion = (
    #         RegistroAnulacion()
    #     )  # necesitarás rellenar campos

    # Empaquetar wrapper raíz
    root = RegFactuSistemaFacturacionRoot(
        cabecera=cabecera, registro_factura=[registro_obj]
    )

    return root
