from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import pandas as pd

from .paths import ensure_dirs, BACKUPS_DIR, STONES_FILE, SHIPMENTS_FILE, IMPORT_LOG_FILE, RAW_DIR, PAYMENTS_FILE, PRICE_SUPPLIER_FILE, PRICE_EXPENSE_RATES_FILE, PRICE_MARGINS_FILE, PRICE_SCORE_COEFFICIENTS_FILE, CURRENCY_RATES_FILE, CATALOG_SECTIONS_FILE
from .schema import STONES_COLUMNS, SHIPMENTS_COLUMNS, IMPORT_LOG_COLUMNS, PAYMENTS_COLUMNS, PRICE_SUPPLIER_COLUMNS, PRICE_EXPENSE_RATES_COLUMNS, PRICE_MARGINS_COLUMNS, PRICE_SCORE_COEFFICIENTS_COLUMNS, CURRENCY_RATES_COLUMNS, WEIGHT_RANGES, PRICE_COLORS, PRICE_CLARITIES, CATALOG_SECTIONS_COLUMNS


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




def build_price_write_preview(currency: str = "RUB") -> dict:
    """7B: build a safe preview for future price write.

    This function must not write to stones_master.csv.

    Important: use the same status logic as calculate_stone_margin_view.
    """
    margin_view = calculate_stone_margin_view(currency)
    stones = read_stones()

    if margin_view.empty:
        return {
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
        }

    stone_source = {}
    if not stones.empty and "stone_id" in stones.columns:
        for _, row in stones.iterrows():
            sid = str(row.get("stone_id", ""))
            stone_source[sid] = {
                "price_source": str(row.get("price_source", "")),
                "shape": str(row.get("shape", "")),
                "catalog_section": str(row.get("catalog_section", "")),
                "allow_price_on_request": str(row.get("allow_price_on_request", "false")),
                "current_public_price_total_rub": str(row.get("public_price_total_rub", "")),
            }

    rows_write = []
    rows_missing = []
    rows_manual = []

    for _, row in margin_view.iterrows():
        sid = str(row.get("ID", ""))
        meta = stone_source.get(sid, {})
        price_source_before = meta.get("price_source", "")
        is_manual = price_source_before == "manual"
        status = str(row.get("Статус расчёта", "")).strip()

        public_price = row.get("Публичная цена за камень с KURGIN Score", "")
        has_public_price = str(public_price).strip() not in {"", "None", "nan"}

        if is_manual:
            rows_manual.append({
                "ID": sid,
                "Report #": row.get("Report #", ""),
                "Текущая цена": meta.get("current_public_price_total_rub", ""),
                "Новая рассчитанная цена": public_price,
                "Действие": "Не перезаписывать без отдельного подтверждения",
            })
            continue

        # A stone is writable only if margin view says it is calculated
        # and there is a public price value.
        if status == "Рассчитано" and has_public_price:
            rows_write.append({
                "ID": sid,
                "Report #": row.get("Report #", ""),
                "Вес": row.get("Вес", ""),
                "Цвет": row.get("Цвет", ""),
                "Чистота": row.get("Чистота", ""),
                "Стартовая цена RUB": row.get("Стартовая цена за камень с KURGIN Score", ""),
                "Рабочая цена RUB": row.get("Рабочая цена за камень с KURGIN Score", ""),
                "Публичная цена RUB": public_price,
                "price_source до": price_source_before or "",
                "price_source после": "auto_calculated",
                "Предупреждение": row.get("Предупреждение", ""),
            })
            continue

        rows_missing.append({
            "ID": sid,
            "Report #": row.get("Report #", ""),
            "Вес": row.get("Вес", ""),
            "Цвет": row.get("Цвет", ""),
            "Чистота": row.get("Чистота", ""),
            "Форма": meta.get("shape", ""),
            "Раздел": meta.get("catalog_section", ""),
            "Причина": status or "Нет цены поставщика",
            "Публичное отображение": "Цена по запросу",
            "Показывать “Цена по запросу”": meta.get("allow_price_on_request", "false"),
        })

    will_write_df = pd.DataFrame(rows_write)
    missing_price_df = pd.DataFrame(rows_missing)
    manual_df = pd.DataFrame(rows_manual)

    summary = {
        "total": int(len(margin_view)),
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
    }

