from datetime import date
from decimal import Decimal

# Asegúrate de importar tus clases correctamente
from app.infrastructure.aeat.models.suministro_informacion import (
    ClaveTipoFacturaType,
    OperacionExentaType,
)
from app.sif.models.factura_create import FacturaInput

# importacion para IdOtroTercero
# from app.sif.models.especiales import IdOtroTercero


def test_ejemplo_simplificada_f2() -> None:
    """Test para factura simplificada (F2) sin datos del destinatario."""
    data = {
        "serie": "Ejemplos",
        "numero": "1",
        "fecha_expedicion": "24-02-2025",
        "tipo_factura": "F2",
        "descripcion": "Factura simplificada",
        "lineas": [
            {
                "base_imponible": "200",
                "tipo_impositivo": "21",
                "cuota_repercutida": "42",
            },
            {
                "base_imponible": "100",
                "tipo_impositivo": "10",
                "cuota_repercutida": "10",
            },
        ],
        "importe_total": "352",
    }
    f = FacturaInput.model_validate(data)
    assert f.fecha_expedicion == date(2025, 2, 24)
    assert f.nif is None  # Una F2 estándar no tiene NIF de cliente


def test_ejemplo_normal_f1() -> None:
    """Test para factura normal (F1) con NIF del destinatario."""
    data = {
        "serie": "Ejemplos",
        "numero": "1",
        "fecha_expedicion": "24-02-2025",
        "tipo_factura": "F1",
        "descripcion": "Factura normal",
        "nif": "A15022510",
        "nombre": "Nombre cliente",
        "lineas": [
            {
                "base_imponible": "200",
                "tipo_impositivo": "21",
                "cuota_repercutida": "42",
            }
        ],
        "importe_total": "242",
    }
    f = FacturaInput.model_validate(data)
    assert f.nif == "A15022510"


def test_ejemplo_con_varios_ivas() -> None:
    """Test para factura con múltiples tipos de IVA en las líneas."""
    data = {
        "serie": "Ejemplos",
        "numero": "1",
        "fecha_expedicion": "24-02-2025",
        "tipo_factura": "F1",
        "descripcion": "Factura con multiples IVAs",
        "nif": "A15022510",
        "nombre": "Nombre cliente",
        "lineas": [
            {
                "base_imponible": "200",
                "tipo_impositivo": "21",
                "cuota_repercutida": "42",
            },
            {
                "base_imponible": "100",
                "tipo_impositivo": "10",
                "cuota_repercutida": "10",
            },
        ],
        "importe_total": "352",
    }
    f = FacturaInput.model_validate(data)
    assert len(f.lineas) == 2
    assert f.importe_total == Decimal("352")


def test_ejemplo_a_ciudadano_extranjero() -> None:
    """Test para factura a cliente extranjero usando ID y pasaporte."""
    data = {
        "serie": "Ejemplos",
        "numero": "1",
        "fecha_expedicion": "24-02-2025",
        "tipo_factura": "F1",
        "descripcion": "Factura normal pasaporte",
        "id_otro": {"codigo_pais": "DE", "id_type": "03", "id": "F8624KW3J6"},
        "nombre": "Nombre cliente",
        "lineas": [
            {
                "base_imponible": "200",
                "tipo_impositivo": "21",
                "cuota_repercutida": "42",
            }
        ],
        "importe_total": "242",
    }
    # Nota: FacturaInput debe tener un mapeo de 'id_otro' a 'especial.id_otro_tercero'
    f = FacturaInput.model_validate(data)
    assert f.nif is None


def test_ejemplo_a_empresa_intracomunitaria() -> None:
    """Test para operación intracomunitaria (exenta E5) usando VAT ID."""
    data = {
        "serie": "Ejemplos",
        "numero": "1",
        "fecha_expedicion": "24-02-2025",
        "tipo_factura": "F1",
        "descripcion": "Factura a empresa VIES",
        "id_otro": {"codigo_pais": "BE", "id_type": "02", "id": "BE0404621642"},
        "nombre": "Nombre cliente",
        "lineas": [{"base_imponible": "200", "operacion_exenta": "E5"}],
        "importe_total": "200",
    }
    f = FacturaInput.model_validate(data)
    assert f.nif is None


def test_ejemplo_exenta_de_iva() -> None:
    """Test para operación exenta (E1) por normativa interna (ej. Art 20 LIVA)."""
    data = {
        "serie": "Ejemplos",
        "numero": "1",
        "fecha_expedicion": "24-02-2025",
        "tipo_factura": "F1",
        "descripcion": "Operación exenta",
        "nif": "A15022510",
        "nombre": "Nombre cliente",
        "lineas": [{"base_imponible": "200", "operacion_exenta": "E1"}],
        "importe_total": "200",
    }
    f = FacturaInput.model_validate(data)
    assert f.lineas[0].operacion_exenta == OperacionExentaType.E1


# NOTA: Los siguientes tests requieren que tus modelos FacturaInput y LineaFactura
# soporten los campos 'impuesto' y 'calificacion_operacion', que no estaban en tu
# definición de clase LineaFactura original. Si fallan, debes añadir esos campos
# a tu clase LineaFactura como Optional[str].


def test_ejemplo_con_igic() -> None:
    """Test para operación con IGIC (Canarias). Requiere campo 'impuesto'."""
    data = {
        "serie": "Ejemplos",
        "numero": "1",
        "fecha_expedicion": "24-02-2025",
        "tipo_factura": "F1",
        "descripcion": "Operacion con IGIC",
        "nif": "A15022510",
        "nombre": "Nombre cliente",
        "lineas": [
            {
                "impuesto": "03",
                "base_imponible": "200",
                "tipo_impositivo": "7",
                "cuota_repercutida": "14",
            }
        ],
        "importe_total": "214",
    }
    f = FacturaInput.model_validate(data)
    assert f.importe_total == Decimal("214")


def test_ejemplo_operacion_no_sujeta() -> None:
    """Test para operación no sujeta a IVA/IGIC/IPSI.

    Requiere campo 'calificacion_operacion'.
    """
    data = {
        "serie": "Ejemplos",
        "numero": "1",
        "fecha_expedicion": "24-02-2025",
        "tipo_factura": "F1",
        "descripcion": "Operación no sujeta",
        "nif": "A15022510",
        "nombre": "Nombre cliente",
        "lineas": [{"base_imponible": "200", "calificacion_operacion": "N1"}],
        "importe_total": "200",
    }
    f = FacturaInput.model_validate(data)
    assert f.importe_total == Decimal("200")


def test_ejemplo_con_ipsi() -> None:
    """Test para operación con IPSI (Ceuta/Melilla). Requiere campo 'impuesto'."""
    data = {
        "serie": "Ejemplos",
        "numero": "1",
        "fecha_expedicion": "24-02-2025",
        "tipo_factura": "F1",
        "descripcion": "Operacion con IPSI",
        "nif": "A15022510",
        "nombre": "Nombre cliente",
        "lineas": [
            {
                "impuesto": "02",
                "base_imponible": "200",
                "tipo_impositivo": "4",
                "cuota_repercutida": "8",
            }
        ],
        "importe_total": "208",
    }
    f = FacturaInput.model_validate(data)
    assert f.importe_total == Decimal("208")


def test_ejemplo_con_recargo_de_equivalencia() -> None:
    """Test para factura con Recargo de Equivalencia (RE)."""
    data = {
        "serie": "RECARGO",
        "numero": "1",
        "fecha_expedicion": "23-04-2025",
        "tipo_factura": "F1",
        "descripcion": "Descripcion de la operacion",
        "nif": "A15022510",
        "nombre": "Nombre cliente",
        "lineas": [
            {
                "base_imponible": "200",
                "tipo_impositivo": "21",
                "cuota_repercutida": "42",
                "clave_regimen": "18",
                "tipo_recargo_equivalencia": "5.2",
                "cuota_recargo_equivalencia": "10.4",
            }
        ],
        "importe_total": "252.4",
    }
    f = FacturaInput.model_validate(data)
    assert f.lineas[0].cuota_recargo_equivalencia == Decimal("10.4")


def test_ejemplo_factura_abono_f1() -> None:
    """Test para factura de abono/rectificativa por diferencias (signo negativo)."""
    data = {
        "serie": "Ejemplos",
        "numero": "1",
        "fecha_expedicion": "24-02-2025",
        "tipo_factura": "F1",
        "descripcion": "Factura de abono",
        "nif": "A15022510",
        "nombre": "Nombre cliente",
        "lineas": [
            {
                "base_imponible": "-200",
                "tipo_impositivo": "21",
                "cuota_repercutida": "-42",
            }
        ],
        "importe_total": "-242",
    }
    f = FacturaInput.model_validate(data)
    assert f.importe_total < Decimal("0")


def test_ejemplo_factura_abono_f2() -> None:
    """Test para factura simplificada de abono (F2)."""
    data = {
        "serie": "SIMPLE",
        "numero": "2",
        "fecha_expedicion": "11-03-2025",
        "tipo_factura": "F2",
        "descripcion": "Factura de abono",
        "lineas": [
            {
                "base_imponible": "-200",
                "tipo_impositivo": "21",
                "cuota_repercutida": "-42",
            }
        ],
        "importe_total": "-242",
    }
    f = FacturaInput.model_validate(data)
    assert f.importe_total < Decimal("0")


def test_ejemplo_rectificativa_r1() -> None:
    """Test para factura rectificativa R1 (sustitución en dos pasos)."""
    data = {
        "serie": "RECTIFICATIVA",
        "numero": "1",
        "fecha_expedicion": "10-04-2025",
        "fecha_operacion": "01-04-2025",
        "tipo_factura": "R1",
        "tipo_rectificativa": "S",
        "descripcion": "Rectificacion por sustitucion en dos pasos",
        "nif": "A15022510",
        "nombre": "Nombre cliente",
        "lineas": [
            {
                "base_imponible": "800",
                "tipo_impositivo": "21",
                "cuota_repercutida": "168",
            }
        ],
        "importe_total": "968",
        "importe_rectificativa": {"base_rectificada": "0", "cuota_rectificada": "0"},
        "facturas_rectificadas": [
            {"serie": "A", "numero": "1", "fecha_expedicion": "07-04-2025"}
        ],
    }
    f = FacturaInput.model_validate(data)
    assert f.tipo_factura == ClaveTipoFacturaType.R1
    assert f.fecha_expedicion == date(2025, 4, 10)


def test_ejemplo_rectificativa_r4() -> None:
    """Test para factura rectificativa R4

    (diferencias, aunque el ejemplo usa sustitución).
    """
    data = {
        "serie": "RECTIFICATIVA",
        "numero": "3",
        "fecha_expedicion": "10-04-2025",
        "fecha_operacion": "01-04-2025",
        "tipo_factura": "R4",
        "tipo_rectificativa": "S",
        "descripcion": "Rectificacion por sustitucion en dos pasos",
        "nif": "A15022510",
        "nombre": "Nombre cliente",
        "lineas": [
            {"base_imponible": "1000", "tipo_impositivo": "0", "cuota_repercutida": "0"}
        ],
        "importe_total": "1000",
        "importe_rectificativa": {"base_rectificada": "0", "cuota_rectificada": "0"},
        "facturas_rectificadas": [
            {"serie": "A", "numero": "1", "fecha_expedicion": "07-04-2025"}
        ],
    }
    f = FacturaInput.model_validate(data)
    assert f.tipo_factura == ClaveTipoFacturaType.R4
