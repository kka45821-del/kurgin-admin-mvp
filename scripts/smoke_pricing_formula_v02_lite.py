"""Smoke checks for KURGIN Pricing Formula v0.2-lite."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from admin_pricing_formula_v02_lite import (  # noqa: E402
    ERROR_AFTER_TAX_PROFIT_NEGATIVE,
    ERROR_PENDING_INVOICE_SAME_SHIPMENT,
    PurchaseInput,
    BatchInput,
    FormulaInput,
    calculate_pricing_v02_lite,
    run_after_tax_guard,
)


def base_purchase(status: str = "projected") -> PurchaseInput:
    return PurchaseInput(
        base_purchase_price_per_ct_supplier_currency=300,
        carat=1.5,
        invoice_currency="USD",
        fx_rate_rub_per_invoice_currency=90,
        kurgin_score_coefficient=1.2,
        purchase_status=status,
        fx_buffer_percent=3,
    )


def base_batch() -> BatchInput:
    return BatchInput(
        batch_fixed_expenses_rub=80000,
        batch_total_supplier_currency=4500,
        batch_expense_allocation_method="value_share",
    )


def base_formula() -> FormulaInput:
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
    )


def main() -> int:
    result = calculate_pricing_v02_lite(base_purchase(), base_batch(), base_formula())
    assert result.calculated_specialist_purchase_price_rub < result.calculated_specialist_client_display_price_rub < result.calculated_public_price_rub
    assert result.calculated_public_price_rub > 0
    assert result.batch_expense_included_in_final_price is False

    low_margin = run_after_tax_guard(final_price_rub=100, score_adjusted_cost_rub=200, tax_on_profit_percent=15)
    assert low_margin["status"] == "blocked"
    assert ERROR_AFTER_TAX_PROFIT_NEGATIVE in low_margin["errors"]

    pending = calculate_pricing_v02_lite(base_purchase("pending_invoice_same_shipment"), base_batch(), base_formula())
    assert pending.price_status == "blocked"
    assert ERROR_PENDING_INVOICE_SAME_SHIPMENT in pending.errors

    print("smoke_pricing_formula_v02_lite: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
