"""Smoke checks for KURGIN Pricing Formula v0.2-lite."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from admin_pricing_formula_v02_lite import (  # noqa: E402
    ERROR_AFTER_TAX_PROFIT_NEGATIVE,
    ERROR_BATCH_CURRENCY_MISMATCH,
    ERROR_PENDING_INVOICE_SAME_SHIPMENT,
    ERROR_ROUND_SCORE_REQUIRED,
    ERROR_SECTION_OUTSIDE_V02_LITE_SCOPE,
    SCORE_STATUS_NON_ROUND_SCORE_NOT_REQUIRED,
    SCORE_STATUS_ROUND_SCORE_REQUIRED,
    SPECIALIST_MODE_LOW_SCORE_FIXED_RULE,
    SPECIALIST_MODE_NORMAL_NON_ROUND_SCORE_NOT_REQUIRED,
    PurchaseInput,
    BatchInput,
    FormulaInput,
    calculate_pricing_v02_lite,
    run_after_tax_guard,
)


def base_purchase(
    status: str = "projected",
    invoice_currency: str = "USD",
    score=90,
    section: str = "main",
    shape: str = "Round",
) -> PurchaseInput:
    return PurchaseInput(
        base_purchase_price_per_ct_supplier_currency=300,
        carat=1.5,
        invoice_currency=invoice_currency,
        fx_rate_rub_per_invoice_currency=90,
        shape=shape,
        kurgin_score_coefficient=1.2,
        purchase_status=status,
        fx_buffer_percent=3,
        kurgin_score=score,
        section=section,
    )


def base_batch(
    batch_fixed_expenses_rub: int = 80000,
    batch_total_supplier_currency: int = 4500,
    batch_total_currency_code: str = "USD",
) -> BatchInput:
    return BatchInput(
        batch_fixed_expenses_rub=batch_fixed_expenses_rub,
        batch_total_supplier_currency=batch_total_supplier_currency,
        batch_expense_allocation_method="value_share",
        batch_total_currency_code=batch_total_currency_code,
    )


def base_formula(low_score_jeweler_margin_rub: int = 2000, low_score_public_spread_rub: int = 2000) -> FormulaInput:
    return FormulaInput(
        customs_percent=40,
        freight_percent=0,
        unexpected_expenses_percent=0,
        kurgin_fixed_margin_usd_per_ct=120,
        kurgin_variable_margin_percent=10,
        tax_on_profit_percent=15,
        jeweler_fixed_margin_usd_per_ct=90,
        jeweler_variable_margin_percent=8,
        public_fixed_extra_rub=10000,
        public_extra_percent=5,
        minimum_net_profit_fixed_rub=5000,
        minimum_net_profit_percent_by_tier=5,
        low_score_jeweler_margin_rub=low_score_jeweler_margin_rub,
        low_score_public_spread_rub=low_score_public_spread_rub,
    )


def main() -> int:
    result = calculate_pricing_v02_lite(base_purchase(), base_batch(), base_formula())
    assert result.calculated_specialist_purchase_price_rub < result.calculated_specialist_client_display_price_rub < result.calculated_public_price_rub
    assert result.calculated_public_price_rub > 0
    assert result.batch_expense_included_in_final_price is True
    assert result.allocated_batch_expense_rub > 0
    assert ERROR_BATCH_CURRENCY_MISMATCH not in result.errors

    no_expense = calculate_pricing_v02_lite(base_purchase(), base_batch(batch_fixed_expenses_rub=0), base_formula())
    assert no_expense.calculated_public_price_rub < result.calculated_public_price_rub

    zero_batch_total = calculate_pricing_v02_lite(base_purchase(), base_batch(batch_total_supplier_currency=0), base_formula())
    assert zero_batch_total.allocated_batch_expense_rub == 0
    assert zero_batch_total.calculated_public_price_rub > 0
    assert ERROR_BATCH_CURRENCY_MISMATCH not in zero_batch_total.errors

    mismatch = calculate_pricing_v02_lite(base_purchase("projected", "USD"), base_batch(batch_total_currency_code="INR"), base_formula())
    assert mismatch.price_status == "blocked"
    assert ERROR_BATCH_CURRENCY_MISMATCH in mismatch.errors

    same_currency = calculate_pricing_v02_lite(base_purchase("projected", "INR"), base_batch(batch_total_currency_code="INR"), base_formula())
    assert ERROR_BATCH_CURRENCY_MISMATCH not in same_currency.errors

    low_score = calculate_pricing_v02_lite(base_purchase(score=75, section="main", shape="Round"), base_batch(), base_formula())
    assert low_score.specialist_client_mode_status == SPECIALIST_MODE_LOW_SCORE_FIXED_RULE
    assert low_score.calculated_specialist_client_display_price_rub == low_score.calculated_specialist_purchase_price_rub + 2000
    assert low_score.calculated_public_price_rub == low_score.calculated_specialist_client_display_price_rub + 2000
    assert low_score.calculated_specialist_purchase_price_rub < low_score.calculated_specialist_client_display_price_rub < low_score.calculated_public_price_rub

    custom_low_score = calculate_pricing_v02_lite(base_purchase(score=75, section="main", shape="Round"), base_batch(), base_formula(2500, 3000))
    assert custom_low_score.calculated_specialist_client_display_price_rub == custom_low_score.calculated_specialist_purchase_price_rub + 2500
    assert custom_low_score.calculated_public_price_rub == custom_low_score.calculated_specialist_client_display_price_rub + 3000
    assert custom_low_score.low_score_jeweler_margin_rub == 2500
    assert custom_low_score.low_score_public_spread_rub == 3000

    score_80 = calculate_pricing_v02_lite(base_purchase(score=80, section="main", shape="Round"), base_batch(), base_formula())
    assert score_80.specialist_client_mode_status != SPECIALIST_MODE_LOW_SCORE_FIXED_RULE

    score_85_large = calculate_pricing_v02_lite(base_purchase(score=85, section="large", shape="Round"), base_batch(), base_formula())
    assert score_85_large.specialist_client_mode_status != SPECIALIST_MODE_LOW_SCORE_FIXED_RULE

    non_round_missing_score = calculate_pricing_v02_lite(base_purchase(score="", section="main", shape="Oval"), base_batch(), base_formula())
    assert non_round_missing_score.price_status != "blocked"
    assert non_round_missing_score.effective_kurgin_score_coefficient == 1.0
    assert non_round_missing_score.score_status == SCORE_STATUS_NON_ROUND_SCORE_NOT_REQUIRED
    assert non_round_missing_score.specialist_client_mode_status == SPECIALIST_MODE_NORMAL_NON_ROUND_SCORE_NOT_REQUIRED

    round_missing_score = calculate_pricing_v02_lite(base_purchase(score="", section="main", shape="Round"), base_batch(), base_formula())
    assert round_missing_score.price_status == "blocked"
    assert ERROR_ROUND_SCORE_REQUIRED in round_missing_score.errors
    assert round_missing_score.score_status == SCORE_STATUS_ROUND_SCORE_REQUIRED

    colored_scope = calculate_pricing_v02_lite(base_purchase(score=90, section="colored", shape="Round"), base_batch(), base_formula())
    assert colored_scope.price_status == "blocked"
    assert ERROR_SECTION_OUTSIDE_V02_LITE_SCOPE in colored_scope.errors

    low_margin = run_after_tax_guard(final_price_rub=100, protected_cost_rub=200, tax_on_profit_percent=15)
    assert low_margin["status"] == "blocked"
    assert ERROR_AFTER_TAX_PROFIT_NEGATIVE in low_margin["errors"]

    pending = calculate_pricing_v02_lite(base_purchase("pending_invoice_same_shipment"), base_batch(), base_formula())
    assert pending.price_status == "blocked"
    assert ERROR_PENDING_INVOICE_SAME_SHIPMENT in pending.errors

    print("smoke_pricing_formula_v02_lite: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
