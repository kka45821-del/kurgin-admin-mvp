from datetime import date

import pandas as pd

from admin_io import (
    load_batch_payments,
    load_batches,
    load_stones,
    save_batch_payments,
    save_batches,
    save_stones,
)


ACTIVE_BATCH_STATUSES = {"", "uploaded", "active", "draft"}
ARCHIVE_BATCH_STATUSES = {"archived", "removed_from_sale"}
PERMANENTLY_DELETED_STATUS = "permanently_deleted"


def normalized_batch_status(row: pd.Series) -> str:
    status = str(row.get("batch_status", "") or "").strip().lower()
    if status:
        return status
    upload_confirmed = str(row.get("upload_confirmed", "") or "").strip().lower()
    return "uploaded" if upload_confirmed in {"true", "1", "yes", "y", "да"} else "draft"


def active_batch_mask(batches: pd.DataFrame) -> pd.Series:
    if batches.empty:
        return pd.Series([], dtype=bool)
    statuses = batches.apply(normalized_batch_status, axis=1)
    return statuses.isin(ACTIVE_BATCH_STATUSES)


def archive_batch_mask(batches: pd.DataFrame) -> pd.Series:
    if batches.empty:
        return pd.Series([], dtype=bool)
    statuses = batches.apply(normalized_batch_status, axis=1)
    return statuses.isin(ARCHIVE_BATCH_STATUSES)


def ensure_soft_remove_columns(stones: pd.DataFrame) -> pd.DataFrame:
    result = stones.copy()
    defaults = {
        "show_in_catalog": True,
        "is_mvp_eligible": True,
        "current_status": "available",
        "removed_from_sale_at": "",
    }
    for column, default in defaults.items():
        if column not in result.columns:
            result[column] = default
    return result


def ensure_batch_archive_columns(batches: pd.DataFrame) -> pd.DataFrame:
    result = batches.copy()
    for column in ["batch_status", "archived_at", "archived_note", "permanently_deleted_at", "removed_from_sale_at", "removed_from_sale_note"]:
        if column not in result.columns:
            result[column] = ""
    return result


def archive_batch(batch_number: str, note: str = "removed from sale in admin") -> tuple[int, bool]:
    today = date.today().isoformat()
    stones = load_stones()
    affected = 0
    if not stones.empty and "batch_number" in stones.columns:
        stones = ensure_soft_remove_columns(stones)
        batch_mask = stones["batch_number"].astype(str).eq(str(batch_number))
        status = stones["current_status"].fillna("").astype(str).str.strip().str.lower()
        active_mask = (batch_mask & ~status.eq("sold")).reindex(stones.index, fill_value=False).fillna(False).astype(bool)
        active_indexes = stones.index[active_mask]
        affected = int(len(active_indexes))
        if affected:
            stones.loc[active_indexes, "show_in_catalog"] = False
            stones.loc[active_indexes, "is_mvp_eligible"] = False
            stones.loc[active_indexes, "current_status"] = "removed_from_sale"
            stones.loc[active_indexes, "removed_from_sale_at"] = today
            save_stones(stones)

    batches = ensure_batch_archive_columns(load_batches())
    batch_marked = False
    if not batches.empty and "batch_number" in batches.columns:
        batch_mask = batches["batch_number"].astype(str).eq(str(batch_number))
        batch_marked = bool(batch_mask.any())
        if batch_marked:
            batches.loc[batch_mask, "batch_status"] = "archived"
            batches.loc[batch_mask, "archived_at"] = today
            batches.loc[batch_mask, "archived_note"] = note
            batches.loc[batch_mask, "removed_from_sale_at"] = today
            batches.loc[batch_mask, "removed_from_sale_note"] = note
            save_batches(batches)

    return affected, batch_marked


def archive_all_active_batches(note: str = "dev cleanup archive all") -> tuple[int, int]:
    batches = ensure_batch_archive_columns(load_batches())
    if batches.empty or "batch_number" not in batches.columns:
        return 0, 0
    active_batches = batches[active_batch_mask(batches)]["batch_number"].astype(str).tolist()
    affected_stones = 0
    affected_batches = 0
    for batch_number in active_batches:
        stones_count, batch_marked = archive_batch(batch_number, note=note)
        affected_stones += stones_count
        affected_batches += int(batch_marked)
    return affected_stones, affected_batches


def permanently_delete_batch(batch_number: str) -> tuple[int, int, int]:
    stones = load_stones()
    deleted_stones = 0
    if not stones.empty and "batch_number" in stones.columns:
        stone_mask = stones["batch_number"].astype(str).eq(str(batch_number))
        deleted_stones = int(stone_mask.sum())
        stones = stones[~stone_mask].copy()
        save_stones(stones)

    batches = load_batches()
    deleted_batch_rows = 0
    if not batches.empty and "batch_number" in batches.columns:
        batch_mask = batches["batch_number"].astype(str).eq(str(batch_number))
        deleted_batch_rows = int(batch_mask.sum())
        batches = batches[~batch_mask].copy()
        save_batches(batches)

    payments = load_batch_payments()
    deleted_payments = 0
    if not payments.empty and "batch_number" in payments.columns:
        payment_mask = payments["batch_number"].astype(str).eq(str(batch_number))
        deleted_payments = int(payment_mask.sum())
        payments = payments[~payment_mask].copy()
        save_batch_payments(payments)

    return deleted_stones, deleted_batch_rows, deleted_payments
