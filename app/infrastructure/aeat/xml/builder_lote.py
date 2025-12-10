from typing import List

from app.domain.dto.registro_alta_dto import RegistroAltaDTO
from app.domain.models.models import RegistroFacturacion
from app.infrastructure.aeat.models.root_suministro_lr import (
    RegFactuSistemaFacturacionRoot,
)
from app.infrastructure.aeat.models.suministro_informacion import (
    CabeceraType,
    PersonaFisicaJuridicaEstype,
)
from app.infrastructure.aeat.models.suministro_lr import RegistroFacturaType
from app.infrastructure.aeat.xml.builder import build_registro_alta
from app.infrastructure.aeat.xml.serializer import default_serializer


def build_registro_factura(dto: RegistroAltaDTO) -> RegistroFacturaType:
    """
    Construye un RegistroFacturaType envolviendo un RegistroAlta.

    Args:
        dto: DTO con los datos del registro de alta.

    Returns:
        RegistroFacturaType con el RegistroAlta incluido.
    """
    registro_alta = build_registro_alta(dto)

    return RegistroFacturaType(registro_alta=registro_alta, registro_anulacion=None)


def build_xml_lote(
    registros: List[RegistroAltaDTO], emisor_nif: str, emisor_nombre: str
) -> str:
    """
    Construye un XML de lote único, incluyendo un RegistroAlta por cada registro.

    Args:
        registros: Lista de DTOs List[RegistroAltaDTO] a incluir en el lote.
    Returns:
        XML validado como string.
    """
    cabecera = CabeceraType(
        obligado_emision=PersonaFisicaJuridicaEstype(
            nombre_razon=emisor_nombre,
            nif=emisor_nif,
        ),
        representante=None,
        remision_voluntaria=None,
        remision_requerimiento=None,
    )
    # Construir lista de registros de facturación
    registro_factura: List[RegistroFacturaType] = [
        build_registro_factura(dto) for dto in registros
    ]
    # Empaquetar wrapper raíz
    root = RegFactuSistemaFacturacionRoot(
        cabecera=cabecera, registro_factura=registro_factura
    )
    # Serializar a string y valida
    xml_str = default_serializer.to_valid_xml(root)

    return xml_str


def construir_xml_lote_desde_entidades(
    registros: List[RegistroFacturacion], emisor_nif: str, emisor_nombre: str
) -> str:
    """
    Construye un XML de lote a partir de entidades del dominio.

    Args:
        registros: Lista RegistroFacturacion de la BD.
        emisor_nif: NIF del emisor.
        emisor_nombre: Nombre del emisor.

    Returns:
        XML serializado y validado como string.
    """
    # 1. Convertir entidades a DTOs
    dtos = [RegistroAltaDTO.to_dto_from_orm(registro) for registro in registros]

    # 2. Construir XML usando la función que ya tienes
    return build_xml_lote(dtos, emisor_nif, emisor_nombre)
