from __future__ import annotations

from datetime import datetime
import shutil
import pandas as pd

from .paths import EXPORTS_DIR, STONES_FILE
from .storage import (
    ensure_data_files,
    read_stones,
    read_catalog_sections,
    backup_existing_files,
    atomic_write_csv,
    build_public_layer_preview,
    build_public_export_preview,
    build_public_stones_v1_csv_bytes,
)
from .schema import STONES_COLUMNS


PUBLISH_CONFIRMATION_TEXT = "ПОДТВЕРЖДАЮ ПУБЛИКАЦИЮ"
UNPUBLISH_CONFIRMATION_TEXT = "ПОДТВЕРЖДАЮ СНЯТИЕ С ПУБЛИКАЦИИ"
ARCHIVE_CONFIRMATION_TEXT = "ПОДТВЕРЖДАЮ АРХИВ"
EXPORT_CONFIRMATION_TEXT = "ПОДТВЕРЖДАЮ ЭКСПОРТ"
PUBLIC_EXPORT_FILENAME = "public_stones_v1.csv"

PUBLIC_REQUIRED_FIELDS = [
    "shape",
    "weight",
    "color",
    "clarity",
    "kurgin_score",
    "public_price_display",
]


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _has_text(value) -> bool:
    text = str(value).strip() if value is not None else ""
    return text.lower() not in {"", "nan", "none", "<na>"}


def _bool_text(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y", "да", "истина"}


def _positive_number(value) -> bool:
    try:
        return float(str(value).replace(" ", "").replace(",", ".")) > 0
    except Exception:
        return False


def _public_section_ids() -> set[str]:
    sections = read_catalog_sections()
    if sections.empty:
        return set()
    mask = sections["is_public"].map(_bool_text) if "is_public" in sections.columns else pd.Series(False, index=sections.index)
    return set(sections.loc[mask, "section_id"].astype(str).str.strip().tolist())


def _price_ready_reason(row: dict) -> tuple[bool, str]:
    price_status = str(row.get("price_status", "")).strip().lower()
    price_display = str(row.get("public_price_display", "")).strip()
    allow_por = _bool_text(row.get("allow_price_on_request", "false"))

    if price_status == "calculated":
        if not price_display:
            return False, "нет public_price_display"
        if not _positive_number(row.get("public_price_total_rub", "")):
            return False, "нет положительной public_price_total_rub"
        return True, "числовая публичная цена готова"

    if price_status == "missing_supplier_price":
        if allow_por and price_display == "Цена по запросу":
            return True, "разрешена цена по запросу"
        return False, "нет цены поставщика и не включена цена по запросу"

    return False, f"неподходящий price_status: {price_status or 'пусто'}"


def _classify_for_publish(row: dict, public_sections: set[str]) -> tuple[bool, str]:
    status = str(row.get("status", "")).strip().lower()
    availability = str(row.get("availability_status", "")).strip().lower()
    section = str(row.get("catalog_section", "")).strip()

    if status == "archived":
        return False, "камень в архиве"
    if status == "published":
        return False, "уже опубликован"
    if availability != "in_stock":
        return False, f"наличие не in_stock: {availability or 'пусто'}"
    if section not in public_sections:
        return False, f"раздел не публичный или не найден: {section or 'пусто'}"

    missing = []
    for field in PUBLIC_REQUIRED_FIELDS:
        if not _has_text(row.get(field, "")):
            missing.append(field)
    if missing:
        return False, "не заполнены обязательные public-поля: " + ", ".join(missing)

    price_ready, price_reason = _price_ready_reason(row)
    if not price_ready:
        return False, price_reason

    return True, "готов к публикации"


def build_publish_preview(stones: pd.DataFrame | None = None, stone_ids: list[str] | None = None) -> dict:
    """Build a dry-run preview for setting selected stones to status=published."""
    ensure_data_files()
    df = stones.copy() if stones is not None else read_stones()
    for col in STONES_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    ids = [str(x) for x in (stone_ids or []) if str(x).strip()]
    if stone_ids is not None and not ids:
        df = df.iloc[0:0].copy()
    elif ids:
        df = df[df["stone_id"].astype(str).isin(ids)].copy()

    public_sections = _public_section_ids()
    rows = []
    for _, row in df.iterrows():
        item = row.to_dict()
        can_publish, reason = _classify_for_publish(item, public_sections)
        rows.append({
            "stone_id": item.get("stone_id", ""),
            "report_number": item.get("report_number", ""),
            "shipment_id": item.get("shipment_id", ""),
            "shape": item.get("shape", ""),
            "weight": item.get("weight", ""),
            "color": item.get("color", ""),
            "clarity": item.get("clarity", ""),
            "status": item.get("status", ""),
            "availability_status": item.get("availability_status", ""),
            "catalog_section": item.get("catalog_section", ""),
            "public_price_display": item.get("public_price_display", ""),
            "price_status": item.get("price_status", ""),
            "allow_price_on_request": item.get("allow_price_on_request", ""),
            "action": "publish" if can_publish else "skip",
            "can_publish": can_publish,
            "reason": reason,
        })

    preview_df = pd.DataFrame(rows)
    ready_df = preview_df[preview_df["can_publish"] == True].copy() if not preview_df.empty else pd.DataFrame()
    blocked_df = preview_df[preview_df["can_publish"] != True].copy() if not preview_df.empty else pd.DataFrame()
    return {
        "preview_df": preview_df,
        "ready_df": ready_df,
        "blocked_df": blocked_df,
        "summary": {
            "selected": int(len(preview_df)),
            "ready": int(len(ready_df)),
            "blocked": int(len(blocked_df)),
        },
    }


def _backup_with_export(label: str):
    backup_dir = backup_existing_files(label)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    export_path = EXPORTS_DIR / PUBLIC_EXPORT_FILENAME
    if export_path.exists():
        shutil.copy2(export_path, backup_dir / PUBLIC_EXPORT_FILENAME)
    return backup_dir


def commit_publish(stone_ids: list[str]) -> dict:
    """Set ready selected stones to published. Skipped stones are not mutated."""
    ensure_data_files()
    ids = [str(x) for x in (stone_ids or []) if str(x).strip()]
    if not ids:
        return {"updated": 0, "backup_dir": "", "preview": build_publish_preview(read_stones(), []), "message": "Не выбраны камни для публикации."}

    stones = read_stones()
    preview = build_publish_preview(stones, ids)
    ready_df = preview.get("ready_df", pd.DataFrame())
    ready_ids = ready_df["stone_id"].astype(str).tolist() if not ready_df.empty else []

    if not ready_ids:
        return {"updated": 0, "backup_dir": "", "preview": preview, "message": "Нет камней, готовых к публикации."}

    backup_dir = _backup_with_export("before_stage_7d_publish")
    mask = stones["stone_id"].astype(str).isin(ready_ids)
    stones.loc[mask, "status"] = "published"
    stones.loc[mask, "updated_at"] = _now_iso()
    atomic_write_csv(stones, STONES_FILE)

    return {
        "updated": int(mask.sum()),
        "backup_dir": str(backup_dir),
        "preview": preview,
        "message": "Камни опубликованы.",
    }


def build_unpublish_preview(stones: pd.DataFrame | None = None, stone_ids: list[str] | None = None) -> dict:
    ensure_data_files()
    df = stones.copy() if stones is not None else read_stones()
    ids = [str(x) for x in (stone_ids or []) if str(x).strip()]
    if stone_ids is not None and not ids:
        df = df.iloc[0:0].copy()
    elif ids:
        df = df[df["stone_id"].astype(str).isin(ids)].copy()

    rows = []
    for _, row in df.iterrows():
        status = str(row.get("status", "")).strip().lower()
        can_unpublish = status == "published"
        rows.append({
            "stone_id": row.get("stone_id", ""),
            "report_number": row.get("report_number", ""),
            "shipment_id": row.get("shipment_id", ""),
            "status": row.get("status", ""),
            "availability_status": row.get("availability_status", ""),
            "catalog_section": row.get("catalog_section", ""),
            "action": "set_ready" if can_unpublish else "skip",
            "can_unpublish": can_unpublish,
            "reason": "будет снят с публикации: status published → ready" if can_unpublish else "не опубликован",
        })
    preview_df = pd.DataFrame(rows)
    ready_df = preview_df[preview_df["can_unpublish"] == True].copy() if not preview_df.empty else pd.DataFrame()
    blocked_df = preview_df[preview_df["can_unpublish"] != True].copy() if not preview_df.empty else pd.DataFrame()
    return {
        "preview_df": preview_df,
        "ready_df": ready_df,
        "blocked_df": blocked_df,
        "summary": {"selected": int(len(preview_df)), "ready": int(len(ready_df)), "blocked": int(len(blocked_df))},
    }


def commit_unpublish(stone_ids: list[str]) -> dict:
    """Remove selected published stones from the public layer by setting status=ready."""
    ensure_data_files()
    ids = [str(x) for x in (stone_ids or []) if str(x).strip()]
    if not ids:
        return {"updated": 0, "backup_dir": "", "preview": build_unpublish_preview(read_stones(), []), "message": "Не выбраны камни для снятия с публикации."}

    stones = read_stones()
    preview = build_unpublish_preview(stones, ids)
    ready_df = preview.get("ready_df", pd.DataFrame())
    ready_ids = ready_df["stone_id"].astype(str).tolist() if not ready_df.empty else []

    if not ready_ids:
        return {"updated": 0, "backup_dir": "", "preview": preview, "message": "Нет опубликованных камней для снятия."}

    backup_dir = _backup_with_export("before_stage_7d_unpublish")
    mask = stones["stone_id"].astype(str).isin(ready_ids)
    stones.loc[mask, "status"] = "ready"
    stones.loc[mask, "updated_at"] = _now_iso()
    atomic_write_csv(stones, STONES_FILE)

    return {
        "updated": int(mask.sum()),
        "backup_dir": str(backup_dir),
        "preview": preview,
        "message": "Камни сняты с публикации.",
    }


def commit_archive(stone_ids: list[str]) -> dict:
    """Archive selected stones. Archived stones never enter the public export."""
    ensure_data_files()
    ids = [str(x) for x in (stone_ids or []) if str(x).strip()]
    if not ids:
        return {"updated": 0, "backup_dir": "", "message": "Не выбраны камни для архива."}

    stones = read_stones()
    backup_dir = _backup_with_export("before_stage_7d_archive")
    mask = stones["stone_id"].astype(str).isin(ids)
    stones.loc[mask, "status"] = "archived"
    stones.loc[mask, "updated_at"] = _now_iso()
    atomic_write_csv(stones, STONES_FILE)
    return {"updated": int(mask.sum()), "backup_dir": str(backup_dir), "message": "Камни отправлены в архив."}


def write_public_export_file() -> dict:
    """Write exports/public_stones_v1.csv from the current public-layer rules."""
    ensure_data_files()
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    public_data = build_public_layer_preview()
    export_data = build_public_export_preview(public_data)
    export_df = export_data.get("export_df", pd.DataFrame())
    export_summary = export_data.get("summary", {})

    backup_dir = _backup_with_export("before_stage_7d_public_export")
    export_path = EXPORTS_DIR / PUBLIC_EXPORT_FILENAME
    export_path.write_bytes(build_public_stones_v1_csv_bytes(export_df))

    return {
        "written": True,
        "path": str(export_path),
        "backup_dir": str(backup_dir),
        "summary": export_summary,
        "export_df": export_df,
    }
