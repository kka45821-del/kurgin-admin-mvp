from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import pandas as pd

from .paths import ensure_dirs, BACKUPS_DIR, STONES_FILE, SHIPMENTS_FILE, IMPORT_LOG_FILE, RAW_DIR, PAYMENTS_FILE
from .schema import STONES_COLUMNS, SHIPMENTS_COLUMNS, IMPORT_LOG_COLUMNS, PAYMENTS_COLUMNS


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

    for path in [STONES_FILE, SHIPMENTS_FILE, IMPORT_LOG_FILE, PAYMENTS_FILE]:
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

    updated = 0
    for _, new_row in update_df.iterrows():
        report = str(new_row.get("report_number", "")).strip()
        if not report:
            continue
        mask = stones["report_number"].astype(str) == report
        if not mask.any():
            continue

        for col in update_allowed:
            stones.loc[mask, col] = new_row.get(col, "")

        stones.loc[mask, "updated_at"] = datetime.now().isoformat(timespec="seconds")
        stones.loc[mask, "updated_import_id"] = import_id
        stones.loc[mask, "last_source_file"] = source_file
        updated += int(mask.sum())

    atomic_write_csv(stones, STONES_FILE)
    return {"updated": updated, "backup_dir": str(backup_dir)}
