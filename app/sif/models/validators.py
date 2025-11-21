"""Business validators and helpers for SIF json models.

Contains functions used by model validators: date parsing, sum checks (importe_total),
and utility functions. Centralizing these helpers makes unit testing straightforward.
"""

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Iterable


def parse_dd_mm_yyyy(s: str) -> date:
    """Parse strings like '02-12-2024' into date objects.

    Verifactu API uses DD-MM-YYYY format. This helper will be used in field validators.
    """
    return datetime.strptime(s, "%d-%m-%Y").date()


def sum_lines_bases_quota_recargo(lines: Iterable[Any]) -> Decimal:
    """Return sum of (base_imponible + cuota_repercutida + cuota_recargo_equivalencia)

    for an iterable of line objects/dicts. Uses Decimal.
    """
    total = Decimal("0.00")
    for ln in lines:
        b = Decimal(str(ln.base_imponible))
        q = Decimal("0.00")
        rc = Decimal("0.00")
        if getattr(ln, "cuota_repercutida", None) is not None:
            q = Decimal(str(ln.cuota_repercutida))
        if getattr(ln, "cuota_recargo_equivalencia", None) is not None:
            rc = Decimal(str(ln.cuota_recargo_equivalencia))
        total += b + q + rc
    # normalise to 2 decimal places
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def importe_matches_total(
    importe_reported: Any,  # Can accept int, float, or string convertible to Decimal
    lines: Iterable[Any],  # Expects an iterable of line objects/dicts
    allowed_margin: Decimal = Decimal("10.00"),
) -> Any:
    """Compare reported importe_total with computed sum of lines, accepting +/-

    allowed_margin. Returns True when acceptable, False otherwise.
    Note: for certain 'clave_regimen' values the check is skipped — callers must check
    that context.
    """
    reported = Decimal(str(importe_reported)).quantize(Decimal("0.01"))
    computed = sum_lines_bases_quota_recargo(lines)
    diff = (reported - computed).copy_abs()
    return diff <= allowed_margin
