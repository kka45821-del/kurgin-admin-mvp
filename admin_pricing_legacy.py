from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st

from admin_io import load_stones, save_stones
from admin_log import write_admin_action
from admin_pricing_rules import calculate_price
from admin_pricing_shared import count_status, effective_section_for_stone_dict, format_tuple


PREVIEW_COLUMNS = [
    "stone_id",
    "shape",
    "carat",
    "color",
    "clarity",
    "section",
    "price_status",
    "raw_calculated_price_rub",
    "calculated_price_rub",
    "score_coefficient",
    "public_action",
    "rate_warning",
    "warnings",
    "errors",
]

CONFIRMATION_EXTRA_COLUMNS = [
    "confirmed_public_price_rub",
    "calculated_price_rub",
    "raw_calculated_price_rub",
    "manual_usd_rub_rate",
    "global_price_adjustment_percent",
    "pricing_run_timestamp",
]


def preview_summary(preview: pd.DataFrame) -> dict[str, int]:
    statuses = preview["price_status"].fillna("missing").astype(str).value_counts()
    warnings = preview["warnings"].fillna("").astype(str).str.strip()
    errors = preview["errors"].fillna("").astype(str).str.strip()
    rate_warning = preview["rate_warning"].fillna(False).astype(bool)

    return {
        "total": int(len(preview)),
        "calculated": count_status(statuses, "calculated"),
        "request_price": count_status(statuses, "request_price"),
        "score_required": count_status(statuses, "score_required"),
        "future_scope": count_status(statuses, "future_scope"),
        "blocked_missing": count_status(statuses, "blocked", "missing"),
        "rows_with_warnings": int(warnings.ne("").sum()),
        "rows_with_errors": int(errors.ne("").sum()),
        "rate_warning": int(rate_warning.sum()),
    }


def build_pricing_preview(
    stones: pd.DataFrame,
    price_table: pd.DataFrame,
    manual_usd_rub_rate: float,
    reference_cbr_usd_rub_rate: float | None,
    rate_warning_threshold_rub: float,
    global_price_adjustment_percent: float,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, stone in stones.iterrows():
        stone_dict = stone.to_dict()
        effective_section = effective_section_for_stone_dict(stone_dict)
        if effective_section:
            stone_dict["section"] = effective_section
        result = calculate_price(
            stone=stone_dict,
            price_table=price_table,
            manual_usd_rub_rate=manual_usd_rub_rate,
            reference_cbr_usd_rub_rate=reference_cbr_usd_rub_rate,
            rate_warning_threshold_rub=rate_warning_threshold_rub,
            global_price_adjustment_percent=global_price_adjustment_percent,
        )
        rows.append(
            {
                "stone_id": stone_dict.get("stone_id", ""),
                "shape": stone_dict.get("shape", ""),
                "carat": stone_dict.get("carat", ""),
                "color": stone_dict.get("color", ""),
                "clarity": stone_dict.get("clarity", ""),
                "section": stone_dict.get("section", ""),
                "price_status": result.get("price_status") or result.get("status", ""),
                "raw_calculated_price_rub": result.get("raw_calculated_price_rub"),
                "calculated_price_rub": result.get("calculated_price_rub"),
                "score_coefficient": result.get("score_coefficient"),
                "public_action": result.get("public_action", ""),
                "rate_warning": bool(result.get("rate_warning", False)),
                "warnings": format_tuple(result.get("warnings", ())),
                "errors": format_tuple(result.get("errors", ())),
            }
        )
    return pd.DataFrame(rows, columns=PREVIEW_COLUMNS)


def confirmable_preview(preview: pd.DataFrame) -> pd.DataFrame:
    if preview.empty:
        return preview.copy()
    calculated_price = pd.to_numeric(preview["calculated_price_rub"], errors="coerce").fillna(0)
    errors = preview["errors"].fillna("").astype(str).str.strip()
    mask = preview["price_status"].eq("calculated") & calculated_price.gt(0) & errors.eq("")
    return preview.loc[mask].copy()


def _ensure_confirmation_columns(stones: pd.DataFrame) -> pd.DataFrame:
    updated = stones.copy()
    for col in CONFIRMATION_EXTRA_COLUMNS:
        if col not in updated.columns:
            updated[col] = ""
    for col in ["price_rub", "price_confirmed", "price_status", "price_source", "index_price_hint"]:
        if col not in updated.columns:
            updated[col] = ""
    return updated


def apply_mass_price_confirmation(
    selected: pd.DataFrame,
    manual_usd_rub_rate: float,
    global_price_adjustment_percent: float,
) -> int:
    stones = _ensure_confirmation_columns(load_stones())
    if stones.empty or selected.empty or "stone_id" not in stones.columns:
        return 0

    timestamp = datetime.now(timezone.utc).isoformat()
    confirmed_count = 0
    selected_by_id = selected.set_index("stone_id", drop=False)

    for index, stone in stones.iterrows():
        stone_id = str(stone.get("stone_id", ""))
        if not stone_id or stone_id not in selected_by_id.index:
            continue

        row = selected_by_id.loc[stone_id]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]

        calculated_price = pd.to_numeric(pd.Series([row.get("calculated_price_rub")]), errors="coerce").fillna(0).iloc[0]
        if calculated_price <= 0:
            continue

        raw_price = row.get("raw_calculated_price_rub", "")
        stones.at[index, "confirmed_public_price_rub"] = int(calculated_price)
        stones.at[index, "price_rub"] = int(calculated_price)
        stones.at[index, "price_confirmed"] = True
        stones.at[index, "price_status"] = "confirmed"
        stones.at[index, "price_source"] = "pricing_engine"
        stones.at[index, "index_price_hint"] = int(calculated_price)
        stones.at[index, "calculated_price_rub"] = int(calculated_price)
        stones.at[index, "raw_calculated_price_rub"] = "" if pd.isna(raw_price) else raw_price
        stones.at[index, "manual_usd_rub_rate"] = manual_usd_rub_rate
        stones.at[index, "global_price_adjustment_percent"] = global_price_adjustment_percent
        stones.at[index, "pricing_run_timestamp"] = timestamp
        confirmed_count += 1

    if confirmed_count > 0:
        save_stones(stones)
    return confirmed_count


def render_legacy_pricing_preview(
    stones: pd.DataFrame,
    price_table: pd.DataFrame,
    manual_rate: float,
    reference_rate: float | None,
    threshold: float,
    adjustment: float,
) -> None:
    if st.button("Рассчитать preview", type="primary"):
        st.session_state["pricing_preview"] = build_pricing_preview(
            stones=stones,
            price_table=price_table,
            manual_usd_rub_rate=manual_rate,
            reference_cbr_usd_rub_rate=reference_rate,
            rate_warning_threshold_rub=threshold,
            global_price_adjustment_percent=adjustment,
        )
        st.session_state["pricing_preview_params"] = {
            "manual_rate": manual_rate,
            "reference_rate": reference_rate,
            "threshold": threshold,
            "adjustment": adjustment,
        }

    preview = st.session_state.get("pricing_preview")
    params = st.session_state.get("pricing_preview_params", {})
    if preview is None:
        return

    summary = preview_summary(preview)

    st.markdown("#### Pricing summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Всего строк", summary["total"])
    m2.metric("Calculated", summary["calculated"])
    m3.metric("Request price", summary["request_price"])
    m4.metric("Score required", summary["score_required"])

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Future scope", summary["future_scope"])
    m6.metric("Blocked / missing", summary["blocked_missing"])
    m7.metric("Rows with warnings", summary["rows_with_warnings"])
    m8.metric("Rows with errors", summary["rows_with_errors"])

    st.metric("Rate warning", summary["rate_warning"])

    st.markdown("#### Calculated price preview")
    st.dataframe(preview, use_container_width=True)

    status_counts = preview["price_status"].fillna("missing").value_counts().rename_axis("price_status").reset_index(name="count")
    st.markdown("#### Price status summary")
    st.dataframe(status_counts, use_container_width=True)

    details = (
        f"manual_usd_rub_rate={params.get('manual_rate')}; "
        f"reference_cbr_usd_rub_rate={params.get('reference_rate')}; "
        f"rate_warning_threshold_rub={params.get('threshold')}; "
        f"global_price_adjustment_percent={params.get('adjustment')}; "
        f"summary={summary}"
    )
    write_admin_action(
        action="pricing_preview_run",
        entity="pricing_engine",
        rows_count=len(preview),
        source="admin_pricing",
        details=details,
    )
    st.caption("Audit log: pricing_preview_run записан. Preview сам по себе цены не сохраняет.")

    st.markdown("#### Mass Price Confirmation")
    st.warning("Подтверждение цен сохраняет цены в stones.csv, но НЕ публикует catalog.json и НЕ включает checkout.")

    confirmable = confirmable_preview(preview)
    if confirmable.empty:
        st.info("Нет строк, доступных для подтверждения. Требуется price_status=calculated, calculated_price_rub > 0 и пустые errors.")
        return

    selection = confirmable.copy()
    selection.insert(0, "confirm", False)
    edited_selection = st.data_editor(
        selection,
        use_container_width=True,
        hide_index=True,
        disabled=[col for col in selection.columns if col != "confirm"],
    )
    selected = edited_selection[edited_selection["confirm"] == True].copy()
    st.caption(f"Выбрано к подтверждению: {len(selected)}")

    if st.button("Подтвердить выбранные цены", type="primary", disabled=selected.empty):
        confirmed_count = apply_mass_price_confirmation(
            selected=selected,
            manual_usd_rub_rate=float(params.get("manual_rate") or manual_rate),
            global_price_adjustment_percent=float(params.get("adjustment") or adjustment),
        )
        write_admin_action(
            action="mass_price_confirmation",
            entity="pricing_engine",
            rows_count=confirmed_count,
            source="admin_pricing",
            details=(
                f"manual_usd_rub_rate={params.get('manual_rate')}; "
                f"global_price_adjustment_percent={params.get('adjustment')}; "
                f"confirmed_count={confirmed_count}; "
                f"summary={summary}"
            ),
        )
        if confirmed_count > 0:
            st.success(f"Подтверждено цен: {confirmed_count}. catalog.json не опубликован; checkout не включён.")
        else:
            st.error("Не удалось подтвердить выбранные цены. Проверь stone_id и preview.")
