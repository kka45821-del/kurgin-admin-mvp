from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

COLOR_SCORES = {
    "D": 10.0, "E": 9.5, "F": 9.0, "G": 8.2, "H": 7.4, "I": 6.5, "J": 5.6,
    "K": 4.8, "L": 4.0, "M": 3.2, "N": 2.6, "O": 2.2, "P": 1.8,
    "BLUE": 8.5, "PINK": 8.5, "YELLOW": 7.5, "GREEN": 7.0, "RED": 9.0,
}
CLARITY_SCORES = {
    "FL": 10.0, "IF": 9.7, "VVS1": 9.3, "VVS2": 8.8, "VS1": 8.2, "VS2": 7.6,
    "SI1": 6.6, "SI2": 5.5, "I1": 4.0, "I2": 2.5, "I3": 1.0,
    "EYE CLEAN": 7.8, "INCLUDED": 4.0,
}
FINISH_SCORES = {
    "EXCELLENT": 10.0, "EX": 10.0, "IDEAL": 10.0,
    "VERY GOOD": 8.5, "VG": 8.5,
    "GOOD": 7.0, "G": 7.0,
    "FAIR": 4.8, "POOR": 2.5,
}
FLUORESCENCE_SCORES = {
    "NONE": 10.0, "N": 10.0,
    "FAINT": 9.0, "SLIGHT": 8.8,
    "MEDIUM": 7.5, "STRONG": 5.5, "VERY STRONG": 4.0,
}
CERTIFICATE_SCORES = {
    "GIA": 10.0, "HRD": 8.8, "IGI": 8.4, "AGS": 8.0, "GCAL": 7.8,
    "SSEF": 9.2, "GUBELIN": 9.2, "GRS": 8.6, "AIGS": 7.8,
    "LOCAL": 5.5, "NONE": 3.0, "": 3.0,
}
AVAILABILITY_RISK = {
    "AVAILABLE": 0.0,
    "IN STOCK": 0.0,
    "RESERVED": 10.0,
    "ON MEMO": 8.0,
    "PENDING": 12.0,
    "SOLD": 35.0,
    "UNAVAILABLE": 35.0,
}


def _clean_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return str(value).strip().upper()


def _map_score(series: pd.Series, mapping: dict[str, float], default: float = 6.0) -> pd.Series:
    return series.map(lambda value: mapping.get(_clean_text(value), default)).astype(float)


def _numeric(series: pd.Series, default: float = 0.0) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(default).astype(float)


def ensure_scoring_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    defaults: dict[str, Any] = {
        "stone_id": "",
        "supplier": "",
        "origin": "",
        "type": "Diamond",
        "shape": "",
        "carat": 0.0,
        "color": "",
        "clarity": "",
        "cut": "",
        "polish": "",
        "symmetry": "",
        "fluorescence": "None",
        "certificate": "",
        "price_usd": 0.0,
        "availability": "Available",
        "notes": "",
    }
    for column, default in defaults.items():
        if column not in result.columns:
            result[column] = default
    return result


def score_catalog(df: pd.DataFrame) -> pd.DataFrame:
    """Return a scored copy of a catalog.

    Score model:
    - quality_score: color, clarity, cut, polish, symmetry, fluorescence and certificate.
    - value_score: price per carat relative to peers by stone type.
    - risk_score: availability, certificate confidence and data completeness penalties.
    - kurgin_score: weighted composite 0-100.

    This is an MVP formula intentionally isolated here for easy calibration.
    """
    result = ensure_scoring_columns(df)

    carat = _numeric(result["carat"]).clip(lower=0.01)
    price = _numeric(result["price_usd"]).clip(lower=0.0)
    price_per_carat = (price / carat).replace([np.inf, -np.inf], np.nan).fillna(0.0)

    color = _map_score(result["color"], COLOR_SCORES)
    clarity = _map_score(result["clarity"], CLARITY_SCORES)
    cut = _map_score(result["cut"], FINISH_SCORES)
    polish = _map_score(result["polish"], FINISH_SCORES)
    symmetry = _map_score(result["symmetry"], FINISH_SCORES)
    fluorescence = _map_score(result["fluorescence"], FLUORESCENCE_SCORES, default=8.0)
    certificate = _map_score(result["certificate"], CERTIFICATE_SCORES, default=5.5)

    quality_score = (
        0.18 * color
        + 0.20 * clarity
        + 0.18 * cut
        + 0.10 * polish
        + 0.10 * symmetry
        + 0.10 * fluorescence
        + 0.14 * certificate
    ) * 10.0

    result["_type_for_peer"] = result["type"].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    result["_price_per_carat_num"] = price_per_carat
    peer_ppc = result.groupby("_type_for_peer")["_price_per_carat_num"].transform(
        lambda values: values[values > 0].median()
    )

    global_ppc = float(price_per_carat[price_per_carat > 0].median()) if (price_per_carat > 0).any() else 1.0
    peer_ppc = peer_ppc.fillna(global_ppc).replace(0, global_ppc)
    relative_value = peer_ppc / price_per_carat.replace(0, np.nan)
    value_score = (50.0 + 24.0 * np.log(relative_value)).replace([np.inf, -np.inf], np.nan).fillna(50.0)
    value_score = value_score.clip(lower=0.0, upper=100.0)

    availability_penalty = result["availability"].map(
        lambda value: AVAILABILITY_RISK.get(_clean_text(value), 8.0)
    )
    missing_penalty = (
        result[["carat", "price_usd", "certificate", "color", "clarity", "cut"]]
        .isna()
        .sum(axis=1)
        .astype(float)
        * 3.0
    )
    certificate_penalty = (10.0 - certificate).clip(lower=0.0) * 1.5
    risk_score = (100.0 - availability_penalty - missing_penalty - certificate_penalty).clip(0.0, 100.0)

    kurgin_score = (0.55 * quality_score + 0.30 * value_score + 0.15 * risk_score).clip(0.0, 100.0)

    result["carat"] = carat.round(2)
    result["price_usd"] = price.round(2)
    result["price_per_carat"] = price_per_carat.round(2)
    result["quality_score"] = quality_score.round(1)
    result["value_score"] = value_score.round(1)
    result["risk_score"] = risk_score.round(1)
    result["kurgin_score"] = kurgin_score.round(1)
    result["rating"] = pd.cut(
        result["kurgin_score"],
        bins=[-1, 54.9, 69.9, 84.9, 100],
        labels=["Risk", "Review", "Strong", "Premium"],
    ).astype(str)

    return result.drop(columns=["_type_for_peer", "_price_per_carat_num"], errors="ignore")


def score_single(record: dict[str, Any]) -> dict[str, Any]:
    frame = pd.DataFrame([record])
    return score_catalog(frame).iloc[0].to_dict()


def score_summary(df: pd.DataFrame) -> dict[str, float | int]:
    if df.empty:
        return {"count": 0, "avg_score": 0.0, "premium": 0, "median_ppc": 0.0}
    scored = score_catalog(df) if "kurgin_score" not in df.columns else df
    return {
        "count": int(len(scored)),
        "avg_score": float(scored["kurgin_score"].mean().round(1)),
        "premium": int((scored["rating"] == "Premium").sum()),
        "median_ppc": float(scored["price_per_carat"].median().round(2)),
    }
