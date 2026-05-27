from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd


PRICED_BATCH_SECTIONS = {"main", "large"}
REQUEST_PRICE_STATUSES = {"", "missing", "request_price", "score_required", "future_scope", "needs_review", "index_pending", "index_suggested"}
ROUND_SHAPES = {"round", "round brilliant", "round brilliant cut", "rbc", "круг"}


def read_price_table(uploaded_file: Any) -> pd.DataFrame:
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


def format_tuple(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "; ".join(str(item) for item in value if str(item))
    return str(value)


def stone_value(stone: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = stone.get(key)
        if value not in (None, ""):
            return value
    return default


def text_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series([""] * len(df), index=df.index, dtype="object")
    return df[column].fillna("").astype(str).str.strip()


def number_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series([0.0] * len(df), index=df.index, dtype="float")
    return pd.to_numeric(df[column], errors="coerce").fillna(0)


def bool_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series([False] * len(df), index=df.index, dtype="bool")
    values = df[column]
    if values.dtype == bool:
        return values.fillna(False).astype(bool)
    return values.fillna("").astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y", "да"])


def normalize_section_series(section: pd.Series) -> pd.Series:
    aliases = {
        "main": "main",
        "основной": "main",
        "основной каталог": "main",
        "large": "large",
        "крупные": "large",
        "medium": "medium",
        "средние": "medium",
        "small": "small",
        "мелкие": "small",
        "colored": "colored",
        "цветные": "colored",
        "side": "side",
        "боковые": "side",
        "pairs": "pairs",
        "парные": "pairs",
        "exclusive": "exclusive",
        "эксклюзив": "exclusive",
    }
    return section.fillna("").astype(str).str.strip().str.lower().map(lambda value: aliases.get(value, value))


def effective_section(stones: pd.DataFrame) -> pd.Series:
    section = normalize_section_series(text_series(stones, "section"))
    carat = number_series(stones, "carat")
    inferred = pd.Series([""] * len(stones), index=stones.index, dtype="object")
    inferred = inferred.mask((carat >= 1) & (carat < 3), "main")
    inferred = inferred.mask(carat >= 3, "large")
    return section.mask(section.eq(""), inferred)


def effective_section_for_stone_dict(stone_dict: dict[str, Any]) -> str:
    raw_section = stone_dict.get("section")
    raw_text = "" if raw_section is None else str(raw_section).strip()
    if raw_text and raw_text.lower() not in {"nan", "none", "null"}:
        return raw_text

    carat = pd.to_numeric(pd.Series([stone_dict.get("carat")]), errors="coerce").fillna(0).iloc[0]
    if 1.0 <= float(carat) < 3.0:
        return "main"
    if float(carat) >= 3.0:
        return "large"
    return ""


def is_colored_mask(stones: pd.DataFrame) -> pd.Series:
    is_colored = bool_series(stones, "is_colored")
    color_type = text_series(stones, "color_type").ne("")
    color_hue = text_series(stones, "color_hue").ne("")
    color_intensity = text_series(stones, "color_intensity").ne("")
    return is_colored | color_type | color_hue | color_intensity


def is_round_mask(stones: pd.DataFrame) -> pd.Series:
    return text_series(stones, "shape").str.lower().isin(ROUND_SHAPES)


def count_status(summary: pd.Series, *statuses: str) -> int:
    return int(sum(int(summary.get(status, 0)) for status in statuses))
