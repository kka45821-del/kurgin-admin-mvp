from __future__ import annotations

from datetime import datetime
from io import BytesIO
import pandas as pd

from .schema import REQUIRED_SHEETS, STONES_COLUMNS
from .storage import read_stones


def _clean_value(value):
    if pd.isna(value):
        return ""
    return value


def _str(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _num(value):
    try:
        if pd.isna(value) or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _first_existing(row, names: list[str]):
    for name in names:
        if name in row.index:
            value = row.get(name, "")
            if not pd.isna(value) and str(value).strip():
                return value
    return ""


def _safe_cell_text(value) -> str:
    if pd.isna(value):
        return ""
    cell = str(value).strip()
    if not cell or cell.lower() == "nan":
        return ""
    return cell


def _is_colored_future_section(color_value: str) -> bool:
    text = (color_value or "").upper()
    fancy_words = ["FANCY", "PINK", "BLUE", "GREEN", "YELLOW", "ORANGE", "PURPLE", "RED", "BROWN"]
    if text in list("DEFGHIJKLMNOPQRSTUVWXYZ"):
        return False
    return any(word in text for word in fancy_words)


def get_template_version(system_df: pd.DataFrame) -> str:
    if system_df is None or system_df.empty:
        return ""

    candidates = ["Formula Output Version", "Engine Version", "Output Version", "Template Version"]

    for _, row in system_df.iterrows():
        values = [_safe_cell_text(v) for v in row.tolist()]
        values = [v for v in values if v]
        if not values:
            continue
        joined = " ".join(values)
        if any(candidate in joined for candidate in candidates):
            return " | ".join(values[:4])

    for _, row in system_df.iterrows():
        values = [_safe_cell_text(v) for v in row.tolist()]
        values = [v for v in values if v]
        if values:
            return " | ".join(values[:4])

    return ""


def read_workbook(uploaded_bytes: bytes) -> tuple[dict[str, pd.DataFrame], list[str]]:
    errors: list[str] = []
    try:
        xls = pd.ExcelFile(BytesIO(uploaded_bytes))
    except Exception as exc:
        return {}, [f"Файл не читается как Excel: {exc}"]

    missing = [sheet for sheet in REQUIRED_SHEETS if sheet not in xls.sheet_names]
    if missing:
        return {}, ["Нет обязательных листов: " + ", ".join(missing)]

    data: dict[str, pd.DataFrame] = {}
    for sheet in REQUIRED_SHEETS:
        try:
            data[sheet] = pd.read_excel(xls, sheet)
        except Exception as exc:
            errors.append(f"Не удалось прочитать лист {sheet}: {exc}")

    results = data.get("Results", pd.DataFrame())
    if results.empty:
        errors.append("В листе Results нет строк с камнями.")

    required_cols = []
    if "Weight" not in results.columns:
        required_cols.append("Weight")
    if "Shape" not in results.columns:
        required_cols.append("Shape")
    if required_cols:
        errors.append("Нет ключевых колонок: " + ", ".join(required_cols))

    return data, errors


def build_details_lookup(details_df: pd.DataFrame) -> pd.DataFrame:
    if details_df is None or details_df.empty:
        return pd.DataFrame(columns=["Report #", "Stock #", "KURGIN Import ID"])
    cols = [c for c in ["Report #", "Stock #", "KURGIN Import ID"] if c in details_df.columns]
    lookup = details_df[cols].copy()
    for col in ["Report #", "Stock #", "KURGIN Import ID"]:
        if col not in lookup.columns:
            lookup[col] = ""
    return lookup.drop_duplicates()


def build_issues_lookup(issues_df: pd.DataFrame) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    if issues_df is None or issues_df.empty:
        return lookup

    for _, row in issues_df.iterrows():
        report = _str(row.get("Report #", ""))
        issue_type = _str(row.get("Issue Type", ""))
        problem = _str(row.get("Problem", ""))
        recommendation = _str(row.get("recommendation_ru", ""))
        parts = [p for p in [issue_type, problem, recommendation] if p]
        if report:
            lookup.setdefault(report, []).append(" | ".join(parts))
    return lookup


def classify_section(weight, color_value: str) -> tuple[str, str, bool]:
    w = _num(weight)
    if w is None:
        return "", "Нет веса — строка не сохраняется.", False
    if w < 1.0:
        return "", "Вне текущей версии: меньше 1.00 ct.", False
    if _is_colored_future_section(color_value):
        return "", "Вне текущей версии: цветной / будущий раздел.", False
    if 1.0 <= w < 3.0:
        return "main", "Основной каталог", True
    if w >= 3.0:
        return "large", "Крупные камни", True
    return "", "Вне текущей версии.", False


def normalize_stones(results_df, details_df, issues_df, shipment, import_id, original_filename):
    details_lookup = build_details_lookup(details_df)
    issues_lookup = build_issues_lookup(issues_df)
    existing_stones = read_stones()
    existing_ids = set(existing_stones.get("stone_id", pd.Series(dtype=str)).astype(str).tolist())
    existing_reports = set(existing_stones.get("report_number", pd.Series(dtype=str)).astype(str).tolist())

    rows_saved, rows_not_saved = [], []
    stats = {"total": len(results_df), "saved": 0, "not_saved": 0, "round": 0, "not_round": 0, "main": 0, "large": 0, "warnings": 0, "conflicts": 0}

    for idx, row in results_df.iterrows():
        report = _str(row.get("Report #", ""))
        stock = _str(row.get("Stock #", ""))
        shape = _str(row.get("Shape", "")).upper()
        weight = row.get("Weight", "")
        color = _str(row.get("Color", ""))
        section, section_label, should_save = classify_section(weight, color)

        if shape == "ROUND":
            stats["round"] += 1
            score_status = "calculated"
            kurgin_score = _clean_value(row.get("Kurgin Score", ""))
        else:
            stats["not_round"] += 1
            score_status = "not_available_for_shape"
            kurgin_score = ""

        if section == "main":
            stats["main"] += 1
        elif section == "large":
            stats["large"] += 1

        kurgin_import_id = ""
        if report and not details_lookup.empty:
            match = details_lookup[details_lookup["Report #"].astype(str) == report]
            if not match.empty:
                kurgin_import_id = _str(match.iloc[0].get("KURGIN Import ID", ""))
        if not kurgin_import_id and stock and not details_lookup.empty:
            match = details_lookup[details_lookup["Stock #"].astype(str) == stock]
            if not match.empty:
                kurgin_import_id = _str(match.iloc[0].get("KURGIN Import ID", ""))

        stone_id = kurgin_import_id or (f"KRG-{report}" if report else f"KRG-{import_id}-{idx+1:04d}")

        warning_messages = issues_lookup.get(report, [])
        validation_status = "warning" if warning_messages else "ok"
        validation_message = " || ".join(warning_messages) if warning_messages else ""
        if warning_messages:
            stats["warnings"] += 1

        conflict_messages = []
        if report and report in existing_reports:
            conflict_messages.append("Совпадает Report #")

        if conflict_messages:
            stats["conflicts"] += 1
            validation_status = "blocking_error"
            validation_message = (validation_message + " || " if validation_message else "") + "; ".join(conflict_messages)

        base = {
            "stone_id": stone_id,
            "kurgin_import_id": kurgin_import_id,
            "report_number": report,
            "stock_number": stock,
            "lab": _str(row.get("Lab", "")),
            "shape": shape,
            "weight": _clean_value(weight),
            "color": color,
            "clarity": _str(row.get("Clarity", "")),
            "cut": _str(row.get("Cut", "")),
            "polish": _str(row.get("Polish", "")),
            "symmetry": _str(row.get("Symmetry", "")),
            "fluorescence": _str(row.get("Fluorescence", "")),
            "measurements": _str(row.get("Measurements", "")),
            "min_diameter": _clean_value(_first_existing(row, ["MinDiameter", "Min Diameter", "Min Diameter MM", "min_diameter"])),
            "max_diameter": _clean_value(_first_existing(row, ["MaxDiameter", "Max Diameter", "Max Diameter MM", "max_diameter"])),
            "depth_mm": _clean_value(_first_existing(row, ["DepthMM", "Depth MM", "Depth Mm", "depth_mm"])),
            "kurgin_score": kurgin_score,
            "score_status": score_status,
            "catalog_section": section,
            "status": "draft",
            "availability_status": "in_stock",
            "shipment_id": import_id,
            "import_id": import_id,
            "source_file": original_filename,
            "imported_at": datetime.now().isoformat(timespec="seconds"),
            "supplier_name": shipment.get("supplier_name", ""),
            "shipment_date": shipment.get("shipment_date", ""),
            "currency": shipment.get("currency", ""),
            "published_price": "",
            "admin_note": "",
            "validation_status": validation_status,
            "validation_message": validation_message,
            "warning_status": "warning" if warning_messages else "",
            "warning_message": " || ".join(warning_messages),
        }

        if should_save and not conflict_messages:
            rows_saved.append(base)
        else:
            out = base.copy()
            out["not_saved_reason"] = validation_message if conflict_messages else section_label
            rows_not_saved.append(out)

    saved_df = pd.DataFrame(rows_saved)
    not_saved_df = pd.DataFrame(rows_not_saved)

    for col in STONES_COLUMNS:
        if col not in saved_df.columns:
            saved_df[col] = ""
    if not saved_df.empty:
        saved_df = saved_df[STONES_COLUMNS]

    stats["saved"] = len(saved_df)
    stats["not_saved"] = len(not_saved_df)
    return saved_df, not_saved_df, stats


def split_conflicts(saved_df: pd.DataFrame, not_saved_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return conflict rows and non-conflict not-saved rows."""
    if not_saved_df is None or not_saved_df.empty:
        return pd.DataFrame(), pd.DataFrame()
    if "not_saved_reason" not in not_saved_df.columns:
        return pd.DataFrame(), not_saved_df
    mask = not_saved_df["not_saved_reason"].astype(str).str.contains("Report #", case=False, na=False)
    return not_saved_df[mask].copy(), not_saved_df[~mask].copy()


def apply_report_corrections_to_results(results_df: pd.DataFrame, corrections: dict[str, str]) -> pd.DataFrame:
    """Apply Report # corrections to a Results dataframe before normalizing stones.

    corrections maps original Report # -> corrected Report #.
    """
    if not corrections or "Report #" not in results_df.columns:
        return results_df
    corrected = results_df.copy()
    corrected["Report #"] = corrected["Report #"].astype(str).apply(lambda x: corrections.get(x, x))
    return corrected
