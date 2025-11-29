from typing import Any, Protocol

from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from app.infrastructure.aeat.xml.schema_validator import validate_suministro_lr


# TODO: definir más concretamente los Any cuando la implementación esté más avanzada
class XsdataSerializerProto(Protocol):
    def render(self, obj: Any) -> str:
        raise NotImplementedError


class AeatXmlSerializer:
    serializer: XsdataSerializerProto

    def __init__(self, schema_path: str | None = None):
        self.serializer = XmlSerializer(
            config=SerializerConfig(
                pretty_print=True,
                xml_declaration=True,
                encoding="UTF-8",
            )
        )

    def to_xml(self, obj: Any) -> str:
        """Serializa una clase xsdata a XML string."""
        xml = self.serializer.render(obj)
        return xml

    def to_valid_xml(self, obj: Any) -> str:
        """Genera XML y valida contra XSD."""
        xml = self.to_xml(obj)

        validate_suministro_lr(xml)

        return xml


# Instancia por defecto para importar directamente
default_serializer = AeatXmlSerializer()
