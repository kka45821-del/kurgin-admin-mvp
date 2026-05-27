from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from admin_pricing_formula_v02_lite import (
    BatchInput,
    FormulaInput,
    PurchaseInput,
    calculate_pricing_v02_lite,
)
from admin_pricing_rules import calculate_price
from admin_pricing_shared import count_status, effective_section_for_stone_dict, format_tuple, stone_value


V02_LITE_PREVIEW_COLUMNS = [
    "stone_id",
    "shape",
    "carat",
    "color",
    "clarity",
    "section",
    "kurgin_score",
    "kurgin_score_coefficient",
    "specialist_client_mode_status",
    "calculated_specialist_purchase_price_rub",
    "calculated_specialist_client_display_price_rub",
    "calculated_public_price_rub",
    "allocated_batch_expense_rub",
    "batch_expense_included_in_final_price",
    "net_profit_after_tax_rub",
    "minimum_net_profit_required_rub",
    "price_status",
    "warnings",
    "errors",
    "formula_version",
]


def build_v02_lite_preview(
    stones: pd.DataFrame,
    price_table: pd.DataFrame,
    params: dict[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, stone in stones.iterrows():
        stone_dict = stone.to_dict()
        effective_section = effective_section_for_stone_dict(stone_dict)
        if effective_section:
            stone_dict["section"] = effective_section

        score_value = stone_value(stone_dict, "karo_score", "kurgin_score", "score")
        legacy_result = calculate_price(
            stone=stone_dict,
            price_table=price_table,
            manual_usd_rub_rate=params["fx_rate_rub_per_invoice_currency"],
            reference_cbr_usd_rub_rate=None,
            rate_warning_threshold_rub=3.0,
            global_price_adjustment_percent=0.0,
        )
        base_price = legacy_result.get("base_price_usd_per_carat")
        coefficient = legacy_result.get("score_coefficient") or 1.0
        row_errors = format_tuple(legacy_result.get("errors", ()))
        row_warnings = format_tuple(legacy_result.get("warnings", ()))

        if not base_price or float(base_price) <= 0:
            rows.append(
                {
                    "stone_id": stone_dict.get("stone_id", ""),
                    "shape": stone_dict.get("shape", ""),
                    "carat": stone_dict.get("carat", ""),
                    "color": stone_dict.get("color", ""),
                    "clarity": stone_dict.get("clarity", ""),
                    "section": stone_dict.get("section", ""),
                    "kurgin_score": score_value,
                    "kurgin_score_coefficient": coefficient,
                    "specialist_client_mode_status": "",
                    "calculated_specialist_purchase_price_rub": None,
                    "calculated_specialist_client_display_price_rub": None,
                    "calculated_public_price_rub": None,
                    "allocated_batch_expense_rub": None,
                    "batch_expense_included_in_final_price": None,
                    "net_profit_after_tax_rub": None,
                    "minimum_net_profit_required_rub": None,
                    "price_status": legacy_result.get("price_status") or legacy_result.get("status", "missing"),
                    "warnings": row_warnings,
                    "errors": row_errors or "base_price_usd_per_carat_missing",
                    "formula_version": "pricing_formula_v0_2_lite",
                }
            )
            continue

        purchase = PurchaseInput(
            base_purchase_price_per_ct_supplier_currency=base_price,
            carat=stone_dict.get("carat", 0),
            invoice_currency=params["invoice_currency"],
            fx_rate_rub_per_invoice_currency=params["fx_rate_rub_per_invoice_currency"],
            kurgin_score_coefficient=coefficient,
            purchase_status=str(stone_dict.get("purchase_status") or "projected"),
            fx_buffer_percent=params["fx_buffer_percent"],
            kurgin_score=score_value,
            section=stone_dict.get("section", ""),
        )
        batch = BatchInput(
            batch_fixed_expenses_rub=params["batch_fixed_expenses_rub"],
            batch_total_supplier_currency=params["batch_total_supplier_currency"],
            batch_expense_allocation_method="value_share",
            batch_total_currency_code=params["batch_total_currency"],
        )
        formula = FormulaInput(
            customs_percent=params["customs_percent"],
            freight_percent=params["freight_percent"],
            unexpected_expenses_percent=params["unexpected_expenses_percent"],
            kurgin_fixed_margin_usd_per_ct=params["kurgin_fixed_margin_usd_per_ct"],
            kurgin_variable_margin_percent=params["kurgin_variable_margin_percent"],
            tax_on_profit_percent=params["tax_on_profit_percent"],
            jeweler_fixed_margin_usd_per_ct=params["jeweler_fixed_margin_usd_per_ct"],
            jeweler_variable_margin_percent=params["jeweler_variable_margin_percent"],
            public_fixed_extra_rub=params["public_fixed_extra_rub"],
            public_extra_percent=params["public_extra_percent"],
            minimum_net_profit_fixed_rub=params["minimum_net_profit_fixed_rub"],
            minimum_net_profit_percent_by_tier=params["minimum_net_profit_percent_by_tier"],
        )
        result = calculate_pricing_v02_lite(purchase, batch, formula)
        rows.append(
            {
                "stone_id": stone_dict.get("stone_id", ""),
                "shape": stone_dict.get("shape", ""),
                "carat": stone_dict.get("carat", ""),
                "color": stone_dict.get("color", ""),
                "clarity": stone_dict.get("clarity", ""),
                "section": stone_dict.get("section", ""),
                "kurgin_score": score_value,
                "kurgin_score_coefficient": coefficient,
                "specialist_client_mode_status": result.specialist_client_mode_status,
                "calculated_specialist_purchase_price_rub": result.calculated_specialist_purchase_price_rub,
                "calculated_specialist_client_display_price_rub": result.calculated_specialist_client_display_price_rub,
                "calculated_public_price_rub": result.calculated_public_price_rub,
                "allocated_batch_expense_rub": result.allocated_batch_expense_rub,
                "batch_expense_included_in_final_price": result.batch_expense_included_in_final_price,
                "net_profit_after_tax_rub": result.net_profit_after_tax_rub,
                "minimum_net_profit_required_rub": result.minimum_net_profit_required_rub,
                "price_status": result.price_status,
                "warnings": format_tuple(result.warnings),
                "errors": format_tuple(result.errors),
                "formula_version": result.formula_version,
            }
        )
    return pd.DataFrame(rows, columns=V02_LITE_PREVIEW_COLUMNS)


def v02_lite_summary(preview: pd.DataFrame) -> dict[str, int]:
    if preview.empty:
        return {
            "total": 0,
            "ok": 0,
            "needs_review": 0,
            "blocked": 0,
            "hierarchy_errors": 0,
            "after_tax_warnings_errors": 0,
            "fx_warnings_errors": 0,
            "pending_invoice_blocked": 0,
        }
    statuses = preview["price_status"].fillna("missing").astype(str).value_counts()
    warnings = preview["warnings"].fillna("").astype(str)
    errors = preview["errors"].fillna("").astype(str)
    combined = warnings + ";" + errors
    return {
        "total": int(len(preview)),
        "ok": count_status(statuses, "ok"),
        "needs_review": count_status(statuses, "needs_review"),
        "blocked": count_status(statuses, "blocked"),
        "hierarchy_errors": int(combined.str.contains("price_hierarchy_invalid", regex=False).sum()),
        "after_tax_warnings_errors": int(combined.str.contains("after_tax", regex=False).sum()),
        "fx_warnings_errors": int((combined.str.contains("below_fx_protected_purchase_cost", regex=False) | combined.str.contains("price_too_close_to_purchase_cost", regex=False)).sum()),
        "pending_invoice_blocked": int(combined.str.contains("pending_invoice_same_shipment", regex=False).sum()),
    }


def render_v02_lite_preview(stones: pd.DataFrame, price_table: pd.DataFrame) -> None:
    st.markdown("### Pricing Formula v0.2-lite Preview")
    st.warning("v0.2-lite preview не сохраняет цены, не подтверждает price_confirmed, не публикует catalog.json и не включает checkout.")

    currency_options = ["USD", "INR", "RUB"]
    c1, c2, c3 = st.columns(3)
    invoice_currency = c1.selectbox("Invoice currency", currency_options, index=0, key="v02_invoice_currency")
    fx_rate = c2.number_input("fx_rate_rub_per_invoice_currency", min_value=0.0, value=100.0, step=0.1, key="v02_fx_rate")
    fx_buffer_percent = c3.number_input("fx_buffer_percent", min_value=0.0, value=3.0, step=0.1, key="v02_fx_buffer")

    c_currency, c_batch_total = st.columns(2)
    batch_total_currency = c_currency.selectbox(
        "batch_total_currency",
        currency_options,
        index=currency_options.index(invoice_currency),
        key="v02_batch_total_currency",
    )

    c4, c5, c6 = st.columns(3)
    customs_percent = c4.number_input("customs_percent", min_value=0.0, value=40.0, step=0.1, key="v02_customs")
    freight_percent = c5.number_input("freight_percent", min_value=0.0, value=5.0, step=0.1, key="v02_freight")
    unexpected_percent = c6.number_input("unexpected_expenses_percent", min_value=0.0, value=5.0, step=0.1, key="v02_unexpected")

    c7, c8 = st.columns(2)
    batch_fixed_expenses = c7.number_input("batch_fixed_expenses_rub", min_value=0.0, value=80000.0, step=1000.0, key="v02_batch_expenses")
    batch_total_supplier_currency = c_batch_total.number_input("batch_total_supplier_currency", min_value=0.0, value=0.0, step=100.0, key="v02_batch_total")

    if batch_total_supplier_currency > 0 and batch_total_currency != invoice_currency:
        st.error(
            "batch_total_supplier_currency должен быть в той же валюте, что и "
            "base_purchase_price_per_ct_supplier_currency / invoice_currency. "
            "Сейчас нельзя смешивать USD stone prices и INR batch total."
        )
        st.info(
            "Если price table в USD, batch_total_supplier_currency тоже должен быть USD. "
            "Если batch total введён в INR, нужно использовать INR purchase prices или пересчитать batch total в USD/выбрать invoice_currency=INR."
        )
        return

    c9, c10 = st.columns(2)
    kurgin_fixed_margin = c9.number_input("kurgin_fixed_margin_usd_per_ct", min_value=0.0, value=120.0, step=1.0, key="v02_kurgin_fixed")
    kurgin_variable_margin = c10.number_input("kurgin_variable_margin_percent", min_value=0.0, value=10.0, step=0.1, key="v02_kurgin_variable")

    c11, c12, c13 = st.columns(3)
    tax_percent = c11.number_input("tax_on_profit_percent", min_value=0.0, value=15.0, step=0.1, key="v02_tax")
    jeweler_fixed_margin = c12.number_input("jeweler_fixed_margin_usd_per_ct", min_value=0.0, value=90.0, step=1.0, key="v02_jeweler_fixed")
    jeweler_variable_margin = c13.number_input("jeweler_variable_margin_percent", min_value=0.0, value=8.0, step=0.1, key="v02_jeweler_variable")

    c14, c15, c16 = st.columns(3)
    public_fixed_extra = c14.number_input("public_fixed_extra_rub", min_value=0.0, value=10000.0, step=1000.0, key="v02_public_fixed")
    public_extra_percent = c15.number_input("public_extra_percent", min_value=0.0, value=5.0, step=0.1, key="v02_public_percent")
    minimum_net_profit_fixed = c16.number_input("minimum_net_profit_fixed_rub", min_value=0.0, value=5000.0, step=1000.0, key="v02_min_profit_fixed")

    minimum_net_profit_percent = st.number_input("minimum_net_profit_percent_by_tier", min_value=0.0, value=5.0, step=0.1, key="v02_min_profit_percent")

    params = {
        "invoice_currency": invoice_currency,
        "batch_total_currency": batch_total_currency,
        "fx_rate_rub_per_invoice_currency": fx_rate,
        "fx_buffer_percent": fx_buffer_percent,
        "customs_percent": customs_percent,
        "freight_percent": freight_percent,
        "unexpected_expenses_percent": unexpected_percent,
        "batch_fixed_expenses_rub": batch_fixed_expenses,
        "batch_total_supplier_currency": batch_total_supplier_currency,
        "kurgin_fixed_margin_usd_per_ct": kurgin_fixed_margin,
        "kurgin_variable_margin_percent": kurgin_variable_margin,
        "tax_on_profit_percent": tax_percent,
        "jeweler_fixed_margin_usd_per_ct": jeweler_fixed_margin,
        "jeweler_variable_margin_percent": jeweler_variable_margin,
        "public_fixed_extra_rub": public_fixed_extra,
        "public_extra_percent": public_extra_percent,
        "minimum_net_profit_fixed_rub": minimum_net_profit_fixed,
        "minimum_net_profit_percent_by_tier": minimum_net_profit_percent,
    }

    if st.button("Рассчитать v0.2-lite preview", type="secondary"):
        st.session_state["pricing_v02_lite_preview"] = build_v02_lite_preview(stones, price_table, params)
        st.session_state["pricing_v02_lite_params"] = params

    preview = st.session_state.get("pricing_v02_lite_preview")
    if preview is None:
        st.info("Нажми кнопку v0.2-lite preview, чтобы увидеть расчёт. Данные не сохраняются.")
        return

    summary = v02_lite_summary(preview)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total rows", summary["total"])
    s2.metric("OK", summary["ok"])
    s3.metric("Needs review", summary["needs_review"])
    s4.metric("Blocked", summary["blocked"])

    s5, s6, s7, s8 = st.columns(4)
    s5.metric("Hierarchy errors", summary["hierarchy_errors"])
    s6.metric("After-tax warnings/errors", summary["after_tax_warnings_errors"])
    s7.metric("FX warnings/errors", summary["fx_warnings_errors"])
    s8.metric("Pending invoice blocked", summary["pending_invoice_blocked"])

    st.markdown("#### v0.2-lite calculated preview")
    st.dataframe(preview, use_container_width=True)
    st.caption("v0.2-lite Preview has no confirmation button, no file writes and no catalog publication.")
