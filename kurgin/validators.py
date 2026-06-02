from __future__ import annotations

from dataclasses import dataclass, asdict

import pandas as pd

from kurgin.config import REQUIRED_COLUMNS
from kurgin.formula import CERTIFICATE_SCORES, CLARITY_SCORES, COLOR_SCORES, FINISH_SCORES


@dataclass(frozen=True)
class DataIssue:
    severity: str
    column: str
    message: str
    affected_rows: str = ""


def _row_list(indexes: pd.Index, max_items: int = 12) -> str:
    rows = [str(int(i) + 2) for i in indexes[:max_items]]
    suffix = "..." if len(indexes) > max_items else ""
    return ", ".join(rows) + suffix


def validate_catalog(df: pd.DataFrame) -> list[DataIssue]:
    issues: list[DataIssue] = []

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            issues.append(DataIssue("error", column, "Required column is missing"))
            continue
        missing = df[column].isna() | (df[column].astype(str).str.strip() == "")
        if missing.any():
            issues.append(
                DataIssue("warning", column, "Empty values detected", _row_list(df.index[missing]))
            )

    if "stone_id" in df.columns:
        duplicated = df["stone_id"].astype(str).duplicated(keep=False)
        if duplicated.any():
            issues.append(
                DataIssue("error", "stone_id", "Duplicate stone IDs detected", _row_list(df.index[duplicated]))
            )

    for column in ["carat", "price_usd"]:
        if column in df.columns:
            numeric = pd.to_numeric(df[column], errors="coerce")
            invalid = numeric.isna() | (numeric <= 0)
            if invalid.any():
                issues.append(
                    DataIssue("error", column, "Values must be numeric and greater than zero", _row_list(df.index[invalid]))
                )

    grade_specs = {
        "color": COLOR_SCORES,
        "clarity": CLARITY_SCORES,
        "cut": FINISH_SCORES,
        "polish": FINISH_SCORES,
        "symmetry": FINISH_SCORES,
        "certificate": CERTIFICATE_SCORES,
    }
    for column, mapping in grade_specs.items():
        if column not in df.columns:
            continue
        values = df[column].fillna("").astype(str).str.strip().str.upper()
        invalid = (values != "") & ~values.isin(mapping.keys())
        if invalid.any():
            issues.append(
                DataIssue("info", column, "Non-standard values will use default score", _row_list(df.index[invalid]))
            )

    return issues


def issues_to_frame(issues: list[DataIssue]) -> pd.DataFrame:
    if not issues:
        return pd.DataFrame(columns=["severity", "column", "message", "affected_rows"])
    return pd.DataFrame([asdict(issue) for issue in issues])
