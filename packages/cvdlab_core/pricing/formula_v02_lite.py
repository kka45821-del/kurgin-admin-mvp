from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_CEILING
from typing import Any

FORMULA_VERSION = "pricing_formula_v0_2_lite"

@dataclass(frozen=True)
class PricingResult:
    formula_version: str
    calculated_specialist_purchase_price_rub: int
    calculated_specialist_client_display_price_rub: int
    calculated_public_price_rub: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def _d(value: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value is not None else default).replace(',', '.'))
    except Exception:
        return Decimal(default)

def ceil_to_1000(value: Any) -> int:
    amount = _d(value)
    if amount <= 0:
        return 0
    return int((amount / Decimal(1000)).to_integral_value(rounding=ROUND_CEILING) * Decimal(1000))

def calculate_pricing_v02_lite(
    *,
    base_price_rub_per_ct: Any,
    carat: Any,
    score_coefficient: Any = 1,
    kurgin_margin_percent: Any = 6,
    specialist_margin_percent: Any = 8,
    public_extra_percent: Any = 2,
) -> PricingResult:
    base = _d(base_price_rub_per_ct)
    ct = _d(carat)
    coeff = _d(score_coefficient, "1")
    kurgin = _d(kurgin_margin_percent) / Decimal(100)
    specialist = _d(specialist_margin_percent) / Decimal(100)
    public_extra = _d(public_extra_percent) / Decimal(100)
    purchase = ceil_to_1000(base * ct * coeff * (Decimal(1) + kurgin))
    client_display = ceil_to_1000(Decimal(purchase) * (Decimal(1) + specialist))
    public = ceil_to_1000(Decimal(client_display) * (Decimal(1) + public_extra))
    errors = []
    if not purchase < client_display < public:
        errors.append("price_hierarchy_invalid")
    return PricingResult(FORMULA_VERSION, purchase, client_display, public, tuple(), tuple(errors))
