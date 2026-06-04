from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import pandas as pd

from .paths import ensure_dirs, BACKUPS_DIR, STONES_FILE, SHIPMENTS_FILE, IMPORT_LOG_FILE
from .schema import STONES_COLUMNS, SHIPMENTS_COLUMNS, IMPORT_LOG_COLUMNS


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


def backup_existing_files(label: str) -> Path:
    ensure_dirs()
    backup_dir = BACKUPS_DIR / f"{now_stamp()}_{label}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for path in [STONES_FILE, SHIPMENTS_FILE, IMPORT_LOG_FILE]:
        if path.exists():
            shutil.copy2(path, backup_dir / path.name)

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

    shipments = read_shipments()
    used = []
    if "import_id" in shipments.columns:
        used += shipments["import_id"].dropna().astype(str).tolist()
    log = read_import_log()
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



def get_shipment_delete_preview(import_id: str) -> dict:
    """Return counts/files affected by full shipment deletion."""
    ensure_data_files()
    stones = read_stones()
    shipments = read_shipments()
    log = read_import_log()
    raw_dir = __import__('modules.paths', fromlist=['RAW_DIR']).RAW_DIR / import_id

    return {
        "import_id": import_id,
        "stones_count": int((stones["shipment_id"].astype(str) == import_id).sum()) if "shipment_id" in stones.columns else 0,
        "shipment_rows": int((shipments["shipment_id"].astype(str) == import_id).sum()) if "shipment_id" in shipments.columns else 0,
        "log_rows": int((log["import_id"].astype(str) == import_id).sum()) if "import_id" in log.columns else 0,
        "raw_dir_exists": raw_dir.exists(),
        "raw_dir": str(raw_dir),
    }


def delete_shipment_completely(import_id: str) -> dict:
    """Delete one shipment, its stones, import log rows, and raw folder after backup."""
    ensure_data_files()
    from .paths import RAW_DIR
    backup_dir = backup_existing_files(f"before_delete_{import_id}")

    stones = read_stones()
    shipments = read_shipments()
    log = read_import_log()

    stones_before = len(stones)
    shipments_before = len(shipments)
    log_before = len(log)

    if "shipment_id" in stones.columns:
        stones = stones[stones["shipment_id"].astype(str) != import_id]
    if "shipment_id" in shipments.columns:
        shipments = shipments[shipments["shipment_id"].astype(str) != import_id]
    if "import_id" in log.columns:
        log = log[log["import_id"].astype(str) != import_id]

    atomic_write_csv(stones, STONES_FILE)
    atomic_write_csv(shipments, SHIPMENTS_FILE)
    atomic_write_csv(log, IMPORT_LOG_FILE)

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
        "raw_deleted": raw_deleted,
    }
