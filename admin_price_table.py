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
ROW_ID_COLUMN = "_row_id"


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
    if normalized["is_active"].dtype == bool:
        normalized["is_active"] = normalized["is_active"].fillna(False).astype(bool)
    else:
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


def price_table_summary(table: pd.DataFrame) -> dict[str, Any]:
    normalized = normalize_price_table(table)
    invalid_band = normalized["carat_band_to"] <= normalized["carat_band_from"]
    colors = sorted([value for value in normalized["color"].dropna().astype(str).unique() if value])
    clarities = sorted([value for value in normalized["clarity"].dropna().astype(str).unique() if value])
    return {
        "total_rows": int(len(normalized)),
        "active_rows": int(normalized["is_active"].sum()),
        "inactive_rows": int((~normalized["is_active"]).sum()),
        "rows_with_base_price_zero": int((normalized["base_price_usd_per_carat"] == 0).sum()),
        "rows_with_missing_color": int((normalized["color"].astype(str).str.strip() == "").sum()),
        "rows_with_missing_clarity": int((normalized["clarity"].astype(str).str.strip() == "").sum()),
        "rows_with_invalid_carat_band": int(invalid_band.sum()),
        "unique_colors": ", ".join(colors) if colors else "—",
        "unique_clarities": ", ".join(clarities) if clarities else "—",
    }


def filter_price_table(table: pd.DataFrame) -> pd.DataFrame:
    normalized = normalize_price_table(table).reset_index(drop=True)
    normalized[ROW_ID_COLUMN] = normalized.index

    color_options = sorted([value for value in normalized["color"].dropna().astype(str).unique() if value])
    clarity_options = sorted([value for value in normalized["clarity"].dropna().astype(str).unique() if value])
    band_options = sorted(
        {
            f"{row.carat_band_from:g}–{row.carat_band_to:g}"
            for row in normalized.itertuples(index=False)
        }
    )

    c1, c2, c3 = st.columns(3)
    selected_colors = c1.multiselect("Filter color", color_options, default=[], key="index_table_filter_color")
    selected_clarities = c2.multiselect("Filter clarity", clarity_options, default=[], key="index_table_filter_clarity")
    selected_bands = c3.multiselect("Filter carat band", band_options, default=[], key="index_table_filter_band")

    c4, c5 = st.columns(2)
    active_filter = c4.selectbox("Filter is_active", ["All", "Active only", "Inactive only"], key="index_table_filter_active")
    zero_only = c5.checkbox("base_price = 0 only", value=False, key="index_table_filter_zero_only")

    filtered = normalized.copy()
    if selected_colors:
        filtered = filtered[filtered["color"].isin(selected_colors)]
    if selected_clarities:
        filtered = filtered[filtered["clarity"].isin(selected_clarities)]
    if selected_bands:
        band_labels = filtered.apply(lambda row: f"{row['carat_band_from']:g}–{row['carat_band_to']:g}", axis=1)
        filtered = filtered[band_labels.isin(selected_bands)]
    if active_filter == "Active only":
        filtered = filtered[filtered["is_active"]]
    elif active_filter == "Inactive only":
        filtered = filtered[~filtered["is_active"]]
    if zero_only:
        filtered = filtered[filtered["base_price_usd_per_carat"] == 0]

    return filtered


def merge_edited_table(full_table: pd.DataFrame, original_view: pd.DataFrame, edited_view: pd.DataFrame) -> pd.DataFrame:
    full = normalize_price_table(full_table).reset_index(drop=True)
    full[ROW_ID_COLUMN] = full.index
    edited = edited_view.copy()

    if ROW_ID_COLUMN not in edited.columns:
        edited[ROW_ID_COLUMN] = pd.NA

    original_ids = set(pd.to_numeric(original_view.get(ROW_ID_COLUMN, pd.Series(dtype=float)), errors="coerce").dropna().astype(int).tolist())
    edited_ids = set(pd.to_numeric(edited[ROW_ID_COLUMN], errors="coerce").dropna().astype(int).tolist())
    deleted_ids = original_ids - edited_ids
    if deleted_ids:
        full = full[~full[ROW_ID_COLUMN].isin(deleted_ids)].copy()

    for _, row in edited.iterrows():
        row_id = pd.to_numeric(pd.Series([row.get(ROW_ID_COLUMN)]), errors="coerce").iloc[0]
        row_values = {column: row.get(column, "") for column in PRICE_TABLE_TEMPLATE_COLUMNS}
        if pd.notna(row_id) and int(row_id) in full[ROW_ID_COLUMN].tolist():
            full.loc[full[ROW_ID_COLUMN] == int(row_id), PRICE_TABLE_TEMPLATE_COLUMNS] = [row_values[column] for column in PRICE_TABLE_TEMPLATE_COLUMNS]
        else:
            new_row = {ROW_ID_COLUMN: pd.NA, **row_values}
            full = pd.concat([full, pd.DataFrame([new_row])], ignore_index=True)

    return normalize_price_table(full[PRICE_TABLE_TEMPLATE_COLUMNS])


def render_admin_price_table() -> pd.DataFrame:
    st.markdown("### Admin Index / Price Table v0.2")
    st.warning(
        "Это внутренняя admin index / price table. Она не публикует catalog.json, "
        "не подтверждает цены и не включает checkout."
    )

    current_table = load_saved_price_table()
    summary = price_table_summary(current_table)
    st.markdown("#### Technical summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total rows", summary["total_rows"])
    m2.metric("Active rows", summary["active_rows"])
    m3.metric("Inactive rows", summary["inactive_rows"])
    m4.metric("Base price = 0", summary["rows_with_base_price_zero"])

    m5, m6, m7 = st.columns(3)
    m5.metric("Missing color", summary["rows_with_missing_color"])
    m6.metric("Missing clarity", summary["rows_with_missing_clarity"])
    m7.metric("Invalid carat band", summary["rows_with_invalid_carat_band"])
    st.caption(f"Colors: {summary['unique_colors']}")
    st.caption(f"Clarities: {summary['unique_clarities']}")

    st.markdown("#### Filters")
    filtered_table = filter_price_table(current_table)
    st.caption(f"Показано строк: {len(filtered_table)} из {len(current_table)}")

    edited_table = st.data_editor(
        filtered_table,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_order=PRICE_TABLE_TEMPLATE_COLUMNS,
        key="admin_index_price_table_editor",
        column_config={
            "base_price_usd_per_carat": st.column_config.NumberColumn("base_price_usd_per_carat", min_value=0, step=1),
            "carat_band_from": st.column_config.NumberColumn("carat_band_from", min_value=0.0, step=0.01),
            "carat_band_to": st.column_config.NumberColumn("carat_band_to", min_value=0.0, step=0.01),
            "is_active": st.column_config.CheckboxColumn("is_active"),
        },
    )

    if st.button("Save edited index table draft", type="secondary"):
        merged_table = merge_edited_table(current_table, filtered_table, edited_table)
        save_draft_price_table(merged_table)
        st.success("Edited index table draft сохранена в data/price_table.csv. Цены не подтверждены; catalog.json не опубликован.")
        current_table = load_saved_price_table()

    st.download_button(
        label="Скачать текущую admin index / price table Excel",
        data=price_table_to_excel_bytes(current_table),
        file_name="kurgin_admin_index_price_table.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded_file = st.file_uploader(
        "Загрузить draft index / price table Excel/CSV",
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

        if st.button("Save uploaded draft table", type="secondary"):
            save_draft_price_table(preview_table)
            st.success("Uploaded draft table сохранена в data/price_table.csv. catalog.json не опубликован; цены не подтверждены.")
            current_table = load_saved_price_table()

    return current_table
