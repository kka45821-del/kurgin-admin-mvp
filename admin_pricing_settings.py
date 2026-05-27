from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st


PRICING_FORMULA_SETTINGS_PATH = Path("data") / "pricing_formula_settings.json"


DEFAULT_PRICING_FORMULA_SETTINGS: dict[str, float] = {
    "customs_percent": 40.0,
    "freight_percent": 5.0,
    "unexpected_expenses_percent": 5.0,
    "kurgin_fixed_margin_usd_per_ct": 80.0,
    "kurgin_variable_margin_percent": 6.0,
    "tax_on_profit_percent": 18.0,
    "jeweler_fixed_margin_usd_per_ct": 30.0,
    "jeweler_variable_margin_percent": 8.0,
    "public_fixed_extra_rub": 5000.0,
    "public_extra_percent": 2.0,
    "low_score_jeweler_margin_rub": 2000.0,
    "low_score_public_spread_rub": 2000.0,
    "fx_buffer_percent": 3.0,
    "minimum_net_profit_fixed_rub": 5000.0,
    "minimum_net_profit_percent_by_tier": 5.0,
}


def default_pricing_formula_settings() -> dict[str, float]:
    return dict(DEFAULT_PRICING_FORMULA_SETTINGS)


def normalize_pricing_formula_settings(settings: dict[str, Any] | None) -> dict[str, float]:
    normalized = default_pricing_formula_settings()
    if not isinstance(settings, dict):
        return normalized
    for key, default_value in normalized.items():
        try:
            normalized[key] = float(settings.get(key, default_value))
        except (TypeError, ValueError):
            normalized[key] = default_value
    return normalized


def load_pricing_formula_settings() -> dict[str, float]:
    if not PRICING_FORMULA_SETTINGS_PATH.exists():
        return default_pricing_formula_settings()
    try:
        with PRICING_FORMULA_SETTINGS_PATH.open("r", encoding="utf-8") as file:
            return normalize_pricing_formula_settings(json.load(file))
    except Exception:
        return default_pricing_formula_settings()


def save_pricing_formula_settings(settings: dict[str, Any]) -> None:
    PRICING_FORMULA_SETTINGS_PATH.parent.mkdir(exist_ok=True)
    normalized = normalize_pricing_formula_settings(settings)
    with PRICING_FORMULA_SETTINGS_PATH.open("w", encoding="utf-8") as file:
        json.dump(normalized, file, ensure_ascii=False, indent=2, sort_keys=True)


def _number_input(label: str, value: float, step: float, key: str) -> float:
    return float(st.number_input(label, min_value=0.0, value=float(value), step=step, key=key))


def render_pricing_formula_settings() -> dict[str, float]:
    st.markdown("#### Pricing Formula Settings v0.1")
    st.warning(
        "Formula settings сохраняются как draft. Они не подтверждают цены, "
        "не публикуют catalog.json и не включают checkout."
    )
    st.caption(
        "Для Streamlit Cloud это пока draft/local-file storage. Позже нужен save-to-GitHub или backend storage."
    )

    saved = load_pricing_formula_settings()

    c1, c2, c3 = st.columns(3)
    settings = {
        "customs_percent": _number_input("customs_percent", saved["customs_percent"], 0.1, "settings_customs_percent"),
        "freight_percent": _number_input("freight_percent", saved["freight_percent"], 0.1, "settings_freight_percent"),
        "unexpected_expenses_percent": _number_input("unexpected_expenses_percent", saved["unexpected_expenses_percent"], 0.1, "settings_unexpected_expenses_percent"),
    }

    c4, c5 = st.columns(2)
    with c4:
        settings["kurgin_fixed_margin_usd_per_ct"] = _number_input(
            "kurgin_fixed_margin_usd_per_ct", saved["kurgin_fixed_margin_usd_per_ct"], 1.0, "settings_kurgin_fixed_margin_usd_per_ct"
        )
    with c5:
        settings["kurgin_variable_margin_percent"] = _number_input(
            "kurgin_variable_margin_percent", saved["kurgin_variable_margin_percent"], 0.1, "settings_kurgin_variable_margin_percent"
        )

    c6, c7, c8 = st.columns(3)
    with c6:
        settings["tax_on_profit_percent"] = _number_input("tax_on_profit_percent", saved["tax_on_profit_percent"], 0.1, "settings_tax_on_profit_percent")
    with c7:
        settings["jeweler_fixed_margin_usd_per_ct"] = _number_input(
            "jeweler_fixed_margin_usd_per_ct", saved["jeweler_fixed_margin_usd_per_ct"], 1.0, "settings_jeweler_fixed_margin_usd_per_ct"
        )
    with c8:
        settings["jeweler_variable_margin_percent"] = _number_input(
            "jeweler_variable_margin_percent", saved["jeweler_variable_margin_percent"], 0.1, "settings_jeweler_variable_margin_percent"
        )

    c9, c10 = st.columns(2)
    with c9:
        settings["public_fixed_extra_rub"] = _number_input("public_fixed_extra_rub", saved["public_fixed_extra_rub"], 1000.0, "settings_public_fixed_extra_rub")
    with c10:
        settings["public_extra_percent"] = _number_input("public_extra_percent", saved["public_extra_percent"], 0.1, "settings_public_extra_percent")

    c11, c12 = st.columns(2)
    with c11:
        settings["low_score_jeweler_margin_rub"] = _number_input(
            "low_score_jeweler_margin_rub", saved["low_score_jeweler_margin_rub"], 500.0, "settings_low_score_jeweler_margin_rub"
        )
    with c12:
        settings["low_score_public_spread_rub"] = _number_input(
            "low_score_public_spread_rub", saved["low_score_public_spread_rub"], 500.0, "settings_low_score_public_spread_rub"
        )

    c13, c14, c15 = st.columns(3)
    with c13:
        settings["fx_buffer_percent"] = _number_input("fx_buffer_percent", saved["fx_buffer_percent"], 0.1, "settings_fx_buffer_percent")
    with c14:
        settings["minimum_net_profit_fixed_rub"] = _number_input(
            "minimum_net_profit_fixed_rub", saved["minimum_net_profit_fixed_rub"], 1000.0, "settings_minimum_net_profit_fixed_rub"
        )
    with c15:
        settings["minimum_net_profit_percent_by_tier"] = _number_input(
            "minimum_net_profit_percent_by_tier", saved["minimum_net_profit_percent_by_tier"], 0.1, "settings_minimum_net_profit_percent_by_tier"
        )

    save_col, reset_col = st.columns(2)
    with save_col:
        if st.button("Save formula settings draft", type="secondary"):
            save_pricing_formula_settings(settings)
            st.success("Formula settings draft сохранён. Цены не подтверждены; catalog.json не опубликован.")
    with reset_col:
        if st.button("Reset to default settings", type="secondary"):
            defaults = default_pricing_formula_settings()
            save_pricing_formula_settings(defaults)
            st.success("Formula settings draft сброшен к defaults. Перезагрузи страницу, чтобы увидеть значения в полях.")
            return defaults

    return normalize_pricing_formula_settings(settings)
