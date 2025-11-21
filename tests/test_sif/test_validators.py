from decimal import Decimal

from app.sif.models.lineas import LineaFactura
from app.sif.models.validators import (
    importe_matches_total,
    sum_lines_bases_quota_recargo,
)


def test_sum_lines() -> None:
    lines = [
        LineaFactura(
            base_imponible=Decimal("100.00"),
            tipo_impositivo=Decimal("21.00"),  # <-- Añadido
            cuota_repercutida=Decimal("21.00"),
            tipo_recargo_equivalencia=None,  # <-- Añadido
            cuota_recargo_equivalencia=None,  # <-- Añadido
            operacion_exenta=None,  # <-- Añadido
        ),
        LineaFactura(
            base_imponible=Decimal("50.00"),
            tipo_impositivo=None,  # <-- Añadido
            cuota_repercutida=None,  # <-- Añadido
            tipo_recargo_equivalencia=None,  # <-- Añadido
            cuota_recargo_equivalencia=Decimal("0.00"),
            operacion_exenta=None,  # <-- Añadido
        ),
    ]
    total = sum_lines_bases_quota_recargo(lines)
    assert total == Decimal("171.00")  # 100 + 21 + 50 + 0 = 171


def test_importe_matches_total_true() -> None:
    lines = [
        LineaFactura(
            base_imponible=Decimal("100.00"),
            tipo_impositivo=Decimal("21.00"),  # <-- Añadido
            cuota_repercutida=Decimal("21.00"),
            tipo_recargo_equivalencia=None,  # <-- Añadido
            cuota_recargo_equivalencia=None,  # <-- Añadido
            operacion_exenta=None,  # <-- Añadido
        )
    ]
    assert importe_matches_total(Decimal("121.00"), lines)
