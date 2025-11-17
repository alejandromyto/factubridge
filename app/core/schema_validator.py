from pathlib import Path

import xmlschema

BASE_DIR = Path(__file__).resolve().parent.parent / "xsd"

# Cache de esquemas ya cargados
_schema_cache = {}


def load_schema(filename: str) -> xmlschema.XMLSchema:
    """Carga un esquema XSD desde /app/xsd con cache."""
    if filename not in _schema_cache:
        xsd_path = BASE_DIR / filename
        if not xsd_path.exists():
            raise FileNotFoundError(f"❌ XSD no encontrado: {xsd_path}")

        _schema_cache[filename] = xmlschema.XMLSchema(xsd_path)

    return _schema_cache[filename]


def validate_xml(xml_content: str, filename: str) -> None:
    """Valida XML frente a un esquema AEAT. Lanza ValueError si no cumple."""
    schema = load_schema(filename)

    try:
        schema.validate(xml_content)
    except xmlschema.XMLSchemaValidationError as exc:
        raise ValueError(
            f"❌ XML inválido según esquema '{filename}': {exc.reason}"
        ) from exc


# ======== SHORTCUTS PARA XSD ESPECÍFICOS ========


def validate_consulta_lr(xml: str) -> None:
    return validate_xml(xml, "ConsultaLR.xsd")


def validate_eventos_sif(xml: str) -> None:
    return validate_xml(xml, "EventosSIF.xsd")


def validate_respuesta_consulta_lr(xml: str) -> None:
    return validate_xml(xml, "RespuestaConsultaLR.xsd")


def validate_respuesta_suministro(xml: str) -> None:
    return validate_xml(xml, "RespuestaSuministro.xsd")


def validate_respuesta_val_registro_no_verifactu(xml: str) -> None:
    return validate_xml(xml, "RespuestaValRegistNoVeriFactu.xsd")


def validate_suministro_informacion(xml: str) -> None:
    return validate_xml(xml, "SuministroInformacion.xsd")


def validate_suministro_lr(xml: str) -> None:
    return validate_xml(xml, "SuministroLR.xsd")
