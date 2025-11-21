"""Tests para validación de NIF/CIF/NIE"""

import pytest

from app.core.validacion_nif import (
    detectar_tipo_documento,
    validar_cif,
    validar_documento_espanol,
    validar_nie,
    validar_nif_dni,
)


class TestNIF:
    """Tests para validación de NIF (DNI)"""

    def test_nif_valido(self) -> None:
        """Casos de NIF válidos"""
        assert validar_nif_dni("12345678Z")
        assert validar_nif_dni("00000000T")
        assert validar_nif_dni("99999999R")

    def test_nif_con_espacios(self) -> None:
        """NIF con espacios debe validarse"""
        assert validar_nif_dni("12345678 Z")
        assert validar_nif_dni(" 12345678Z ")

    def test_nif_minusculas(self) -> None:
        """NIF en minúsculas debe validarse"""
        assert validar_nif_dni("12345678z")

    def test_nif_letra_incorrecta(self) -> None:
        """NIF con letra incorrecta debe fallar"""
        assert not validar_nif_dni("12345678A")  # Debería ser Z

    def test_nif_formato_incorrecto(self) -> None:
        """NIF con formato incorrecto debe fallar"""
        assert not validar_nif_dni("1234567Z")  # Solo 7 dígitos
        assert not validar_nif_dni("123456789Z")  # 9 dígitos
        assert not validar_nif_dni("ABCDEFGHZ")  # No numérico


class TestNIE:
    """Tests para validación de NIE"""

    def test_nie_valido_x(self) -> None:
        """NIE válidos con X"""
        assert validar_nie("X1234567L")

    def test_nie_valido_y(self) -> None:
        """NIE válidos con Y"""
        assert validar_nie("Y1234567X")

    def test_nie_valido_z(self) -> None:
        """NIE válidos con Z"""
        assert validar_nie("Z1234567R")

    def test_nie_letra_incorrecta(self) -> None:
        """NIE con letra incorrecta debe fallar"""
        assert not validar_nie("X1234567Z")

    def test_nie_formato_incorrecto(self) -> None:
        """NIE con formato incorrecto debe fallar"""
        assert not validar_nie("A1234567L")  # Debe empezar con X/Y/Z
        assert not validar_nie("X123456L")  # Solo 6 dígitos


class TestCIF:
    """Tests para validación de CIF"""

    def test_cif_valido_letra(self) -> None:
        """CIF válidos con letra de control"""
        assert validar_cif("A12345674")  # CIF de prueba

    def test_cif_valido_digito(self) -> None:
        """CIF válidos con dígito de control"""
        assert validar_cif("B12345674")

    def test_cif_digito_no_valido(self) -> None:
        """CIF válidos con dígito de control"""
        assert not validar_cif("B12345678")

    def test_cif_organizacion_invalida(self) -> None:
        """CIF con letra de organización inválida debe fallar"""
        assert not validar_cif("I12345678")  # I no es válida
        assert not validar_cif("O12345678")  # O no es válida

    def test_cif_control_incorrecto(self) -> None:
        """CIF con control incorrecto debe fallar"""
        assert not validar_cif("A12345675")  # Control incorrecto


class TestDeteccionTipo:
    """Tests para detección automática de tipo"""

    def test_detectar_nif(self) -> None:
        """Debe detectar NIF correctamente"""
        assert detectar_tipo_documento("12345678Z") == "NIF"

    def test_detectar_nie(self) -> None:
        """Debe detectar NIE correctamente"""
        assert detectar_tipo_documento("X1234567L") == "NIE"

    def test_detectar_cif(self) -> None:
        """Debe detectar CIF correctamente"""
        assert detectar_tipo_documento("A12345674") == "CIF"

    def test_detectar_desconocido(self) -> None:
        """Debe detectar documentos inválidos"""
        assert detectar_tipo_documento("ABCDEFGH") == "DESCONOCIDO"


class TestValidacionGeneral:
    """Tests para validación general de documentos"""

    def test_validar_nif_completo(self) -> None:
        """Validación completa de NIF"""
        resultado = validar_documento_espanol("12345678Z")
        assert resultado["valido"]
        assert resultado["tipo"] == "NIF"
        assert resultado["documento"] == "12345678Z"

    def test_validar_nie_completo(self) -> None:
        """Validación completa de NIE"""
        resultado = validar_documento_espanol("X1234567L")
        assert resultado["valido"]
        assert resultado["tipo"] == "NIE"

    def test_validar_cif_completo(self) -> None:
        """Validación completa de CIF"""
        resultado = validar_documento_espanol("A12345674")
        assert resultado["valido"]
        assert resultado["tipo"] == "CIF"

    def test_validar_documento_invalido(self) -> None:
        """Documento inválido debe fallar"""
        resultado = validar_documento_espanol("INVALIDO")
        assert not resultado["valido"]
        assert resultado["tipo"] == "DESCONOCIDO"


# Casos reales para testing
CASOS_REALES_VALIDOS = [
    "12345678Z",  # NIF válido
    "X1234567L",  # NIE válido
    "A12345674",  # CIF válido
    "B75777847",  # CIF real ejemplo
]

CASOS_REALES_INVALIDOS = [
    "12345678A",  # NIF con letra incorrecta
    "X1234567Z",  # NIE con letra incorrecta
    "I12345678",  # CIF con organización inválida
    "123456789",  # Sin letra
    "ABCDEFGHI",  # No es documento
]


@pytest.mark.parametrize("documento", CASOS_REALES_VALIDOS)
def test_casos_validos(documento: str) -> None:
    """Test con casos válidos reales"""
    resultado = validar_documento_espanol(documento)
    assert resultado["valido"], f"Documento {documento} debería ser válido"


@pytest.mark.parametrize("documento", CASOS_REALES_INVALIDOS)
def test_casos_invalidos(documento: str) -> None:
    """Test con casos inválidos reales"""
    resultado = validar_documento_espanol(documento)
    assert not resultado["valido"], f"Documento {documento} debería ser inválido"
