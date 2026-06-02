from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from kurgin.config import CANONICAL_COLUMNS, SAMPLE_CSV_PATH

COLUMN_ALIASES = {
    "id": "stone_id",
    "stoneid": "stone_id",
    "stone_id": "stone_id",
    "sku": "stone_id",
    "lot": "stone_id",
    "lot_id": "stone_id",
    "supplier": "supplier",
    "vendor": "supplier",
    "origin": "origin",
    "country": "origin",
    "type": "type",
    "stone_type": "type",
    "gem": "type",
    "shape": "shape",
    "cut_shape": "shape",
    "carat": "carat",
    "ct": "carat",
    "weight": "carat",
    "color": "color",
    "colour": "color",
    "clarity": "clarity",
    "cut": "cut",
    "polish": "polish",
    "symmetry": "symmetry",
    "fluorescence": "fluorescence",
    "fluor": "fluorescence",
    "certificate": "certificate",
    "cert": "certificate",
    "lab": "certificate",
    "price": "price_usd",
    "price_usd": "price_usd",
    "usd": "price_usd",
    "availability": "availability",
    "status": "availability",
    "notes": "notes",
    "comment": "notes",
}


def _slug(value: object) -> str:
    text = str(value).strip().lower()
    allowed = []
    for char in text:
        allowed.append(char if char.isalnum() else "_")
    return "_".join("".join(allowed).split("_")).strip("_")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    mapped_columns = []
    for column in result.columns:
        key = _slug(column)
        mapped_columns.append(COLUMN_ALIASES.get(key, key))
    result.columns = mapped_columns
    result = result.loc[:, ~result.columns.duplicated()]
    return result


def load_sample_catalog() -> pd.DataFrame:
    return normalize_columns(pd.read_csv(SAMPLE_CSV_PATH))


def read_catalog(file: str | Path | BinaryIO) -> pd.DataFrame:
    if isinstance(file, (str, Path)):
        path = Path(file)
        suffix = path.suffix.lower()
        if suffix in {".xlsx", ".xls"}:
            return normalize_columns(pd.read_excel(path))
        if suffix == ".csv":
            return normalize_columns(pd.read_csv(path))
        raise ValueError(f"Unsupported file extension: {suffix}")

    name = getattr(file, "name", "uploaded.csv")
    suffix = Path(name).suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return normalize_columns(pd.read_excel(file))
    if suffix == ".csv":
        return normalize_columns(pd.read_csv(file))
    raise ValueError(f"Unsupported file extension: {suffix}")


def filter_catalog(
    df: pd.DataFrame,
    query: str = "",
    stone_type: str | None = None,
    availability: str | None = None,
    min_score: float = 0.0,
) -> pd.DataFrame:
    result = df.copy()

    if query:
        haystack = result.astype(str).agg(" ".join, axis=1).str.lower()
        result = result[haystack.str.contains(query.lower(), regex=False, na=False)]

    if stone_type and stone_type != "All":
        result = result[result.get("type", "").astype(str) == stone_type]

    if availability and availability != "All":
        result = result[result.get("availability", "").astype(str) == availability]

    if "kurgin_score" in result.columns:
        result = result[pd.to_numeric(result["kurgin_score"], errors="coerce").fillna(0) >= min_score]

    return result


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "KURGIN") -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        export = df.copy()
        export.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name[:31]]

        header_format = workbook.add_format({
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#0F766E",
            "border": 1,
        })
        number_format = workbook.add_format({"num_format": "#,##0.00"})
        money_format = workbook.add_format({"num_format": "$#,##0"})
        score_format = workbook.add_format({"num_format": "0.0"})

        for col_num, column in enumerate(export.columns):
            worksheet.write(0, col_num, column, header_format)
            width = max(12, min(32, int(export[column].astype(str).str.len().quantile(0.9)) + 2))
            worksheet.set_column(col_num, col_num, width)

            if column in {"price_usd"}:
                worksheet.set_column(col_num, col_num, 14, money_format)
            elif column in {"price_per_carat"}:
                worksheet.set_column(col_num, col_num, 16, number_format)
            elif column.endswith("_score") or column == "kurgin_score":
                worksheet.set_column(col_num, col_num, 14, score_format)

        worksheet.freeze_panes(1, 0)
        worksheet.autofilter(0, 0, max(len(export), 1), max(len(export.columns) - 1, 0))

    return output.getvalue()


def empty_template() -> pd.DataFrame:
    return pd.DataFrame(columns=CANONICAL_COLUMNS)
