import pandas as pd


def bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y", "да"])


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = df.copy()
    for col in columns:
        if col not in result.columns:
            result[col] = ""
    return result


def rub(value) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0
    return f"{amount:,.0f} ₽".replace(",", " ")


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(value))[:80]


def batch_metadata(batch_number: str, batches: pd.DataFrame) -> dict:
    if batches.empty or "batch_number" not in batches.columns:
        return {}
    rows = batches[batches["batch_number"].astype(str).eq(str(batch_number))]
    if rows.empty:
        return {}
    return rows.iloc[0].to_dict()
