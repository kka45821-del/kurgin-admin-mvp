"""
KURGIN Pricing Formula v0.2-lite.

Pure deterministic formula module for the first controlled v0.2-lite pricing test.

This module intentionally contains:
- no Streamlit imports;
- no pandas UI;
- no file writes;
- no save_stones calls;
- no catalog publication;
- no price confirmation;
- no checkout logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from typing import Any


FORMULA_VERSION = "pricing_formula_v0_2_lite"
ROUNDING_UNIT_RUB = Decimal("1000")

STATUS_OK = "ok"
STATUS_BLOCKED = "blocked"
STATUS_NEEDS_REVIEW = "needs_review"

ERROR_BELOW_FX_PROTECTED_PURCHASE_COST = "below_fx_protected_purchase_cost"
ERROR_AFTER_TAX_PROFIT_NEGATIVE = "after_tax_profit_negative"
ERROR_PRICE_HIERARCHY_INVALID = "price_hierarchy_invalid"
ERROR_PENDING_INVOICE_SAME_SHIPMENT = "pending_invoice_same_shipment_blocked"
ERROR_INVALID_INPUT = "invalid_input"

WARNING_AFTER_TAX_PROFIT_BELOW_MINIMUM = "after_tax_profit_below_minimum"
WARNING_PRICE_TOO_CLOSE_TO_PURCHASE_COST = "price_too_close_to_purchase_cost"
WARNING_BATCH_EXPENSE_NOT_INCLUDED_IN_FINAL_PRICE = "batch_expense_not_included_in_final_price"


@dataclass(frozen=True)
class PurchaseInput:
    base_purchase_price_per_ct_supplier_currency: Any
    carat: Any
    invoice_currency: str
    fx_rate_rub_per_invoice_currency: Any
    kurgin_score_coefficient: Any = Decimal("1")
    purchase_status: str = "projected"
    fx_buffer_percent: Any = Decimal("0")
    actual_purchase_total_rub: Any | None = None


@dataclass(frozen=True)
class BatchInput:
    batch_fixed_expenses_rub: Any
    batch_total_supplier_currency: Any
    batch_expense_allocation_method: str = "value_share"


@dataclass(frozen=True)
class FormulaInput:
    customs_percent: Any
    freight_percent: Any = Decimal("0")
    unexpected_expenses_percent: Any = Decimal("0")
    kurgin_fixed_margin_usd_per_ct: Any = Decimal("0")
    kurgin_variable_margin_percent: Any = Decimal("0")
    tax_on_profit_percent: Any = Decimal("15")
    jeweler_fixed_margin_usd_per_ct: Any = Decimal("0")
    jeweler_variable_margin_percent: Any = Decimal("0")
    public_fixed_extra_rub: Any = Decimal("0")
    public_extra_percent: Any = Decimal("0")
    minimum_net_profit_fixed_rub: Any = Decimal("0")
    minimum_net_profit_percent_by_tier: Any = Decimal("0")


@dataclass(frozen=True)
class PricingV02LiteResult:
    formula_version: str
    price_status: str
    calculated_specialist_purchase_price_rub: int
    calculated_specialist_client_display_price_rub: int
    calculated_public_price_rub: int
    base_cost_per_ct: float
    score_adjusted_cost_per_ct: float
    allocated_batch_expense_rub: int
    batch_expense_included_in_final_price: bool
    kurgin_tax_reserve_per_ct: float
    net_profit_after_tax_rub: int
    minimum_net_profit_required_rub: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    public_extra_rub: int = 0
    stone_share: float = 0.0
    fx_protected_purchase_cost_rub: int = 0
    projected_purchase_total_rub: int = 0
    fx_buffer_rub: int = 0
    gross_margin_rub: int = 0
    tax_reserve_rub: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _to_decimal(value: Any, default: Decimal | None = None) -> Decimal | None:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return Decimal(1) if value else Decimal(0)

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "—", "-"}:
        return default

    cleaned = (
        text.replace("\u00a0", "")
        .replace(" ", "")
        .replace(",", ".")
        .replace("₽", "")
        .replace("$", "")
        .replace("usd", "")
        .replace("rub", "")
        .replace("rur", "")
    )
    allowed: list[str] = []
    dot_seen = False
    minus_seen = False
    for char in cleaned:
        if char.isdigit():
            allowed.append(char)
        elif char == "." and not dot_seen:
            allowed.append(char)
            dot_seen = True
        elif char == "-" and not minus_seen and not allowed:
            allowed.append(char)
            minus_seen = True

    number_text = "".join(allowed)
    if number_text in {"", "-", ".", "-."}:
        return default
    try:
        return Decimal(number_text)
    except InvalidOperation:
        return default


def _positive_decimal(value: Any, field_name: str, errors: list[str]) -> Decimal:
    result = _to_decimal(value)
    if result is None or result <= 0:
        errors.append(f"{field_name}_required")
        return Decimal("0")
    return result


def _decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    return _to_decimal(value, default) or default


def ceil_to_1000(value: Any) -> int:
    amount = _to_decimal(value, Decimal("0")) or Decimal("0")
    if amount <= 0:
        return 0
    rounded = (amount / ROUNDING_UNIT_RUB).to_integral_value(rounding=ROUND_CEILING) * ROUNDING_UNIT_RUB
    return int(rounded)


def calculate_stone_share(stone_purchase_total_currency: Any, batch_total_supplier_currency: Any) -> Decimal:
    stone_total = _to_decimal(stone_purchase_total_currency, Decimal("0")) or Decimal("0")
    batch_total = _to_decimal(batch_total_supplier_currency, Decimal("0")) or Decimal("0")
    if stone_total <= 0 or batch_total <= 0:
        return Decimal("0")
    return stone_total / batch_total


def calculate_allocated_batch_expense(batch_fixed_expenses_rub: Any, stone_share: Any) -> int:
    expenses = _to_decimal(batch_fixed_expenses_rub, Decimal("0")) or Decimal("0")
    share = _to_decimal(stone_share, Decimal("0")) or Decimal("0")
    if expenses <= 0 or share <= 0:
        return 0
    return int((expenses * share).to_integral_value(rounding=ROUND_CEILING))


def calculate_base_cost_per_ct(
    base_purchase_price_per_ct: Any,
    customs_percent: Any,
    freight_percent: Any,
    unexpected_expenses_percent: Any,
) -> Decimal:
    base = _to_decimal(base_purchase_price_per_ct, Decimal("0")) or Decimal("0")
    customs = _to_decimal(customs_percent, Decimal("0")) or Decimal("0")
    freight = _to_decimal(freight_percent, Decimal("0")) or Decimal("0")
    unexpected = _to_decimal(unexpected_expenses_percent, Decimal("0")) or Decimal("0")
    return base * (Decimal("1") + customs / Decimal("100")) * (Decimal("1") + freight / Decimal("100")) * (Decimal("1") + unexpected / Decimal("100"))


def calculate_score_adjusted_cost_per_ct(base_cost_per_ct: Any, kurgin_score_coefficient: Any) -> Decimal:
    base = _to_decimal(base_cost_per_ct, Decimal("0")) or Decimal("0")
    coefficient = _to_decimal(kurgin_score_coefficient, Decimal("1")) or Decimal("1")
    return base * coefficient


def calculate_specialist_purchase_price(
    score_adjusted_cost_per_ct: Any,
    kurgin_fixed_margin_usd_per_ct: Any,
    kurgin_variable_margin_percent: Any,
    tax_on_profit_percent: Any,
) -> dict[str, Decimal]:
    cost = _to_decimal(score_adjusted_cost_per_ct, Decimal("0")) or Decimal("0")
    fixed_margin = _to_decimal(kurgin_fixed_margin_usd_per_ct, Decimal("0")) or Decimal("0")
    variable_percent = _to_decimal(kurgin_variable_margin_percent, Decimal("0")) or Decimal("0")
    tax_percent = _to_decimal(tax_on_profit_percent, Decimal("0")) or Decimal("0")

    margin = fixed_margin + cost * variable_percent / Decimal("100")
    tax_reserve = margin * tax_percent / Decimal("100")
    specialist_purchase_per_ct = cost + margin + tax_reserve
    return {
        "kurgin_net_margin_target_per_ct": margin,
        "kurgin_tax_reserve_per_ct": tax_reserve,
        "specialist_purchase_per_ct": specialist_purchase_per_ct,
    }


def calculate_specialist_client_display_price(
    specialist_purchase_per_ct: Any,
    jeweler_fixed_margin_usd_per_ct: Any,
    jeweler_variable_margin_percent: Any,
) -> dict[str, Decimal]:
    purchase = _to_decimal(specialist_purchase_per_ct, Decimal("0")) or Decimal("0")
    fixed_margin = _to_decimal(jeweler_fixed_margin_usd_per_ct, Decimal("0")) or Decimal("0")
    variable_percent = _to_decimal(jeweler_variable_margin_percent, Decimal("0")) or Decimal("0")
    jeweler_margin = fixed_margin + purchase * variable_percent / Decimal("100")
    return {
        "jeweler_margin_per_ct": jeweler_margin,
        "specialist_client_display_per_ct": purchase + jeweler_margin,
    }


def calculate_public_price(
    specialist_client_display_price_rub: Any,
    public_fixed_extra_rub: Any,
    public_extra_percent: Any,
) -> dict[str, int]:
    client_price = _to_decimal(specialist_client_display_price_rub, Decimal("0")) or Decimal("0")
    fixed_extra = _to_decimal(public_fixed_extra_rub, Decimal("0")) or Decimal("0")
    extra_percent = _to_decimal(public_extra_percent, Decimal("0")) or Decimal("0")
    percent_extra = client_price * extra_percent / Decimal("100")
    public_extra = max(fixed_extra, percent_extra)
    return {
        "public_extra_rub": int(public_extra.to_integral_value(rounding=ROUND_CEILING)),
        "public_price_rub": ceil_to_1000(client_price + public_extra),
    }


def run_fx_guard(final_price_rub: Any, fx_protected_purchase_cost_rub: Any, minimum_net_profit_required_rub: Any = 0) -> dict[str, tuple[str, ...] | str]:
    final_price = _to_decimal(final_price_rub, Decimal("0")) or Decimal("0")
    protected_cost = _to_decimal(fx_protected_purchase_cost_rub, Decimal("0")) or Decimal("0")
    minimum_profit = _to_decimal(minimum_net_profit_required_rub, Decimal("0")) or Decimal("0")
    if final_price < protected_cost:
        return {"status": STATUS_BLOCKED, "errors": (ERROR_BELOW_FX_PROTECTED_PURCHASE_COST,), "warnings": ()}
    if final_price < protected_cost + minimum_profit:
        return {"status": STATUS_NEEDS_REVIEW, "errors": (), "warnings": (WARNING_PRICE_TOO_CLOSE_TO_PURCHASE_COST,)}
    return {"status": STATUS_OK, "errors": (), "warnings": ()}


def run_after_tax_guard(final_price_rub: Any, score_adjusted_cost_rub: Any, tax_on_profit_percent: Any) -> dict[str, Any]:
    final_price = _to_decimal(final_price_rub, Decimal("0")) or Decimal("0")
    cost = _to_decimal(score_adjusted_cost_rub, Decimal("0")) or Decimal("0")
    tax_percent = _to_decimal(tax_on_profit_percent, Decimal("0")) or Decimal("0")
    gross_margin = final_price - cost
    tax_reserve = gross_margin * tax_percent / Decimal("100") if gross_margin > 0 else Decimal("0")
    net_profit = gross_margin - tax_reserve
    if net_profit <= 0:
        status = STATUS_BLOCKED
        errors = (ERROR_AFTER_TAX_PROFIT_NEGATIVE,)
    else:
        status = STATUS_OK
        errors = ()
    return {
        "status": status,
        "errors": errors,
        "warnings": (),
        "gross_margin_rub": int(gross_margin.to_integral_value(rounding=ROUND_CEILING)),
        "tax_reserve_rub": int(tax_reserve.to_integral_value(rounding=ROUND_CEILING)),
        "net_profit_after_tax_rub": int(net_profit.to_integral_value(rounding=ROUND_CEILING)),
    }


def run_minimum_profit_guard(net_profit_after_tax_rub: Any, minimum_net_profit_required_rub: Any) -> dict[str, tuple[str, ...] | str]:
    net_profit = _to_decimal(net_profit_after_tax_rub, Decimal("0")) or Decimal("0")
    minimum_profit = _to_decimal(minimum_net_profit_required_rub, Decimal("0")) or Decimal("0")
    if net_profit <= 0:
        return {"status": STATUS_BLOCKED, "errors": (ERROR_AFTER_TAX_PROFIT_NEGATIVE,), "warnings": ()}
    if net_profit < minimum_profit:
        return {"status": STATUS_NEEDS_REVIEW, "errors": (), "warnings": (WARNING_AFTER_TAX_PROFIT_BELOW_MINIMUM,)}
    return {"status": STATUS_OK, "errors": (), "warnings": ()}


def run_price_hierarchy_guard(specialist_purchase_price_rub: Any, specialist_client_display_price_rub: Any, public_price_rub: Any) -> dict[str, tuple[str, ...] | str]:
    specialist = _to_decimal(specialist_purchase_price_rub, Decimal("0")) or Decimal("0")
    client = _to_decimal(specialist_client_display_price_rub, Decimal("0")) or Decimal("0")
    public = _to_decimal(public_price_rub, Decimal("0")) or Decimal("0")
    if not specialist < client < public:
        return {"status": STATUS_BLOCKED, "errors": (ERROR_PRICE_HIERARCHY_INVALID,), "warnings": ()}
    return {"status": STATUS_OK, "errors": (), "warnings": ()}


def _combine_status(current: str, incoming: str) -> str:
    if current == STATUS_BLOCKED or incoming == STATUS_BLOCKED:
        return STATUS_BLOCKED
    if current == STATUS_NEEDS_REVIEW or incoming == STATUS_NEEDS_REVIEW:
        return STATUS_NEEDS_REVIEW
    return STATUS_OK


def calculate_pricing_v02_lite(
    purchase: PurchaseInput | dict[str, Any],
    batch: BatchInput | dict[str, Any],
    formula: FormulaInput | dict[str, Any],
) -> PricingV02LiteResult:
    if isinstance(purchase, dict):
        purchase = PurchaseInput(**purchase)
    if isinstance(batch, dict):
        batch = BatchInput(**batch)
    if isinstance(formula, dict):
        formula = FormulaInput(**formula)

    warnings: list[str] = [WARNING_BATCH_EXPENSE_NOT_INCLUDED_IN_FINAL_PRICE]
    errors: list[str] = []
    price_status = STATUS_OK

    carat = _positive_decimal(purchase.carat, "carat", errors)
    base_purchase_price = _positive_decimal(purchase.base_purchase_price_per_ct_supplier_currency, "base_purchase_price_per_ct_supplier_currency", errors)
    fx_rate = _positive_decimal(purchase.fx_rate_rub_per_invoice_currency, "fx_rate_rub_per_invoice_currency", errors)

    purchase_status = str(purchase.purchase_status or "").strip().lower()
    if purchase_status == "pending_invoice_same_shipment":
        errors.append(ERROR_PENDING_INVOICE_SAME_SHIPMENT)
        price_status = STATUS_BLOCKED

    stone_purchase_total_currency = base_purchase_price * carat
    stone_share = calculate_stone_share(stone_purchase_total_currency, batch.batch_total_supplier_currency)
    allocated_batch_expense_rub = calculate_allocated_batch_expense(batch.batch_fixed_expenses_rub, stone_share)

    base_cost_per_ct = calculate_base_cost_per_ct(
        base_purchase_price,
        formula.customs_percent,
        formula.freight_percent,
        formula.unexpected_expenses_percent,
    )
    score_adjusted_cost_per_ct = calculate_score_adjusted_cost_per_ct(base_cost_per_ct, purchase.kurgin_score_coefficient)

    specialist_layer = calculate_specialist_purchase_price(
        score_adjusted_cost_per_ct,
        formula.kurgin_fixed_margin_usd_per_ct,
        formula.kurgin_variable_margin_percent,
        formula.tax_on_profit_percent,
    )
    specialist_purchase_per_ct = specialist_layer["specialist_purchase_per_ct"]

    client_layer = calculate_specialist_client_display_price(
        specialist_purchase_per_ct,
        formula.jeweler_fixed_margin_usd_per_ct,
        formula.jeweler_variable_margin_percent,
    )
    specialist_client_display_per_ct = client_layer["specialist_client_display_per_ct"]

    specialist_purchase_price_rub = ceil_to_1000(specialist_purchase_per_ct * carat * fx_rate)
    specialist_client_display_price_rub = ceil_to_1000(specialist_client_display_per_ct * carat * fx_rate)
    public_layer = calculate_public_price(
        specialist_client_display_price_rub,
        formula.public_fixed_extra_rub,
        formula.public_extra_percent,
    )
    public_extra_rub = public_layer["public_extra_rub"]
    public_price_rub = public_layer["public_price_rub"]

    projected_purchase_total_rub = int((stone_purchase_total_currency * fx_rate).to_integral_value(rounding=ROUND_CEILING))
    fx_buffer_percent = _decimal(purchase.fx_buffer_percent)
    fx_buffer_rub = int((Decimal(projected_purchase_total_rub) * fx_buffer_percent / Decimal("100")).to_integral_value(rounding=ROUND_CEILING))
    actual_paid = _to_decimal(purchase.actual_purchase_total_rub)
    if purchase_status == "paid" and actual_paid is not None and actual_paid > 0:
        fx_protected_purchase_cost_rub = int(actual_paid.to_integral_value(rounding=ROUND_CEILING))
    else:
        fx_protected_purchase_cost_rub = projected_purchase_total_rub + fx_buffer_rub

    protected_cost_rub = Decimal(fx_protected_purchase_cost_rub + allocated_batch_expense_rub)
    minimum_net_profit_required_rub = max(
        _decimal(formula.minimum_net_profit_fixed_rub),
        protected_cost_rub * _decimal(formula.minimum_net_profit_percent_by_tier) / Decimal("100"),
    )
    minimum_net_profit_required_int = int(minimum_net_profit_required_rub.to_integral_value(rounding=ROUND_CEILING))

    score_adjusted_cost_rub = score_adjusted_cost_per_ct * carat * fx_rate

    guard_results = [
        run_fx_guard(public_price_rub, fx_protected_purchase_cost_rub, minimum_net_profit_required_int),
        run_after_tax_guard(public_price_rub, score_adjusted_cost_rub, formula.tax_on_profit_percent),
    ]
    after_tax = guard_results[1]
    guard_results.append(run_minimum_profit_guard(after_tax["net_profit_after_tax_rub"], minimum_net_profit_required_int))
    guard_results.append(run_price_hierarchy_guard(specialist_purchase_price_rub, specialist_client_display_price_rub, public_price_rub))

    for guard in guard_results:
        price_status = _combine_status(price_status, str(guard["status"]))
        errors.extend(guard.get("errors", ()))
        warnings.extend(guard.get("warnings", ()))

    if errors:
        price_status = STATUS_BLOCKED

    return PricingV02LiteResult(
        formula_version=FORMULA_VERSION,
        price_status=price_status,
        calculated_specialist_purchase_price_rub=specialist_purchase_price_rub,
        calculated_specialist_client_display_price_rub=specialist_client_display_price_rub,
        calculated_public_price_rub=public_price_rub,
        base_cost_per_ct=float(base_cost_per_ct),
        score_adjusted_cost_per_ct=float(score_adjusted_cost_per_ct),
        allocated_batch_expense_rub=allocated_batch_expense_rub,
        batch_expense_included_in_final_price=False,
        kurgin_tax_reserve_per_ct=float(specialist_layer["kurgin_tax_reserve_per_ct"]),
        net_profit_after_tax_rub=int(after_tax["net_profit_after_tax_rub"]),
        minimum_net_profit_required_rub=minimum_net_profit_required_int,
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(dict.fromkeys(errors)),
        public_extra_rub=public_extra_rub,
        stone_share=float(stone_share),
        fx_protected_purchase_cost_rub=fx_protected_purchase_cost_rub,
        projected_purchase_total_rub=projected_purchase_total_rub,
        fx_buffer_rub=fx_buffer_rub,
        gross_margin_rub=int(after_tax["gross_margin_rub"]),
        tax_reserve_rub=int(after_tax["tax_reserve_rub"]),
    )
