from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import json
import shutil
import pandas as pd

from .paths import ensure_dirs, BACKUPS_DIR, STONES_FILE, SHIPMENTS_FILE, IMPORT_LOG_FILE, RAW_DIR, PAYMENTS_FILE, PRICE_SUPPLIER_FILE, PRICE_EXPENSE_RATES_FILE, PRICE_MARGINS_FILE, PRICE_SCORE_COEFFICIENTS_FILE, CURRENCY_RATES_FILE, CATALOG_SECTIONS_FILE
from .schema import STONES_COLUMNS, SHIPMENTS_COLUMNS, IMPORT_LOG_COLUMNS, PAYMENTS_COLUMNS, PRICE_SUPPLIER_COLUMNS, PRICE_EXPENSE_RATES_COLUMNS, PRICE_MARGINS_COLUMNS, PRICE_SCORE_COEFFICIENTS_COLUMNS, CURRENCY_RATES_COLUMNS, WEIGHT_RANGES, PRICE_COLORS, PRICE_CLARITIES, CATALOG_SECTIONS_COLUMNS, PRICE_WRITE_STONE_COLUMNS


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def ensure_csv(path: Path, columns: list[str]) -> None:
    ensure_dirs()
    if not path.exists():
        pd.DataFrame(columns=columns).to_csv(path, index=False)


def ensure_data_files() -> None:
    ensure_csv(STONES_FILE, STONES_COLUMNS)
    ensure_csv(SHIPMENTS_FILE, SHIPMENTS_COLUMNS)
    ensure_csv(IMPORT_LOG_FILE, IMPORT_LOG_COLUMNS)
    ensure_csv(PAYMENTS_FILE, PAYMENTS_COLUMNS)
    ensure_price_files()
    ensure_catalog_sections()


def read_csv_safe(path: Path, columns: list[str]) -> pd.DataFrame:
    ensure_csv(path, columns)
    try:
        df = pd.read_csv(path, dtype=str).fillna("")
    except Exception:
        df = pd.DataFrame(columns=columns)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns + [c for c in df.columns if c not in columns]]


def read_stones() -> pd.DataFrame:
    return read_csv_safe(STONES_FILE, STONES_COLUMNS)


def read_shipments() -> pd.DataFrame:
    return read_csv_safe(SHIPMENTS_FILE, SHIPMENTS_COLUMNS)


def read_import_log() -> pd.DataFrame:
    return read_csv_safe(IMPORT_LOG_FILE, IMPORT_LOG_COLUMNS)

def read_payments() -> pd.DataFrame:
    return read_csv_safe(PAYMENTS_FILE, PAYMENTS_COLUMNS)


def backup_existing_files(label: str) -> Path:
    ensure_dirs()
    backup_dir = BACKUPS_DIR / f"{now_stamp()}_{label}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for path in [STONES_FILE, SHIPMENTS_FILE, IMPORT_LOG_FILE, PAYMENTS_FILE, CATALOG_SECTIONS_FILE, PRICE_SUPPLIER_FILE, PRICE_EXPENSE_RATES_FILE, PRICE_MARGINS_FILE, PRICE_SCORE_COEFFICIENTS_FILE, CURRENCY_RATES_FILE]:
        if path.exists():
            shutil.copy2(path, backup_dir / path.name)

    raw_snapshot = backup_dir / "raw_snapshot"
    if RAW_DIR.exists():
        shutil.copytree(RAW_DIR, raw_snapshot, dirs_exist_ok=True)

    return backup_dir


def atomic_write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp_path, index=False)
    tmp_path.replace(path)


def append_csv(existing_path: Path, columns: list[str], new_df: pd.DataFrame) -> pd.DataFrame:
    existing = read_csv_safe(existing_path, columns)
    combined = pd.concat([existing, new_df], ignore_index=True)
    atomic_write_csv(combined, existing_path)
    return combined


def generate_import_id() -> str:
    ensure_data_files()
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"IMP-{today}-"

    used = []
    shipments = read_shipments()
    log = read_import_log()
    if "import_id" in shipments.columns:
        used += shipments["import_id"].dropna().astype(str).tolist()
    if "import_id" in log.columns:
        used += log["import_id"].dropna().astype(str).tolist()

    nums = []
    for item in used:
        if item.startswith(prefix):
            tail = item.replace(prefix, "", 1)
            if tail.isdigit():
                nums.append(int(tail))

    next_num = max(nums) + 1 if nums else 1
    return f"{prefix}{next_num:03d}"


def update_stone_admin_fields(
    stone_id: str,
    catalog_section: str,
    status: str,
    availability_status: str,
    admin_note: str,
    validation_message: str,
) -> dict:
    ensure_data_files()
    backup_dir = backup_existing_files(f"before_update_stone_{stone_id}")

    stones = read_stones()
    mask = stones["stone_id"].astype(str) == str(stone_id)
    if not mask.any():
        return {"updated": False, "message": "Камень не найден.", "backup_dir": str(backup_dir)}

    stones.loc[mask, "catalog_section"] = catalog_section
    stones.loc[mask, "status"] = status
    stones.loc[mask, "availability_status"] = availability_status
    stones.loc[mask, "admin_note"] = admin_note
    stones.loc[mask, "validation_message"] = validation_message

    atomic_write_csv(stones, STONES_FILE)

    return {"updated": True, "message": "Камень сохранён.", "backup_dir": str(backup_dir)}



def update_shipment_fields(shipment_id: str, data: dict) -> dict:
    ensure_data_files()
    backup_dir = backup_existing_files(f"before_update_shipment_{shipment_id}")
    shipments = read_shipments()
    mask = shipments["shipment_id"].astype(str) == str(shipment_id)
    if not mask.any():
        return {"updated": False, "message": "Поставка не найдена.", "backup_dir": str(backup_dir)}
    for key, value in data.items():
        if key in shipments.columns:
            shipments.loc[mask, key] = value
    atomic_write_csv(shipments, SHIPMENTS_FILE)
    return {"updated": True, "message": "Поставка сохранена.", "backup_dir": str(backup_dir)}


def add_payment(shipment_id: str, payment_date: str, amount, currency: str, comment: str) -> dict:
    ensure_data_files()
    backup_dir = backup_existing_files(f"before_add_payment_{shipment_id}")
    payment_id = "PAY-" + datetime.now().strftime("%Y%m%d%H%M%S")
    row = pd.DataFrame([{
        "payment_id": payment_id,
        "shipment_id": shipment_id,
        "payment_date": payment_date,
        "amount": amount,
        "currency": currency,
        "comment": comment,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }])
    append_csv(PAYMENTS_FILE, PAYMENTS_COLUMNS, row)
    return {"payment_id": payment_id, "backup_dir": str(backup_dir)}


def delete_payment(payment_id: str) -> dict:
    ensure_data_files()
    backup_dir = backup_existing_files(f"before_delete_payment_{payment_id}")
    payments = read_payments()
    before = len(payments)
    payments = payments[payments["payment_id"].astype(str) != str(payment_id)]
    atomic_write_csv(payments, PAYMENTS_FILE)
    return {"deleted": before - len(payments), "backup_dir": str(backup_dir)}

def get_shipment_delete_preview(import_id: str) -> dict:
    stones = read_stones()
    shipments = read_shipments()
    log = read_import_log()
    payments = read_payments()
    raw_dir = RAW_DIR / import_id

    return {
        "import_id": import_id,
        "stones_count": int((stones["shipment_id"].astype(str) == import_id).sum()) if "shipment_id" in stones.columns else 0,
        "shipment_rows": int((shipments["shipment_id"].astype(str) == import_id).sum()) if "shipment_id" in shipments.columns else 0,
        "log_rows": int((log["import_id"].astype(str) == import_id).sum()) if "import_id" in log.columns else 0,
        "payments_count": int((payments["shipment_id"].astype(str) == import_id).sum()) if "shipment_id" in payments.columns else 0,
        "raw_dir_exists": raw_dir.exists(),
        "raw_dir": str(raw_dir),
    }


def delete_shipment_completely(import_id: str) -> dict:
    ensure_data_files()
    backup_dir = backup_existing_files(f"before_delete_{import_id}")

    stones = read_stones()
    shipments = read_shipments()
    log = read_import_log()
    payments = read_payments()

    stones_before = len(stones)
    shipments_before = len(shipments)
    log_before = len(log)
    payments_before = len(payments)

    if "shipment_id" in stones.columns:
        stones = stones[stones["shipment_id"].astype(str) != import_id]
    if "shipment_id" in shipments.columns:
        shipments = shipments[shipments["shipment_id"].astype(str) != import_id]
    if "import_id" in log.columns:
        log = log[log["import_id"].astype(str) != import_id]
    if "shipment_id" in payments.columns:
        payments = payments[payments["shipment_id"].astype(str) != import_id]

    atomic_write_csv(stones, STONES_FILE)
    atomic_write_csv(shipments, SHIPMENTS_FILE)
    atomic_write_csv(log, IMPORT_LOG_FILE)
    atomic_write_csv(payments, PAYMENTS_FILE)

    raw_dir = RAW_DIR / import_id
    raw_deleted = False
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
        raw_deleted = True

    return {
        "backup_dir": str(backup_dir),
        "stones_deleted": stones_before - len(stones),
        "shipment_rows_deleted": shipments_before - len(shipments),
        "log_rows_deleted": log_before - len(log),
        "payments_deleted": payments_before - len(payments),
        "raw_deleted": raw_deleted,
    }


def _safe_scalar(value) -> str:
    """Return a single safe string value for assignment into a CSV-backed cell."""
    if isinstance(value, pd.Series):
        value = value.iloc[0] if not value.empty else ""
    if isinstance(value, (list, tuple, dict, set)):
        value = str(value)
    if pd.isna(value):
        return ""
    return str(value)


def update_existing_stones_from_import(update_df: pd.DataFrame, import_id: str, source_file: str) -> dict:
    """Update existing stones by report_number using new Excel-derived data.

    Manual/admin fields are preserved:
    published_price, status, availability_status, catalog_section, admin_note, price_comment.
    """
    ensure_data_files()
    backup_dir = backup_existing_files(f"before_update_existing_{import_id}")

    stones = read_stones()
    if stones.empty or update_df.empty:
        return {"updated": 0, "backup_dir": str(backup_dir)}

    manual_fields = {
        "published_price",
        "status",
        "availability_status",
        "catalog_section",
        "admin_note",
        "price_comment",
        *PRICE_WRITE_STONE_COLUMNS,
    }

    update_allowed = [
        col for col in update_df.columns
        if col in stones.columns
        and col not in manual_fields
        and col not in {"stone_id"}
    ]

    updated_reports = set()
    for _, new_row in update_df.iterrows():
        report = str(new_row.get("report_number", "")).strip()
        if not report:
            continue

        matching_indexes = stones.index[stones["report_number"].astype(str) == report].tolist()
        if not matching_indexes:
            continue

        for row_index in matching_indexes:
            for col in update_allowed:
                stones.at[row_index, col] = _safe_scalar(new_row.get(col, ""))

            stones.at[row_index, "updated_at"] = datetime.now().isoformat(timespec="seconds")
            stones.at[row_index, "updated_import_id"] = str(import_id)
            stones.at[row_index, "last_source_file"] = str(source_file)

        updated_reports.add(report)

    atomic_write_csv(stones, STONES_FILE)
    return {"updated": len(updated_reports), "backup_dir": str(backup_dir)}



def ensure_catalog_sections() -> None:
    ensure_dirs()
    if not CATALOG_SECTIONS_FILE.exists():
        df = pd.DataFrame([
            {"section_id": "main", "section_name_ru": "Основной каталог", "section_name_en": "Main Catalog", "is_public": "true", "sort_order": "1", "comment": ""},
            {"section_id": "large", "section_name_ru": "Крупные камни", "section_name_en": "Large Stones", "is_public": "true", "sort_order": "2", "comment": ""},
        ], columns=CATALOG_SECTIONS_COLUMNS)
        df.to_csv(CATALOG_SECTIONS_FILE, index=False)


def read_catalog_sections() -> pd.DataFrame:
    ensure_catalog_sections()
    return read_csv_safe(CATALOG_SECTIONS_FILE, CATALOG_SECTIONS_COLUMNS)


def update_catalog_sections(sections_df: pd.DataFrame) -> dict:
    ensure_data_files()
    backup_dir = backup_existing_files("before_update_catalog_sections")
    allowed_ids = {"main", "large"}
    df = sections_df.copy().fillna("")
    for col in CATALOG_SECTIONS_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[df["section_id"].astype(str).isin(allowed_ids)].copy()

    existing = set(df["section_id"].astype(str).tolist())
    if "main" not in existing:
        df = pd.concat([df, pd.DataFrame([{"section_id": "main", "section_name_ru": "Основной каталог", "section_name_en": "Main Catalog", "is_public": "true", "sort_order": "1", "comment": ""}])], ignore_index=True)
    if "large" not in existing:
        df = pd.concat([df, pd.DataFrame([{"section_id": "large", "section_name_ru": "Крупные камни", "section_name_en": "Large Stones", "is_public": "true", "sort_order": "2", "comment": ""}])], ignore_index=True)

    df["is_public"] = df["is_public"].astype(str).str.lower().map(lambda x: "true" if x in {"true", "1", "yes", "да", "истина"} else "false")
    atomic_write_csv(df[CATALOG_SECTIONS_COLUMNS], CATALOG_SECTIONS_FILE)
    return {"updated": True, "backup_dir": str(backup_dir)}




def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_price_files() -> None:
    ensure_dirs()

    if not PRICE_SUPPLIER_FILE.exists():
        rows = []
        for weight_id, _label in WEIGHT_RANGES:
            for color in PRICE_COLORS:
                for clarity in PRICE_CLARITIES:
                    rows.append({
                        "weight_range_id": weight_id,
                        "color": color,
                        "clarity": clarity,
                        "supplier_price_per_ct_usd": "",
                        "comment": "",
                        "updated_at": "",
                    })
        pd.DataFrame(rows, columns=PRICE_SUPPLIER_COLUMNS).to_csv(PRICE_SUPPLIER_FILE, index=False)

    if not PRICE_EXPENSE_RATES_FILE.exists():
        pd.DataFrame([
            {"expense_key": "customs", "expense_name_ru": "Таможня", "rate": "0.37", "is_active": "true", "comment": "", "updated_at": ""},
            {"expense_key": "delivery", "expense_name_ru": "Доставка", "rate": "0.05", "is_active": "true", "comment": "", "updated_at": ""},
            {"expense_key": "transfer", "expense_name_ru": "Переводы", "rate": "0.05", "is_active": "true", "comment": "", "updated_at": ""},
            {"expense_key": "other", "expense_name_ru": "Иные траты", "rate": "0.05", "is_active": "true", "comment": "", "updated_at": ""},
            {"expense_key": "extra", "expense_name_ru": "Дополнительные траты", "rate": "0.00", "is_active": "true", "comment": "", "updated_at": ""},
        ], columns=PRICE_EXPENSE_RATES_COLUMNS).to_csv(PRICE_EXPENSE_RATES_FILE, index=False)

    if not PRICE_MARGINS_FILE.exists():
        rows = []
        default_divisors = {
            "1.00-1.49": "1",
            "1.50-1.99": "1.5",
            "2.00-2.49": "2",
            "2.50-2.99": "2.5",
            "3.00-3.99": "3",
            "4.00-4.99": "4",
            "5.00+": "5",
        }
        default_numerators = {
            "start": "50",
            "working": "70",
            "public": "60",
        }
        for margin_type in ["start", "working", "public"]:
            for weight_id, _label in WEIGHT_RANGES:
                rows.append({
                    "margin_type": margin_type,
                    "weight_range_id": weight_id,
                    "numerator": default_numerators[margin_type],
                    "divisor": default_divisors.get(weight_id, "1"),
                    "comment": "",
                    "updated_at": "",
                })
        pd.DataFrame(rows, columns=PRICE_MARGINS_COLUMNS).to_csv(PRICE_MARGINS_FILE, index=False)

    if not PRICE_SCORE_COEFFICIENTS_FILE.exists():
        pd.DataFrame([
            {"score_key": "poor", "score_name_ru": "Низкое качество", "coefficient": "0.90", "sort_order": "1", "comment": "", "updated_at": ""},
            {"score_key": "fair", "score_name_ru": "Среднее качество", "coefficient": "0.95", "sort_order": "2", "comment": "", "updated_at": ""},
            {"score_key": "standard", "score_name_ru": "Стандартный", "coefficient": "1.00", "sort_order": "3", "comment": "", "updated_at": ""},
            {"score_key": "high", "score_name_ru": "Высокое качество", "coefficient": "1.05", "sort_order": "4", "comment": "", "updated_at": ""},
            {"score_key": "premium", "score_name_ru": "Премиальный", "coefficient": "1.10", "sort_order": "5", "comment": "", "updated_at": ""},
            {"score_key": "elite", "score_name_ru": "Элитный", "coefficient": "1.15", "sort_order": "6", "comment": "", "updated_at": ""},
            {"score_key": "not_calculated", "score_name_ru": "Не рассчитано", "coefficient": "1.00", "sort_order": "7", "comment": "", "updated_at": ""},
        ], columns=PRICE_SCORE_COEFFICIENTS_COLUMNS).to_csv(PRICE_SCORE_COEFFICIENTS_FILE, index=False)

    if not CURRENCY_RATES_FILE.exists():
        pd.DataFrame([
            {"rate_key": "USD_RUB", "rate_name_ru": "Курс доллар / рубль", "rate_value": "", "updated_at": "", "comment": ""},
            {"rate_key": "INR_RUB", "rate_name_ru": "Курс рупия / рубль", "rate_value": "", "updated_at": "", "comment": ""},
            {"rate_key": "USD_INR", "rate_name_ru": "Курс доллар / рупия", "rate_value": "", "updated_at": "", "comment": ""},
        ], columns=CURRENCY_RATES_COLUMNS).to_csv(CURRENCY_RATES_FILE, index=False)


def read_price_supplier() -> pd.DataFrame:
    ensure_price_files()
    return read_csv_safe(PRICE_SUPPLIER_FILE, PRICE_SUPPLIER_COLUMNS)


def read_price_expense_rates() -> pd.DataFrame:
    ensure_price_files()
    return read_csv_safe(PRICE_EXPENSE_RATES_FILE, PRICE_EXPENSE_RATES_COLUMNS)


def read_price_margins() -> pd.DataFrame:
    ensure_price_files()
    return read_csv_safe(PRICE_MARGINS_FILE, PRICE_MARGINS_COLUMNS)


def read_price_score_coefficients() -> pd.DataFrame:
    ensure_price_files()
    return read_csv_safe(PRICE_SCORE_COEFFICIENTS_FILE, PRICE_SCORE_COEFFICIENTS_COLUMNS)


def read_currency_rates() -> pd.DataFrame:
    ensure_price_files()
    return read_csv_safe(CURRENCY_RATES_FILE, CURRENCY_RATES_COLUMNS)


def _prepare_price_df(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy().fillna("")
    for col in columns:
        if col not in out.columns:
            out[col] = ""
    out["updated_at"] = _now_iso() if "updated_at" in out.columns else ""
    return out[columns]


def update_price_supplier(df: pd.DataFrame) -> dict:
    ensure_data_files()
    backup_dir = backup_existing_files("before_update_price_supplier")
    atomic_write_csv(_prepare_price_df(df, PRICE_SUPPLIER_COLUMNS), PRICE_SUPPLIER_FILE)
    return {"updated": True, "backup_dir": str(backup_dir)}


def update_price_expense_rates(df: pd.DataFrame) -> dict:
    ensure_data_files()
    backup_dir = backup_existing_files("before_update_price_expenses")
    out = _prepare_price_df(df, PRICE_EXPENSE_RATES_COLUMNS)
    out["is_active"] = out["is_active"].astype(str).str.lower().map(
        lambda x: "true" if x in {"true", "1", "yes", "да", "истина"} else "false"
    )
    atomic_write_csv(out, PRICE_EXPENSE_RATES_FILE)
    return {"updated": True, "backup_dir": str(backup_dir)}


def update_price_margins(df: pd.DataFrame) -> dict:
    ensure_data_files()
    backup_dir = backup_existing_files("before_update_price_margins")
    atomic_write_csv(_prepare_price_df(df, PRICE_MARGINS_COLUMNS), PRICE_MARGINS_FILE)
    return {"updated": True, "backup_dir": str(backup_dir)}


def update_price_score_coefficients(df: pd.DataFrame) -> dict:
    ensure_data_files()
    backup_dir = backup_existing_files("before_update_price_score_coefficients")
    atomic_write_csv(_prepare_price_df(df, PRICE_SCORE_COEFFICIENTS_COLUMNS), PRICE_SCORE_COEFFICIENTS_FILE)
    return {"updated": True, "backup_dir": str(backup_dir)}


def update_currency_rates(df: pd.DataFrame) -> dict:
    ensure_data_files()
    backup_dir = backup_existing_files("before_update_currency_rates")
    atomic_write_csv(_prepare_price_df(df, CURRENCY_RATES_COLUMNS), CURRENCY_RATES_FILE)
    return {"updated": True, "backup_dir": str(backup_dir)}




def _float_value(value, default: float = 0.0) -> float:
    try:
        text = str(value).strip().replace(",", ".")
        if not text:
            return default
        return float(text)
    except Exception:
        return default


def _has_positive_price(value) -> bool:
    """Supplier price must be filled and greater than zero to calculate downstream prices."""
    try:
        text = str(value).strip().replace(",", ".")
        if not text:
            return False
        return float(text) > 0
    except Exception:
        return False


def calculate_root_price_table() -> pd.DataFrame:
    """Calculate root price-per-carat chain in USD.

    6B scope only:
    supplier -> internal -> start -> working -> public.
    No KURGIN Score, no Index, no stone-level final price.

    Important rule:
    if supplier price is empty or 0, downstream prices are not calculated.
    """
    ensure_price_files()

    supplier = read_price_supplier()
    expenses = read_price_expense_rates()
    margins = read_price_margins()

    active_expenses = expenses[
        expenses["is_active"].astype(str).str.lower().isin(["true", "1", "yes", "да", "истина"])
    ].copy()
    total_expense_rate = active_expenses["rate"].map(_float_value).sum()

    margin_map = {}
    for _, row in margins.iterrows():
        margin_type = str(row.get("margin_type", "")).strip()
        weight_range_id = str(row.get("weight_range_id", "")).strip()
        numerator = _float_value(row.get("numerator", "0"))
        divisor = _float_value(row.get("divisor", "1"), default=1.0)
        if divisor == 0:
            divisor = 1.0
        margin_map[(margin_type, weight_range_id)] = numerator / divisor

    rows = []
    for _, row in supplier.iterrows():
        weight_range_id = str(row.get("weight_range_id", "")).strip()
        raw_supplier_price = row.get("supplier_price_per_ct_usd", "")

        if not _has_positive_price(raw_supplier_price):
            rows.append({
                "weight_range_id": weight_range_id,
                "color": row.get("color", ""),
                "clarity": row.get("clarity", ""),
                "supplier_price_per_ct_usd": "",
                "internal_price_per_ct_usd": "",
                "start_price_per_ct_usd": "",
                "working_price_per_ct_usd": "",
                "public_price_per_ct_usd": "",
                "total_expense_rate": round(total_expense_rate, 6),
                "calculation_status": "Нет цены поставщика",
            })
            continue

        supplier_price = _float_value(raw_supplier_price)

        internal_price = supplier_price * (1 + total_expense_rate)
        start_margin = margin_map.get(("start", weight_range_id), 0.0)
        working_margin = margin_map.get(("working", weight_range_id), 0.0)
        public_margin = margin_map.get(("public", weight_range_id), 0.0)

        start_price = internal_price + start_margin
        working_price = start_price + working_margin
        public_price = working_price + public_margin

        rows.append({
            "weight_range_id": weight_range_id,
            "color": row.get("color", ""),
            "clarity": row.get("clarity", ""),
            "supplier_price_per_ct_usd": round(supplier_price, 2),
            "internal_price_per_ct_usd": round(internal_price, 2),
            "start_price_per_ct_usd": round(start_price, 2),
            "working_price_per_ct_usd": round(working_price, 2),
            "public_price_per_ct_usd": round(public_price, 2),
            "total_expense_rate": round(total_expense_rate, 6),
            "calculation_status": "Рассчитано",
        })

    return pd.DataFrame(rows)


def root_price_matrix_by_color(root_df: pd.DataFrame, price_column: str, color: str) -> pd.DataFrame:
    """Return matrix: rows = clarity, columns = weight ranges for a selected color and price column."""
    if root_df.empty:
        return pd.DataFrame()

    labels = {
        "1.00-1.49": "1.00–1.49",
        "1.50-1.99": "1.50–1.99",
        "2.00-2.49": "2.00–2.49",
        "2.50-2.99": "2.50–2.99",
        "3.00-3.99": "3.00–3.99",
        "4.00-4.99": "4.00–4.99",
        "5.00+": "5.00+",
    }
    clarities = ["IF", "VVS1", "VVS2", "VS1", "VS2"]
    weight_ids = ["1.00-1.49", "1.50-1.99", "2.00-2.49", "2.50-2.99", "3.00-3.99", "4.00-4.99", "5.00+"]

    subset = root_df[root_df["color"].astype(str) == str(color)].copy()
    rows = []
    for clarity in clarities:
        item = {"Чистота": clarity}
        for weight_id in weight_ids:
            match = subset[
                (subset["clarity"].astype(str) == clarity)
                & (subset["weight_range_id"].astype(str) == weight_id)
            ]
            value = ""
            if not match.empty:
                value = match.iloc[0].get(price_column, "")
            item[labels[weight_id]] = value
        rows.append(item)

    return pd.DataFrame(rows)


def _round_price(value: float, currency: str, public_index: bool = False) -> int:
    try:
        amount = float(value)
    except Exception:
        amount = 0.0
    currency = str(currency).upper()
    if currency == "RUB" and public_index:
        if amount <= 0:
            return 0
        import math
        return int(math.ceil(amount / 100.0) * 100)
    return int(round(amount))


def _currency_multiplier(currency: str) -> float:
    currency = str(currency).upper()
    if currency == "USD":
        return 1.0
    rates = read_currency_rates()
    values = {str(row.get("rate_key", "")): _float_value(row.get("rate_value", "0")) for _, row in rates.iterrows()}
    if currency == "RUB":
        return values.get("USD_RUB", 0.0) or 0.0
    if currency == "INR":
        return values.get("USD_INR", 0.0) or 0.0
    return 1.0


def calculate_index_table(score_key: str = "standard", currency: str = "RUB") -> pd.DataFrame:
    root_df = calculate_root_price_table()
    score_df = read_price_score_coefficients()
    score_match = score_df[score_df["score_key"].astype(str) == str(score_key)]
    coefficient = 1.0
    score_name = "Стандартный"
    if not score_match.empty:
        coefficient = _float_value(score_match.iloc[0].get("coefficient", "1"), 1.0)
        score_name = str(score_match.iloc[0].get("score_name_ru", "Стандартный"))
    multiplier = _currency_multiplier(currency)
    public_index = str(currency).upper() == "RUB"
    rows = []
    for _, row in root_df.iterrows():
        public_value = row.get("public_price_per_ct_usd", "")
        if not _has_positive_price(public_value):
            rows.append({
                "weight_range_id": row.get("weight_range_id", ""),
                "color": row.get("color", ""),
                "clarity": row.get("clarity", ""),
                "score_key": score_key,
                "score_name_ru": score_name,
                "score_coefficient": coefficient,
                "currency": str(currency).upper(),
                "public_price_per_ct_usd": "",
                "index_price_per_ct_usd": "",
                "index_price_per_ct_display": "",
                "calculation_status": "Нет цены поставщика",
            })
            continue

        public_usd = _float_value(public_value)
        indexed_usd = public_usd * coefficient
        display_value = indexed_usd * multiplier
        rows.append({
            "weight_range_id": row.get("weight_range_id", ""),
            "color": row.get("color", ""),
            "clarity": row.get("clarity", ""),
            "score_key": score_key,
            "score_name_ru": score_name,
            "score_coefficient": coefficient,
            "currency": str(currency).upper(),
            "public_price_per_ct_usd": round(public_usd, 2),
            "index_price_per_ct_usd": round(indexed_usd, 2),
            "index_price_per_ct_display": _round_price(display_value, currency, public_index=public_index),
            "calculation_status": "Рассчитано",
        })
    return pd.DataFrame(rows)


def index_price_matrix_by_color(index_df: pd.DataFrame, color: str) -> pd.DataFrame:
    if index_df.empty:
        return pd.DataFrame()
    labels = {
        "1.00-1.49": "1.00–1.49",
        "1.50-1.99": "1.50–1.99",
        "2.00-2.49": "2.00–2.49",
        "2.50-2.99": "2.50–2.99",
        "3.00-3.99": "3.00–3.99",
        "4.00-4.99": "4.00–4.99",
        "5.00+": "5.00+",
    }
    clarities = ["IF", "VVS1", "VVS2", "VS1", "VS2"]
    weight_ids = ["1.00-1.49", "1.50-1.99", "2.00-2.49", "2.50-2.99", "3.00-3.99", "4.00-4.99", "5.00+"]
    subset = index_df[index_df["color"].astype(str) == str(color)].copy()
    rows = []
    for clarity in clarities:
        item = {"Чистота": clarity}
        for weight_id in weight_ids:
            match = subset[(subset["clarity"].astype(str) == clarity) & (subset["weight_range_id"].astype(str) == weight_id)]
            item[labels[weight_id]] = "" if match.empty else match.iloc[0].get("index_price_per_ct_display", "")
        rows.append(item)
    return pd.DataFrame(rows)




def _weight_range_for_weight(weight_value) -> str:
    w = _float_value(weight_value, default=-1)
    if 1.00 <= w < 1.50:
        return "1.00-1.49"
    if 1.50 <= w < 2.00:
        return "1.50-1.99"
    if 2.00 <= w < 2.50:
        return "2.00-2.49"
    if 2.50 <= w < 3.00:
        return "2.50-2.99"
    if 3.00 <= w < 4.00:
        return "3.00-3.99"
    if 4.00 <= w < 5.00:
        return "4.00-4.99"
    if w >= 5.00:
        return "5.00+"
    return ""


def _score_key_from_stone(row: dict) -> tuple[str, str]:
    """Return score key and warning.

    Current temporary mapping by numeric KURGIN Score:
    <60 poor, <70 fair, <80 standard, <90 high, <95 premium, >=95 elite.
    If ROUND has no score, return not_calculated and warning.
    Non-ROUND returns not_calculated without warning.
    """
    shape = str(row.get("shape", "")).upper().strip()
    score = _float_value(row.get("kurgin_score", ""), default=-1)

    if shape != "ROUND":
        return "not_calculated", ""

    if score < 0:
        return "not_calculated", "Нет KURGIN Score"

    if score < 60:
        return "poor", ""
    if score < 70:
        return "fair", ""
    if score < 80:
        return "standard", ""
    if score < 90:
        return "high", ""
    if score < 95:
        return "premium", ""
    return "elite", ""


def _score_coefficients_lookup() -> dict:
    score_df = read_price_score_coefficients()
    lookup = {}
    for _, row in score_df.iterrows():
        key = str(row.get("score_key", ""))
        lookup[key] = {
            "name": str(row.get("score_name_ru", key)),
            "coefficient": _float_value(row.get("coefficient", "1"), 1.0),
        }
    return lookup


def _convert_and_round_price(value, currency: str, internal_view: bool = True):
    """Convert from USD and round for 6D internal margin view.

    6D rule:
    USD -> integer dollar, RUB -> integer ruble, INR -> integer rupee.
    """
    if value == "" or value is None:
        return ""
    amount = _float_value(value, 0.0)
    multiplier = _currency_multiplier(currency)
    converted = amount * multiplier
    return int(round(converted))


def calculate_stone_margin_view(currency: str = "RUB") -> pd.DataFrame:
    """6D: calculate margin comparison table for real stones.

    Read-only preview. Does not write results to stones_master.csv.
    """
    stones = read_stones()
    root_df = calculate_root_price_table()
    score_lookup = _score_coefficients_lookup()

    if stones.empty:
        return pd.DataFrame()

    root_lookup = {}
    for _, row in root_df.iterrows():
        key = (
            str(row.get("weight_range_id", "")),
            str(row.get("color", "")).upper().strip(),
            str(row.get("clarity", "")).upper().strip(),
        )
        root_lookup[key] = row.to_dict()

    rows = []
    for _, stone in stones.iterrows():
        stone_dict = stone.to_dict()
        weight = _float_value(stone.get("weight", ""), default=0.0)
        color = str(stone.get("color", "")).upper().strip()
        clarity = str(stone.get("clarity", "")).upper().strip()
        weight_range_id = _weight_range_for_weight(weight)

        base = {
            "ID": stone.get("stone_id", ""),
            "Report #": stone.get("report_number", ""),
            "Вес": weight if weight else "",
            "Цвет": color,
            "Чистота": clarity,
        }

        price_row = root_lookup.get((weight_range_id, color, clarity))
        if not price_row or str(price_row.get("calculation_status", "")) != "Рассчитано":
            rows.append({
                **base,
                "KURGIN Score": stone.get("kurgin_score", ""),
                "Цена поставщика за камень без KURGIN Score": "",
                "Разница: внутренняя − поставщик": "",
                "Внутренняя цена за камень без KURGIN Score": "",
                "Разница: стартовая − внутренняя": "",
                "Стартовая цена за камень с KURGIN Score": "",
                "Разница: рабочая − стартовая": "",
                "Рабочая цена за камень с KURGIN Score": "",
                "Разница: публичная − рабочая": "",
                "Публичная цена за камень с KURGIN Score": "",
                "Статус расчёта": "Нет цены поставщика",
                "Предупреждение": "",
            })
            continue

        score_key, warning = _score_key_from_stone(stone_dict)
        score_info = score_lookup.get(score_key, {"name": "Не рассчитано", "coefficient": 1.0})
        score_coeff = score_info.get("coefficient", 1.0)
        score_label = f"{score_info.get('name', score_key)} ×{score_coeff}"

        supplier_stone_usd = _float_value(price_row.get("supplier_price_per_ct_usd", 0)) * weight
        internal_stone_usd = _float_value(price_row.get("internal_price_per_ct_usd", 0)) * weight
        start_stone_usd = _float_value(price_row.get("start_price_per_ct_usd", 0)) * score_coeff * weight
        working_stone_usd = _float_value(price_row.get("working_price_per_ct_usd", 0)) * score_coeff * weight
        public_stone_usd = _float_value(price_row.get("public_price_per_ct_usd", 0)) * score_coeff * weight

        supplier_display = _convert_and_round_price(supplier_stone_usd, currency)
        internal_display = _convert_and_round_price(internal_stone_usd, currency)
        start_display = _convert_and_round_price(start_stone_usd, currency)
        working_display = _convert_and_round_price(working_stone_usd, currency)
        public_display = _convert_and_round_price(public_stone_usd, currency)

        rows.append({
            **base,
            "KURGIN Score": score_label,
            "Цена поставщика за камень без KURGIN Score": supplier_display,
            "Разница: внутренняя − поставщик": internal_display - supplier_display if supplier_display != "" and internal_display != "" else "",
            "Внутренняя цена за камень без KURGIN Score": internal_display,
            "Разница: стартовая − внутренняя": start_display - internal_display if start_display != "" and internal_display != "" else "",
            "Стартовая цена за камень с KURGIN Score": start_display,
            "Разница: рабочая − стартовая": working_display - start_display if working_display != "" and start_display != "" else "",
            "Рабочая цена за камень с KURGIN Score": working_display,
            "Разница: публичная − рабочая": public_display - working_display if public_display != "" and working_display != "" else "",
            "Публичная цена за камень с KURGIN Score": public_display,
            "Статус расчёта": "Рассчитано",
            "Предупреждение": warning,
        })

    return pd.DataFrame(rows)





PRICE_NUMERIC_STONE_COLUMNS = [
    "supplier_price_per_ct_usd",
    "internal_price_per_ct_usd",
    "start_price_per_ct_usd",
    "working_price_per_ct_usd",
    "public_price_per_ct_usd",
    "supplier_price_total_usd",
    "internal_price_total_usd",
    "start_price_total_usd",
    "working_price_total_usd",
    "public_price_total_usd",
    "supplier_price_total_rub",
    "internal_price_total_rub",
    "start_price_total_rub",
    "working_price_total_rub",
    "public_price_total_rub",
]

PRICE_SERVICE_STONE_COLUMNS = [
    "price_currency_base",
    "price_fx_usd_rub",
    "price_calculated_at",
    "price_status",
    "price_warning",
    "price_source",
    "public_price_display",
    "allow_price_on_request",
]

PRICE_WRITE_CONFIRMATION_TEXT = "ЗАПИСАТЬ ЦЕНЫ"
PRICE_ON_REQUEST_CONFIRMATION_TEXT = "ВКЛЮЧИТЬ ПО ЗАПРОСУ"


def _bool_text(value, default: str = "false") -> str:
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "да", "истина"}:
        return "true"
    if text in {"false", "0", "no", "нет", "ложь", ""}:
        return "false"
    return default


def _money_usd(value) -> str:
    return f"{_float_value(value, 0.0):.2f}"


def _money_rub(value) -> str:
    return str(int(round(_float_value(value, 0.0))))


def _currency_display_value(total_usd: float, currency: str):
    currency = str(currency).upper().strip() or "RUB"
    multiplier = _currency_multiplier(currency)
    if currency != "USD" and multiplier <= 0:
        return ""
    return int(round(total_usd * multiplier))


def _price_warning_for_missing(row: dict, price_row) -> str:
    weight_range_id = _weight_range_for_weight(row.get("weight", ""))
    if not weight_range_id:
        return "Нет диапазона веса"
    if price_row is None:
        return "Нет цены поставщика"
    status = str(price_row.get("calculation_status", ""))
    if status != "Рассчитано":
        return "Нет цены поставщика"
    return "Нет рассчитанной цены"


def _missing_public_price_display(allow_price_on_request: str) -> str:
    return "Цена по запросу" if _bool_text(allow_price_on_request) == "true" else ""


def _blank_price_fields(calculated_at: str, existing_allow_price_on_request: str = "false") -> dict:
    allow_text = _bool_text(existing_allow_price_on_request)
    fields = {col: "" for col in PRICE_NUMERIC_STONE_COLUMNS}
    fields.update({
        "price_currency_base": "USD",
        "price_fx_usd_rub": "",
        "price_calculated_at": calculated_at,
        "price_status": "missing_supplier_price",
        "price_warning": "Нет цены поставщика",
        "price_source": "not_calculated",
        "public_price_display": _missing_public_price_display(allow_text),
        "allow_price_on_request": allow_text,
    })
    return fields


def _is_manual_price_stone(stone: dict) -> bool:
    price_source = str(stone.get("price_source", "")).strip().lower()
    if price_source == "manual":
        return True

    # Legacy manual/admin price field from earlier stages.
    # Do not silently replace it with auto-calculated public prices.
    published_price = str(stone.get("published_price", "")).strip()
    if published_price and price_source not in {"auto_calculated", "not_calculated"}:
        return True

    return False


def _build_price_record(stone: dict, price_row: dict, score_lookup: dict, fx_usd_rub: float, calculated_at: str) -> dict:
    weight = _float_value(stone.get("weight", ""), default=0.0)
    score_key, warning = _score_key_from_stone(stone)
    score_info = score_lookup.get(score_key, {"name": "Не рассчитано", "coefficient": 1.0})
    score_coeff = _float_value(score_info.get("coefficient", 1.0), 1.0)

    supplier_per_ct = _float_value(price_row.get("supplier_price_per_ct_usd", 0.0))
    internal_per_ct = _float_value(price_row.get("internal_price_per_ct_usd", 0.0))
    start_per_ct = _float_value(price_row.get("start_price_per_ct_usd", 0.0)) * score_coeff
    working_per_ct = _float_value(price_row.get("working_price_per_ct_usd", 0.0)) * score_coeff
    public_per_ct = _float_value(price_row.get("public_price_per_ct_usd", 0.0)) * score_coeff

    supplier_total_usd = supplier_per_ct * weight
    internal_total_usd = internal_per_ct * weight
    start_total_usd = start_per_ct * weight
    working_total_usd = working_per_ct * weight
    public_total_usd = public_per_ct * weight

    def rub_value(total_usd: float) -> str:
        if fx_usd_rub <= 0:
            return ""
        return _money_rub(total_usd * fx_usd_rub)

    fields = {
        "supplier_price_per_ct_usd": _money_usd(supplier_per_ct),
        "internal_price_per_ct_usd": _money_usd(internal_per_ct),
        "start_price_per_ct_usd": _money_usd(start_per_ct),
        "working_price_per_ct_usd": _money_usd(working_per_ct),
        "public_price_per_ct_usd": _money_usd(public_per_ct),
        "supplier_price_total_usd": _money_usd(supplier_total_usd),
        "internal_price_total_usd": _money_usd(internal_total_usd),
        "start_price_total_usd": _money_usd(start_total_usd),
        "working_price_total_usd": _money_usd(working_total_usd),
        "public_price_total_usd": _money_usd(public_total_usd),
        "supplier_price_total_rub": rub_value(supplier_total_usd),
        "internal_price_total_rub": rub_value(internal_total_usd),
        "start_price_total_rub": rub_value(start_total_usd),
        "working_price_total_rub": rub_value(working_total_usd),
        "public_price_total_rub": rub_value(public_total_usd),
        "price_currency_base": "USD",
        "price_fx_usd_rub": f"{fx_usd_rub:.6f}" if fx_usd_rub > 0 else "",
        "price_calculated_at": calculated_at,
        "price_status": "calculated",
        "price_warning": str(warning),
        "price_source": "auto_calculated",
        "public_price_display": rub_value(public_total_usd),
        "allow_price_on_request": "false",
    }

    return {
        "stone_id": str(stone.get("stone_id", "")),
        "report_number": str(stone.get("report_number", "")),
        "weight": weight if weight else "",
        "color": str(stone.get("color", "")).upper().strip(),
        "clarity": str(stone.get("clarity", "")).upper().strip(),
        "score_key": score_key,
        "score_coefficient": score_coeff,
        "warning": str(warning),
        "public_total_usd": public_total_usd,
        "fields": fields,
    }


def _price_preview_fingerprint(writable_records: list[dict], missing_records: list[dict], manual_records: list[dict]) -> str:
    def slim_writable(record: dict) -> dict:
        fields = record.get("fields", {})
        return {
            "stone_id": record.get("stone_id", ""),
            "supplier_price_total_usd": fields.get("supplier_price_total_usd", ""),
            "public_price_total_usd": fields.get("public_price_total_usd", ""),
            "public_price_total_rub": fields.get("public_price_total_rub", ""),
            "price_warning": fields.get("price_warning", ""),
            "price_fx_usd_rub": fields.get("price_fx_usd_rub", ""),
        }

    def slim_missing(record: dict) -> dict:
        fields = record.get("fields", {})
        return {
            "stone_id": record.get("stone_id", ""),
            "price_status": fields.get("price_status", ""),
            "price_warning": fields.get("price_warning", ""),
            "allow_price_on_request": fields.get("allow_price_on_request", "false"),
        }

    payload = {
        "writable": [slim_writable(r) for r in writable_records],
        "missing": [slim_missing(r) for r in missing_records],
        "manual": sorted([str(r.get("stone_id", "")) for r in manual_records]),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_price_write_preview(currency: str = "RUB") -> dict:
    """7B/7C: build a safe preview for future price write.

    The preview is read-only. It also contains a fingerprint used by 7C
    to reject stale confirmations.
    """
    ensure_data_files()
    display_currency = str(currency).upper().strip() or "RUB"
    stones = read_stones()
    root_df = calculate_root_price_table()
    score_lookup = _score_coefficients_lookup()
    fx_usd_rub = _currency_multiplier("RUB")
    calculated_at = _now_iso()

    empty_result = {
        "summary": {
            "total": 0,
            "will_write": 0,
            "missing_supplier_price": 0,
            "manual_prices": 0,
            "skipped": 0,
            "price_on_request_possible": 0,
        },
        "will_write_df": pd.DataFrame(),
        "missing_price_df": pd.DataFrame(),
        "manual_df": pd.DataFrame(),
        "writable_records": [],
        "missing_records": [],
        "manual_records": [],
        "currency": display_currency,
        "fx_usd_rub": fx_usd_rub,
        "generated_at": calculated_at,
        "fingerprint": _price_preview_fingerprint([], [], []),
    }

    if stones.empty:
        return empty_result

    root_lookup = {}
    for _, row in root_df.iterrows():
        key = (
            str(row.get("weight_range_id", "")),
            str(row.get("color", "")).upper().strip(),
            str(row.get("clarity", "")).upper().strip(),
        )
        root_lookup[key] = row.to_dict()

    rows_write = []
    rows_missing = []
    rows_manual = []
    writable_records = []
    missing_records = []
    manual_records = []

    for _, stone_row in stones.iterrows():
        stone = stone_row.to_dict()
        sid = str(stone.get("stone_id", ""))
        price_source_before = str(stone.get("price_source", "")).strip().lower()
        is_manual = _is_manual_price_stone(stone)
        weight_range_id = _weight_range_for_weight(stone.get("weight", ""))
        color = str(stone.get("color", "")).upper().strip()
        clarity = str(stone.get("clarity", "")).upper().strip()
        price_row = root_lookup.get((weight_range_id, color, clarity))

        if is_manual:
            public_display = ""
            if price_row and str(price_row.get("calculation_status", "")) == "Рассчитано":
                record = _build_price_record(stone, price_row, score_lookup, fx_usd_rub, calculated_at)
                public_display = _currency_display_value(record.get("public_total_usd", 0.0), display_currency)
            manual_item = {
                "stone_id": sid,
                "report_number": str(stone.get("report_number", "")),
            }
            manual_records.append(manual_item)
            rows_manual.append({
                "ID": sid,
                "Report #": stone.get("report_number", ""),
                "Текущая цена RUB": stone.get("public_price_total_rub", "") or stone.get("published_price", ""),
                f"Новая рассчитанная цена {display_currency}": public_display,
                "Действие": "Не перезаписывать без отдельного подтверждения",
            })
            continue

        if not price_row or str(price_row.get("calculation_status", "")) != "Рассчитано":
            warning = _price_warning_for_missing(stone, price_row)
            fields = _blank_price_fields(calculated_at, stone.get("allow_price_on_request", "false"))
            fields["price_warning"] = warning if warning else "Нет цены поставщика"
            missing_record = {
                "stone_id": sid,
                "report_number": str(stone.get("report_number", "")),
                "fields": fields,
            }
            missing_records.append(missing_record)
            rows_missing.append({
                "ID": sid,
                "Report #": stone.get("report_number", ""),
                "Вес": stone.get("weight", ""),
                "Цвет": color,
                "Чистота": clarity,
                "Форма": stone.get("shape", ""),
                "Раздел": stone.get("catalog_section", ""),
                "Причина": fields.get("price_warning", "Нет цены поставщика"),
                "Публичное отображение": fields.get("public_price_display", "") or "Не включено",
                "allow_price_on_request сейчас": fields.get("allow_price_on_request", "false"),
                "Числовые цены": "Не записывать",
            })
            continue

        record = _build_price_record(stone, price_row, score_lookup, fx_usd_rub, calculated_at)
        writable_records.append(record)
        display_price = _currency_display_value(record.get("public_total_usd", 0.0), display_currency)
        start_display = _currency_display_value(_float_value(record["fields"].get("start_price_total_usd", 0.0)), display_currency)
        working_display = _currency_display_value(_float_value(record["fields"].get("working_price_total_usd", 0.0)), display_currency)
        rows_write.append({
            "ID": sid,
            "Report #": stone.get("report_number", ""),
            "Вес": stone.get("weight", ""),
            "Цвет": color,
            "Чистота": clarity,
            f"Стартовая цена {display_currency}": start_display,
            f"Рабочая цена {display_currency}": working_display,
            f"Публичная цена {display_currency}": display_price,
            "public_price_total_usd": record["fields"].get("public_price_total_usd", ""),
            "public_price_total_rub": record["fields"].get("public_price_total_rub", ""),
            "price_source до": price_source_before or "",
            "price_source после": "auto_calculated",
            "Предупреждение": record.get("warning", ""),
        })

    will_write_df = pd.DataFrame(rows_write)
    missing_price_df = pd.DataFrame(rows_missing)
    manual_df = pd.DataFrame(rows_manual)

    summary = {
        "total": int(len(stones)),
        "will_write": int(len(will_write_df)),
        "missing_supplier_price": int(len(missing_price_df)),
        "manual_prices": int(len(manual_df)),
        "skipped": int(len(missing_price_df) + len(manual_df)),
        "price_on_request_possible": int(len(missing_price_df)),
    }

    return {
        "summary": summary,
        "will_write_df": will_write_df,
        "missing_price_df": missing_price_df,
        "manual_df": manual_df,
        "writable_records": writable_records,
        "missing_records": missing_records,
        "manual_records": manual_records,
        "currency": display_currency,
        "fx_usd_rub": fx_usd_rub,
        "generated_at": calculated_at,
        "fingerprint": _price_preview_fingerprint(writable_records, missing_records, manual_records),
    }


def _ensure_price_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().fillna("")
    for col in PRICE_WRITE_STONE_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    return out


def _apply_price_records(stones: pd.DataFrame, records: list[dict]) -> pd.DataFrame:
    out = _ensure_price_columns(stones)
    for record in records:
        sid = str(record.get("stone_id", ""))
        if not sid:
            continue
        mask = out["stone_id"].astype(str) == sid
        if not mask.any():
            continue
        fields = record.get("fields", {})
        for col in PRICE_WRITE_STONE_COLUMNS:
            if col in fields:
                out.loc[mask, col] = fields.get(col, "")
        if "updated_at" in out.columns:
            out.loc[mask, "updated_at"] = _now_iso()
    return out


def commit_price_write(currency: str = "RUB", expected_fingerprint: str = "", confirmed: bool = False) -> dict:
    """7C: write calculated price fields into stones_master.csv after preview confirmation.

    Manual prices are never overwritten by this function.
    Stones without supplier price get no numeric prices; they receive only status metadata.
    """
    ensure_data_files()
    if not confirmed:
        return {"updated": False, "message": "Запись отменена: нет явного подтверждения."}

    preview = build_price_write_preview(currency)
    current_fingerprint = preview.get("fingerprint", "")
    if not expected_fingerprint or expected_fingerprint != current_fingerprint:
        return {
            "updated": False,
            "message": "Запись отменена: предпросмотр устарел. Сформируйте предпросмотр заново.",
            "current_fingerprint": current_fingerprint,
        }

    writable_records = preview.get("writable_records", [])
    missing_records = preview.get("missing_records", [])
    manual_records = preview.get("manual_records", [])

    if writable_records and _currency_multiplier("RUB") <= 0:
        return {"updated": False, "message": "Запись отменена: не задан курс USD_RUB для итоговых RUB-полей."}

    records_to_apply = list(writable_records) + list(missing_records)
    if not records_to_apply:
        return {
            "updated": False,
            "message": "Нет строк для записи. Ручные цены не изменены.",
            "prices_written": 0,
            "missing_marked": 0,
            "manual_skipped": len(manual_records),
        }

    backup_dir = backup_existing_files("before_price_write_7c")
    stones = read_stones()
    stones = _apply_price_records(stones, records_to_apply)
    atomic_write_csv(stones, STONES_FILE)

    return {
        "updated": True,
        "message": "Цены записаны в stones_master.csv.",
        "backup_dir": str(backup_dir),
        "prices_written": int(len(writable_records)),
        "missing_marked": int(len(missing_records)),
        "manual_skipped": int(len(manual_records)),
    }


def enable_price_on_request_for_missing(currency: str = "RUB", expected_fingerprint: str = "", confirmed: bool = False) -> dict:
    """Separately enable allow_price_on_request=true for currently missing supplier prices.

    This is intentionally not part of commit_price_write, because price-on-request
    must be enabled through a separate preview and confirmation path.
    """
    ensure_data_files()
    if not confirmed:
        return {"updated": False, "message": "Действие отменено: нет явного подтверждения."}

    preview = build_price_write_preview(currency)
    current_fingerprint = preview.get("fingerprint", "")
    if not expected_fingerprint or expected_fingerprint != current_fingerprint:
        return {
            "updated": False,
            "message": "Действие отменено: предпросмотр устарел. Сформируйте предпросмотр заново.",
            "current_fingerprint": current_fingerprint,
        }

    missing_records = preview.get("missing_records", [])
    if not missing_records:
        return {"updated": False, "message": "Нет камней без цены поставщика для включения “Цена по запросу”.", "enabled": 0}

    records = []
    for record in missing_records:
        fields = dict(record.get("fields", {}))
        for col in PRICE_NUMERIC_STONE_COLUMNS:
            fields[col] = ""
        fields["allow_price_on_request"] = "true"
        fields["public_price_display"] = "Цена по запросу"
        fields["price_source"] = "not_calculated"
        fields["price_status"] = "missing_supplier_price"
        fields["price_warning"] = fields.get("price_warning", "") or "Нет цены поставщика"
        records.append({**record, "fields": fields})

    backup_dir = backup_existing_files("before_enable_price_on_request_7c")
    stones = read_stones()
    stones = _apply_price_records(stones, records)
    atomic_write_csv(stones, STONES_FILE)

    return {
        "updated": True,
        "message": "allow_price_on_request включён для камней без цены поставщика.",
        "backup_dir": str(backup_dir),
        "enabled": int(len(records)),
    }


PUBLIC_LAYER_GROUPS = [
    "Public OK — numeric price",
    "Public OK — price on request",
    "Ready but not published",
    "Hidden by status",
    "Hidden by availability_status",
    "Hidden by catalog_section",
    "Missing price",
    "Manual price review",
    "Data problems",
]

PUBLIC_CARD_REQUIRED_FIELDS = [
    "shape",
    "weight",
    "color",
    "clarity",
    "kurgin_score",
    "public_price_display",
]

PUBLIC_CARD_WARNING_FIELDS = [
    "min_diameter",
    "max_diameter",
    "depth_mm",
    "cut",
    "symmetry",
    "polish",
    "fluorescence",
]

PUBLIC_PREVIEW_COLUMNS = [
    "stone_id",
    "report_number",
    "lab",
    "shape",
    "weight",
    "color",
    "clarity",
    "kurgin_score",
    "public_price_display",
    "price_status_public",
    "availability_status_public",
    "catalog_section",
    "section_name",
    "min_diameter",
    "max_diameter",
    "depth_mm",
    "cut_grade",
    "symmetry",
    "polish",
    "fluorescence",
    "public_card_status",
    "public_visibility_reason",
]


def _has_text(value) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return text not in {"", "nan", "NaN", "<NA>"}


def _is_positive_number(value) -> bool:
    return _float_value(value, 0.0) > 0


def _section_lookup() -> dict:
    sections = read_catalog_sections()
    lookup = {}
    for _, row in sections.iterrows():
        section_id = str(row.get("section_id", "")).strip()
        if not section_id:
            continue
        lookup[section_id] = {
            "section_name_ru": str(row.get("section_name_ru", section_id)),
            "section_name_en": str(row.get("section_name_en", section_id)),
            "is_public": _bool_text(row.get("is_public", "false")) == "true",
        }
    return lookup


def _missing_fields(row: dict, fields: list[str]) -> list[str]:
    missing = []
    for field in fields:
        if field not in row:
            continue
        if not _has_text(row.get(field, "")):
            missing.append(field)
    return missing


def _price_public_state(row: dict) -> tuple[str, str, bool, bool, list[str]]:
    """Return price_kind, reason, is_public_price, is_manual_review, problems."""
    price_status = str(row.get("price_status", "")).strip().lower()
    price_source = str(row.get("price_source", "")).strip().lower()
    price_display = str(row.get("public_price_display", "")).strip()
    allow_por = _bool_text(row.get("allow_price_on_request", "false")) == "true"
    public_total_rub = row.get("public_price_total_rub", "")
    problems = []

    if price_status == "calculated":
        if not _has_text(price_display):
            problems.append("calculated without public_price_display")
        if not _is_positive_number(public_total_rub):
            problems.append("calculated without public_price_total_rub")
        if problems:
            return "problem", "Некорректная рассчитанная цена", False, False, problems
        manual_review = price_source == "manual"
        if allow_por:
            problems.append("allow_price_on_request true with calculated price")
        return "numeric", "Числовая публичная цена готова", True, manual_review, problems

    if price_status == "missing_supplier_price":
        if allow_por and price_display == "Цена по запросу":
            return "price_on_request", "Разрешено отображение “Цена по запросу”", True, False, []
        return "missing", "Нет цены поставщика и “Цена по запросу” не разрешена", False, False, []

    if not price_status:
        return "missing", "price_status пустой", False, False, ["empty price_status"]

    return "problem", f"Неизвестный price_status: {price_status}", False, False, [f"unknown price_status: {price_status}"]


def _build_public_preview_row(row: dict, section_info: dict, price_kind: str, reason: str) -> dict:
    return {
        "stone_id": row.get("stone_id", ""),
        "report_number": row.get("report_number", ""),
        "lab": row.get("lab", ""),
        "shape": row.get("shape", ""),
        "weight": row.get("weight", ""),
        "color": row.get("color", ""),
        "clarity": row.get("clarity", ""),
        "kurgin_score": row.get("kurgin_score", ""),
        "public_price_display": row.get("public_price_display", ""),
        "price_status_public": price_kind,
        "availability_status_public": row.get("availability_status", ""),
        "catalog_section": row.get("catalog_section", ""),
        "section_name": section_info.get("section_name_ru", ""),
        "min_diameter": row.get("min_diameter", ""),
        "max_diameter": row.get("max_diameter", ""),
        "depth_mm": row.get("depth_mm", ""),
        "cut_grade": row.get("cut", ""),
        "symmetry": row.get("symmetry", ""),
        "polish": row.get("polish", ""),
        "fluorescence": row.get("fluorescence", ""),
        "public_card_status": "public_candidate",
        "public_visibility_reason": reason,
    }


def build_public_layer_preview() -> dict:
    """7E: build read-only Admin preview/audit for the future public layer.

    This function applies 7D public-layer rules. It does not mutate CSV files,
    does not create backups, does not write exports and does not sync data.
    """
    ensure_data_files()
    stones = read_stones()
    sections = _section_lookup()
    generated_at = _now_iso()

    audit_rows = []
    public_rows = []

    for _, stone_row in stones.iterrows():
        row = stone_row.to_dict()
        sid = str(row.get("stone_id", ""))
        status = str(row.get("status", "")).strip().lower()
        availability = str(row.get("availability_status", "")).strip().lower()
        section_id = str(row.get("catalog_section", "")).strip()
        section_info = sections.get(section_id, {})
        section_exists = bool(section_info)
        section_public = bool(section_info.get("is_public", False))

        problems = []
        warnings = []
        group = "Data problems"
        public_candidate = False
        price_kind = "not_public"
        reason = ""
        control = "blocked"

        if not section_id:
            group = "Hidden by catalog_section"
            reason = "catalog_section пустой"
        elif not section_exists:
            group = "Data problems"
            reason = "catalog_section не найден в catalog_sections.csv"
            problems.append("catalog_section not found")
        elif not section_public:
            group = "Hidden by catalog_section"
            reason = "catalog_sections.is_public != true"
        elif status == "ready":
            group = "Ready but not published"
            reason = "status = ready; готово внутри Admin, но не public"
        elif status != "published":
            group = "Hidden by status"
            reason = f"status = {status or 'empty'}"
        elif availability != "in_stock":
            group = "Hidden by availability_status"
            reason = f"availability_status = {availability or 'empty'}"
        else:
            price_kind, price_reason, price_is_public, manual_review, price_problems = _price_public_state(row)
            problems.extend(price_problems)

            warning_missing = _missing_fields(row, PUBLIC_CARD_WARNING_FIELDS)

            if price_kind == "missing":
                group = "Missing price"
                reason = price_reason
            elif price_kind == "problem":
                group = "Data problems"
                reason = price_reason
                problems.extend(price_problems)
            else:
                required_missing = _missing_fields(row, PUBLIC_CARD_REQUIRED_FIELDS)
                if required_missing:
                    group = "Data problems"
                    reason = "Не заполнены обязательные public card fields: " + ", ".join(required_missing)
                    problems.append("missing required public card fields: " + ", ".join(required_missing))
                elif price_kind == "numeric" and manual_review:
                    group = "Manual price review"
                    public_candidate = True
                    reason = "Числовая цена готова, но price_source = manual требует Admin review"
                    control = "warning"
                elif price_kind == "numeric":
                    group = "Public OK — numeric price"
                    public_candidate = True
                    reason = price_reason
                    control = "ok" if not price_problems else "warning"
                elif price_kind == "price_on_request":
                    group = "Public OK — price on request"
                    public_candidate = True
                    reason = price_reason
                    control = "ok"

            if warning_missing:
                warnings.append("Missing card detail fields: " + ", ".join(warning_missing))
            if price_problems and public_candidate:
                warnings.append("; ".join(price_problems))

        if problems and group != "Data problems" and control == "ok":
            control = "warning"
        if problems and group == "Data problems":
            control = "problem"
        if warnings and control == "ok":
            control = "warning"

        audit_item = {
            "Группа": group,
            "Контроль": control,
            "Причина": reason,
            "Проблемы": "; ".join(dict.fromkeys([p for p in problems if p])),
            "Предупреждения": "; ".join(dict.fromkeys([w for w in warnings if w])),
            "Public candidate": "yes" if public_candidate else "no",
            "ID": sid,
            "Report #": row.get("report_number", ""),
            "Lab": row.get("lab", ""),
            "Форма": row.get("shape", ""),
            "Карат": row.get("weight", ""),
            "Цвет": row.get("color", ""),
            "Чистота": row.get("clarity", ""),
            "KURGIN Score": row.get("kurgin_score", ""),
            "Цена": row.get("public_price_display", ""),
            "status": status,
            "availability_status": availability,
            "catalog_section": section_id,
            "section_name": section_info.get("section_name_ru", ""),
            "section_is_public": "true" if section_public else "false",
            "price_status": row.get("price_status", ""),
            "price_source": row.get("price_source", ""),
            "allow_price_on_request": _bool_text(row.get("allow_price_on_request", "false")),
            "min_diameter": row.get("min_diameter", ""),
            "max_diameter": row.get("max_diameter", ""),
            "depth_mm": row.get("depth_mm", ""),
            "cut": row.get("cut", ""),
            "symmetry": row.get("symmetry", ""),
            "polish": row.get("polish", ""),
            "fluorescence": row.get("fluorescence", ""),
        }
        audit_rows.append(audit_item)

        if public_candidate:
            public_rows.append(_build_public_preview_row(row, section_info, price_kind, reason))

    audit_df = pd.DataFrame(audit_rows)
    public_preview_df = pd.DataFrame(public_rows)
    for col in PUBLIC_PREVIEW_COLUMNS:
        if col not in public_preview_df.columns:
            public_preview_df[col] = ""
    public_preview_df = public_preview_df[PUBLIC_PREVIEW_COLUMNS] if not public_preview_df.empty else pd.DataFrame(columns=PUBLIC_PREVIEW_COLUMNS)

    group_counts = []
    for group_name in PUBLIC_LAYER_GROUPS:
        count = int((audit_df["Группа"].astype(str) == group_name).sum()) if not audit_df.empty and "Группа" in audit_df.columns else 0
        group_counts.append({"Группа": group_name, "Количество": count})
    group_counts_df = pd.DataFrame(group_counts)

    problem_df = audit_df[audit_df["Контроль"].astype(str) == "problem"].copy() if not audit_df.empty else pd.DataFrame()
    warning_df = audit_df[audit_df["Контроль"].astype(str) == "warning"].copy() if not audit_df.empty else pd.DataFrame()

    public_ok_numeric = 0
    if not public_preview_df.empty:
        public_ok_numeric = int((public_preview_df["price_status_public"].astype(str) == "numeric").sum())
    public_ok_request = 0
    if not public_preview_df.empty:
        public_ok_request = int((public_preview_df["price_status_public"].astype(str) == "price_on_request").sum())

    summary = {
        "total": int(len(audit_df)),
        "public_candidates": int(len(public_preview_df)),
        "public_ok_numeric": public_ok_numeric,
        "public_ok_price_on_request": public_ok_request,
        "manual_price_review": int((audit_df["Группа"].astype(str) == "Manual price review").sum()) if not audit_df.empty else 0,
        "ready_not_published": int((audit_df["Группа"].astype(str) == "Ready but not published").sum()) if not audit_df.empty else 0,
        "hidden_by_status": int((audit_df["Группа"].astype(str) == "Hidden by status").sum()) if not audit_df.empty else 0,
        "hidden_by_availability": int((audit_df["Группа"].astype(str) == "Hidden by availability_status").sum()) if not audit_df.empty else 0,
        "hidden_by_section": int((audit_df["Группа"].astype(str) == "Hidden by catalog_section").sum()) if not audit_df.empty else 0,
        "missing_price": int((audit_df["Группа"].astype(str) == "Missing price").sum()) if not audit_df.empty else 0,
        "data_problems": int((audit_df["Группа"].astype(str) == "Data problems").sum()) if not audit_df.empty else 0,
        "warnings": int(len(warning_df)),
        "generated_at": generated_at,
    }

    return {
        "summary": summary,
        "audit_df": audit_df,
        "public_preview_df": public_preview_df,
        "group_counts_df": group_counts_df,
        "problem_df": problem_df,
        "warning_df": warning_df,
        "generated_at": generated_at,
    }
