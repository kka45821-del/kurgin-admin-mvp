from io import BytesIO

import pandas as pd
import streamlit as st

from admin_io import load_stones

from .helpers import ensure_columns, safe_name
from .payments import batch_payment_rows


def excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            safe_sheet_name = str(sheet_name)[:31] or "Sheet"
            df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
    return out.getvalue()


def batch_stones(batch_number: str) -> pd.DataFrame:
    stones = load_stones()
    if stones.empty or "batch_number" not in stones.columns:
        return pd.DataFrame()
    return stones[stones["batch_number"].astype(str).eq(str(batch_number))].copy()


def detail_table(df: pd.DataFrame, date_column_name: str) -> pd.DataFrame:
    columns = {
        "batch_number": "номер партии",
        "upload_date": date_column_name,
        "report_number": "номер сертификата",
        "shape": "огранка",
        "carat": "карат",
        "color": "цвет",
        "clarity": "чистота",
    }
    if df.empty:
        return pd.DataFrame(columns=list(columns.values()))
    result = ensure_columns(df, list(columns.keys()))
    return result[list(columns.keys())].rename(columns=columns)


def batch_report_parts(batch_number: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    batch_df = batch_stones(batch_number)
    payments = batch_payment_rows(batch_number)
    if not batch_df.empty and "current_status" in batch_df.columns:
        status = batch_df["current_status"].astype(str).str.lower()
        on_site = batch_df[~status.isin(["sold", "removed", "removed_from_sale", "unavailable", "hidden"])]
        sold = batch_df[status.eq("sold")]
        removed = batch_df[status.isin(["removed", "removed_from_sale", "unavailable", "hidden"])]
    else:
        on_site = batch_df
        sold = pd.DataFrame()
        removed = pd.DataFrame()
    return on_site, sold, removed, payments


def render_table_download(label: str, df: pd.DataFrame, batch_number: str, suffix: str):
    st.download_button(
        label,
        data=excel_bytes({suffix: df}),
        file_name=f"KURGIN_{safe_name(batch_number)}_{safe_name(suffix)}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"download_{suffix}_{batch_number}",
    )
