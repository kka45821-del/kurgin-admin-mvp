from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd
import streamlit as st

from admin_io import load_stones
from admin_pricing_rules import calculate_price


PREVIEW_COLUMNS = [
    "stone_id",
    "shape",
    "carat",
    "color",
    "clarity",
    "section",
    "price_status",
    "calculated_price_rub",
    "score_coefficient",
    "public_action",
    "warnings",
    "errors",
]


def _read_price_table(uploaded_file: Any) -> pd.DataFrame:
    name = str(getattr(uploaded_file, "name", "")).lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(uploaded_file)

    content = uploaded_file.read()
    try:
        return pd.read_csv(BytesIO(content))
    except Exception:
        return pd.read_excel(BytesIO(content))


def _format_tuple(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "; ".join(str(item) for item in value if str(item))
    return str(value)


def _build_pricing_preview(
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
                "calculated_price_rub": result.get("calculated_price_rub"),
                "score_coefficient": result.get("score_coefficient"),
                "public_action": result.get("public_action", ""),
                "warnings": _format_tuple(result.get("warnings", ())),
                "errors": _format_tuple(result.get("errors", ())),
            }
        )
    return pd.DataFrame(rows, columns=PREVIEW_COLUMNS)


def render_pricing_tab() -> None:
    st.markdown("### Pricing Engine Preview")
    st.caption(
        "Безопасный preview: расчёт не сохраняет цены, не подтверждает price_confirmed, "
        "не публикует catalog.json и не включает checkout."
    )

    stones = load_stones()
    price = pd.to_numeric(stones.get("price_rub", pd.Series(dtype=float)), errors="coerce").fillna(0) if not stones.empty else pd.Series(dtype=float)
    confirmed = (
        stones.get("price_confirmed", pd.Series(dtype=str)).astype(str).str.lower().isin(["true", "1", "yes", "да"])
        if not stones.empty
        else pd.Series(dtype=bool)
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Камней в stones.csv", len(stones))
    c2.metric("С текущей ценой", int((price > 0).sum()))
    c3.metric("Цена подтверждена", int(confirmed.sum()))

    st.warning("Preview не меняет stones.csv. Для sellable позже потребуется отдельное ручное подтверждение цены и publication gate.")

    uploaded_file = st.file_uploader("Price table Excel/CSV", type=["xlsx", "xls", "csv"])
    col_rate, col_ref = st.columns(2)
    manual_rate = col_rate.number_input("Manual USD/RUB rate", min_value=0.0, value=100.0, step=0.1)
    reference_rate_enabled = col_ref.checkbox("Указать reference CBR USD/RUB", value=False)
    reference_rate = None
    if reference_rate_enabled:
        reference_rate = col_ref.number_input("Reference CBR USD/RUB", min_value=0.0, value=100.0, step=0.1)

    col_threshold, col_adjustment = st.columns(2)
    threshold = col_threshold.number_input("Rate warning threshold RUB", min_value=0.0, value=3.0, step=0.1)
    adjustment = col_adjustment.number_input("Global price adjustment %", value=0.0, step=0.1)

    if uploaded_file is None:
        st.info("Загрузи price table, чтобы рассчитать preview.")
        return

    try:
        price_table = _read_price_table(uploaded_file)
    except Exception as exc:
        st.error(f"Не удалось прочитать price table: {exc}")
        return

    st.markdown("#### Price table preview")
    st.caption(f"Строк в price table: {len(price_table)}")
    st.dataframe(price_table.head(20), use_container_width=True)

    if stones.empty:
        st.info("stones.csv пустой. Сначала загрузи каталог камней.")
        return

    if st.button("Рассчитать preview", type="primary"):
        preview = _build_pricing_preview(
            stones=stones,
            price_table=price_table,
            manual_usd_rub_rate=manual_rate,
            reference_cbr_usd_rub_rate=reference_rate,
            rate_warning_threshold_rub=threshold,
            global_price_adjustment_percent=adjustment,
        )
        st.markdown("#### Calculated price preview")
        st.dataframe(preview, use_container_width=True)

        status_counts = preview["price_status"].fillna("missing").value_counts().rename_axis("price_status").reset_index(name="count")
        st.markdown("#### Price status summary")
        st.dataframe(status_counts, use_container_width=True)
