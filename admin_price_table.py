from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from admin_pricing_shared import read_price_table
from admin_pricing_template import PRICE_TABLE_TEMPLATE_COLUMNS, PRICE_TEMPLATE_BANDS, PRICE_TEMPLATE_VALUES


PRICE_TABLE_PATH = Path("data") / "price_table.csv"
PRICE_TABLE_SESSION_KEY = "admin_price_table_uploaded_preview"


def default_price_table_frame() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (color, clarity), values in PRICE_TEMPLATE_VALUES.items():
        for index, value in enumerate(values):
            band_from, band_to, active_band = PRICE_TEMPLATE_BANDS[index]
            rows.append(
                {
                    "section": "",
                    "carat_band_from": float(band_from),
                    "carat_band_to": float(band_to),
                    "color": color,
                    "clarity": clarity,
                    "base_price_usd_per_carat": int(value or 0),
                    "is_active": bool(active_band),
                }
            )
    return pd.DataFrame(rows, columns=PRICE_TABLE_TEMPLATE_COLUMNS)


def normalize_price_table(table: pd.DataFrame) -> pd.DataFrame:
    normalized = table.copy() if table is not None else pd.DataFrame(columns=PRICE_TABLE_TEMPLATE_COLUMNS)
    for column in PRICE_TABLE_TEMPLATE_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""

    normalized = normalized[PRICE_TABLE_TEMPLATE_COLUMNS].copy()
    normalized["section"] = normalized["section"].fillna("").astype(str).str.strip()
    normalized["color"] = normalized["color"].fillna("").astype(str).str.strip().str.upper()
    normalized["clarity"] = normalized["clarity"].fillna("").astype(str).str.strip().str.upper()

    for column in ["carat_band_from", "carat_band_to", "base_price_usd_per_carat"]:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce").fillna(0)

    active_text = normalized["is_active"].fillna("").astype(str).str.strip().str.lower()
    normalized["is_active"] = active_text.isin(["true", "1", "yes", "y", "да"])
    return normalized


def load_saved_price_table() -> pd.DataFrame:
    if PRICE_TABLE_PATH.exists():
        try:
            return normalize_price_table(pd.read_csv(PRICE_TABLE_PATH))
        except Exception:
            return pd.DataFrame(columns=PRICE_TABLE_TEMPLATE_COLUMNS)
    return default_price_table_frame()


def save_draft_price_table(table: pd.DataFrame) -> None:
    PRICE_TABLE_PATH.parent.mkdir(exist_ok=True)
    normalize_price_table(table).to_csv(PRICE_TABLE_PATH, index=False)


def price_table_to_excel_bytes(table: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        normalize_price_table(table).to_excel(writer, index=False, sheet_name="KURGIN_Price_Table")
    output.seek(0)
    return output.getvalue()


def render_admin_price_table() -> pd.DataFrame:
    st.markdown("### Admin Price Table v0.1")
    st.warning(
        "Admin Price Table v0.1 сохраняет только draft-таблицу в data/price_table.csv. "
        "Она не подтверждает цены, не публикует catalog.json и не включает checkout."
    )

    current_table = load_saved_price_table()
    st.markdown("#### Current saved admin price table")
    st.caption(f"Строк в текущей таблице: {len(current_table)}")
    st.dataframe(current_table, use_container_width=True)

    st.download_button(
        label="Скачать текущую admin price table Excel",
        data=price_table_to_excel_bytes(current_table),
        file_name="kurgin_admin_price_table.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded_file = st.file_uploader(
        "Загрузить draft price table Excel/CSV",
        type=["xlsx", "xls", "csv"],
        key="admin_price_table_upload",
    )

    if uploaded_file is not None:
        try:
            uploaded_table = normalize_price_table(read_price_table(uploaded_file))
            st.session_state[PRICE_TABLE_SESSION_KEY] = uploaded_table
        except Exception as exc:
            st.error(f"Не удалось прочитать price table: {exc}")

    preview_table = st.session_state.get(PRICE_TABLE_SESSION_KEY)
    if preview_table is not None:
        st.markdown("#### Preview uploaded draft table")
        st.caption(f"Строк в загруженной таблице: {len(preview_table)}")
        st.dataframe(preview_table, use_container_width=True)

        if st.button("Save draft table", type="secondary"):
            save_draft_price_table(preview_table)
            st.success("Draft price table сохранена в data/price_table.csv. catalog.json не опубликован; цены не подтверждены.")
            current_table = load_saved_price_table()

    return current_table
