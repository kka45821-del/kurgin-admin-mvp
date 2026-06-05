from __future__ import annotations

from pathlib import Path
import pandas as pd

from .paths import RAW_DIR


def _read_raw(import_id: str, filename: str) -> pd.DataFrame:
    path = RAW_DIR / str(import_id) / filename
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame()


def _filter_by_stone(df: pd.DataFrame, report_number: str, stock_number: str) -> pd.DataFrame:
    if df.empty:
        return df
    result = df
    if report_number and "Report #" in df.columns:
        result = df[df["Report #"].astype(str) == str(report_number)]
        if not result.empty:
            return result
    if stock_number and "Stock #" in df.columns:
        result = df[df["Stock #"].astype(str) == str(stock_number)]
        if not result.empty:
            return result
    return pd.DataFrame()


def get_stone_raw(import_id: str, report_number: str, stock_number: str) -> dict[str, pd.DataFrame]:
    results = _filter_by_stone(_read_raw(import_id, "results_full.csv"), report_number, stock_number)
    details = _filter_by_stone(_read_raw(import_id, "details_full.csv"), report_number, stock_number)
    issues = _filter_by_stone(_read_raw(import_id, "issues_full.csv"), report_number, stock_number)
    return {"results": results, "details": details, "issues": issues}


def transpose_one_row(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Поле", "Значение"])
    row = df.iloc[0].to_dict()
    return pd.DataFrame([{"Поле": k, "Значение": v} for k, v in row.items()])
