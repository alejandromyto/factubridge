# app/domain/dto/RegistroAltaDTO.py

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from app.domain.models.models import InstalacionSIF, RegistroFacturacion
from app.infrastructure.aeat.models.suministro_informacion import ClaveTipoFacturaType
from app.sif.models.factura_create import (
    FacturasRectificadasInput,
    FacturasSustituidasInput,
    ImporteRectificativaInput,
)
from app.sif.models.ids import IdOtro
from app.sif.models.lineas import LineaFactura


@dataclass
class RegistroAltaDTO:
    """DTO independiente del ORM, listo para usarse en XML builder."""

    registro_id: uuid.UUID
    instalacion_sif: InstalacionSIF

    # Emisor
    emisor_nif: str
    emisor_nombre: str

    # Datos de la factura
    serie: str
    numero: str
    fecha_expedicion: date
    fecha_operacion: Optional[date]
    fecha_hora_huso: datetime

    # Destinatario
    destinatario_nif: Optional[str]
    destinatario_nombre: Optional[str]
    id_otro: Optional[IdOtro]

    # Tipos de factura
    tipo_factura: ClaveTipoFacturaType
    tipo_rectificativa: Optional[str]
    importe_rectificativa: Optional[ImporteRectificativaInput]
    facturas_rectificadas: Optional[FacturasRectificadasInput]
    facturas_sustituidas: Optional[FacturasSustituidasInput]

    # Contenido económico
    operacion: str
    descripcion: str
    importe_total: Decimal
    cuota_total: Decimal

    # Huellas
    huella: str
    anterior_huella: Optional[str]
    anterior_emisor_nif: Optional[str]
    anterior_serie: Optional[str]
    anterior_numero: Optional[str]
    anterior_fecha_expedicion: Optional[date]

    # Líneas
    lineas: List[LineaFactura]

    # ------------------------------------------------------------------
    # FACTORY METHOD: Construye DTO desde RegistroFacturacion ORM
    # ------------------------------------------------------------------
    @staticmethod
    def to_dto_from_orm(r: RegistroFacturacion) -> "RegistroAltaDTO":
        """
        Crea DTO desde RegistroFacturacion.

        DTO = Objeto de Transferencia de Datos para no pasar chorrocientos argumentos.
        """
        # ✅ Revalida SOLO los objetos compuestos
        factura_data = r.factura_json

        # Parsea lineas con seguridad de tipos List[LineaFactura]
        lineas: list[LineaFactura] = [
            LineaFactura(**linea) for linea in factura_data.get("lineas", [])
        ]
        id_otro_data = factura_data.get("id_otro")
        id_otro: IdOtro | None = IdOtro(**id_otro_data) if id_otro_data else None
        importe_rect_data = factura_data.get("importe_rectificativa")
        importe_rectificativa = None
        if importe_rect_data:
            importe_rectificativa = ImporteRectificativaInput(**importe_rect_data)
        sustituidas_data = factura_data.get("facturas_sustituidas")
        facturas_sustituidas = None
        if sustituidas_data:
            facturas_sustituidas = FacturasSustituidasInput(**sustituidas_data)
        rectificadas_data = factura_data.get("facturas_rectificadas")
        facturas_rectificadas = None
        if rectificadas_data:
            facturas_rectificadas = FacturasRectificadasInput(**rectificadas_data)
        instalacion_sif = r.instalacion_sif
        obligado = instalacion_sif.obligado
        return RegistroAltaDTO(
            registro_id=r.id,
            instalacion_sif=instalacion_sif,
            emisor_nif=obligado.nif,
            emisor_nombre=obligado.nombre_razon_social,
            serie=r.serie,
            numero=r.numero,
            fecha_expedicion=r.fecha_expedicion,
            fecha_operacion=r.fecha_operacion,
            fecha_hora_huso=r.created_at,
            destinatario_nif=r.destinatario_nif,
            destinatario_nombre=r.destinatario_nombre,
            id_otro=id_otro,
            tipo_factura=ClaveTipoFacturaType(r.tipo_factura),
            tipo_rectificativa=r.tipo_rectificativa,
            importe_rectificativa=importe_rectificativa,
            facturas_rectificadas=facturas_rectificadas,
            facturas_sustituidas=facturas_sustituidas,
            operacion=r.operacion,
            descripcion=r.descripcion if r.descripcion else "Factura Normal",
            importe_total=r.importe_total,
            cuota_total=r.cuota_total,
            huella=r.huella,
            anterior_huella=r.anterior_huella,
            anterior_emisor_nif=r.anterior_emisor_nif,
            anterior_serie=r.anterior_serie,
            anterior_numero=r.anterior_numero,
            anterior_fecha_expedicion=r.anterior_fecha_expedicion,
            lineas=lineas,
        )
