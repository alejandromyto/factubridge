import os
import re

# Configuración
MODELS_DIR = "app/infrastructure/aeat/models"

# 1. Lista de enums a convetir en str,Enum
TARGET_ENUMS = {
    "EstadoRegistroType",
    "IndicadorPaginacionType",
    "ResultadoConsultaType",
    "CalificacionOperacionType",
    "ClaveTipoFacturaType",
    "ClaveTipoRectificativaType",
    "CompletaSinDestinatarioType",
    "CuponType",
    "FinRequerimientoType",
    "GeneradoPorType",
    "IdOperacionesTrascendenciaTributariaType",
    "ImpuestoType",
    "IncidenciaType",
    "IndicadorRepresentanteType",
    "MacrodatoType",
    "MostrarNombreRazonEmisorType",
    "MostrarSistemaInformaticoType",
    "OperacionExentaType",
    "PersonaFisicaJuridicaIdtypeType",
    "PrimerRegistroCadenaType",
    "RechazoPrevioAnulacionType",
    "RechazoPrevioType",
    "SiNoType",
    "SimplificadaCualificadaType",
    "SinRegistroPrevioType",
    "SubsanacionType",
    "TercerosOdestinatarioType",
    "TipoHuellaType",
    "TipoOperacionType",
    "TipoPeriodoType",
    "VersionType",
    "EstadoEnvioType",
    "TipoAnomaliaType",
    "TipoEventoType",
    "CountryType2",
    "EstadoRegistroSftype",
}

# 2. Contenido de fichero manual
ROOT_FILE_NAME = "root_suministro_lr.py"
ROOT_FILE_CONTENT = """from dataclasses import dataclass, field
from typing import List, Optional
from .suministro_lr import CabeceraType, RegistroFacturaType

__NAMESPACE__ = (
    "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/"
    "aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd"
)

@dataclass
class RegFactuSistemaFacturacionRoot:
    \"\"\"
    Root element para envío LR (Generado automáticamente por script post-procesado).

    Este wrapper es necesario porque el XSD define el elemento root como
    un element anónimo, no como un tipo global. xsdata NO lo genera
    automáticamente.
    \"\"\"

    cabecera: Optional[CabeceraType] = field(
        default=None,
        metadata={
            "name": "Cabecera",
            "type": "Element",
            "required": True,
        },
    )

    registro_factura: List[RegistroFacturaType] = field(
        default_factory=list,
        metadata={
            "name": "RegistroFactura",
            "type": "Element",
            "min_occurs": 1,
            "max_occurs": 1000,
        },
    )

    class Meta:
        name = "RegFactuSistemaFacturacion"
        namespace = __NAMESPACE__
"""


def create_root_file() -> None:
    """Crea el fichero root que xsdata no genera."""
    filepath = os.path.join(MODELS_DIR, ROOT_FILE_NAME)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(ROOT_FILE_CONTENT)
    print(f"✅ Fichero manual creado: {ROOT_FILE_NAME}")


def fix_enums() -> None:
    """Corrige la herencia de los enums."""
    count = 0
    for filename in os.listdir(MODELS_DIR):
        if not filename.endswith(".py"):
            continue

        filepath = os.path.join(MODELS_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        modified = False
        for enum_name in TARGET_ENUMS:
            pattern = rf"class {enum_name}\s*\(Enum\):"
            if re.search(pattern, content):
                new_def = f"class {enum_name}(str, Enum):"
                content = re.sub(pattern, new_def, content)
                modified = True
                print(f"🔧 Enum corregido: {enum_name} en {filename}")
                count += 1

        if modified:
            if "from enum import Enum" not in content:
                content = "from enum import Enum\n" + content
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
    print(f"🎉 Enums corregidos: {count}")


if __name__ == "__main__":
    if os.path.exists(MODELS_DIR):
        create_root_file()
        fix_enums()
    else:
        print(f"❌ Error: No existe el directorio {MODELS_DIR}")
