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
    build_public_stones_v1_csv_bytes,
)
from .schema import STONES_COLUMNS


PUBLISH_CONFIRMATION_TEXT = "ПОДТВЕРЖДАЮ ПУБЛИКАЦИЮ"
UNPUBLISH_CONFIRMATION_TEXT = "ПОДТВЕРЖДАЮ СНЯТИЕ С ПУБЛИКАЦИИ"
ARCHIVE_CONFIRMATION_TEXT = "ПОДТВЕРЖДАЮ АРХИВ"
EXPORT_CONFIRMATION_TEXT = "ПОДТВЕРЖДАЮ ЭКСПОРТ"
PUBLIC_EXPORT_FILENAME = "public_stones_v1.csv"
PUBLIC_EXPORT_SCHEMA_VERSION = "public_stones_v1"

PUBLIC_REQUIRED_FIELDS = [
    "shape",
    "weight",
    "color",
    "clarity",
    "public_price_display",
]

PUBLIC_EXPORT_COLUMNS = [
    "schema_version", "exported_at", "stone_id", "report_number", "lab",
    "catalog_section", "section_name", "public_card_status", "public_visibility_reason",
    "shape", "weight", "carat_label", "color", "clarity", "kurgin_score",
    "kurgin_score_range_label", "public_price_display", "price_display_type",
    "min_diameter", "max_diameter", "height", "depth_mm", "cut_grade",
    "symmetry", "polish", "fluorescence", "tags", "availability_status_public",
    "detail_available", "kurgin_report_available", "lab_report_available", "main_image_available",
]


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _has_text(value) -> bool:
    text = str(value).strip() if value is not None else ""
    return text.lower() not in {"", "nan", "none", "<na>"}


def _bool_text(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y", "да", "истина"}


def _number_or_none(value):
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except Exception:
        return None


def _positive_number(value) -> bool:
    number = _number_or_none(value)
    return number is not None and number > 0


def _shape_is_round(row: dict) -> bool:
    return str(row.get("shape", "")).strip().upper() == "ROUND"


def _score_required_for_public(row: dict) -> bool:
    return _shape_is_round(row)


def _score_ready_reason(row: dict) -> tuple[bool, str]:
    if not _score_required_for_public(row):
        return True, "KURGIN Score не требуется для не ROUND"
    if _has_text(row.get("kurgin_score", "")):
        return True, "KURGIN Score есть"
    return False, "для ROUND нужен KURGIN Score"


def _score_range_label(row: dict) -> str:
    score = _number_or_none(row.get("kurgin_score", ""))
    if score is None:
        if _shape_is_round(row):
            return ""
        return "Не применяется к форме"
    if score < 60:
        return "<60"
    if score < 70:
        return "60–69.99"
    if score < 80:
        return "70–79.99"
    if score < 90:
        return "80–89.99"
    if score < 95:
        return "90–94.99"
    return "95+"


def _normalize_fluorescence(value) -> str:
    text = str(value).strip() if value is not None else ""
    if text.lower() in {"", "nan", "none", "<na>"}:
        return "None"
    return text


def _carat_label(value) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        return ""
    number = _number_or_none(text)
    if number is None:
        return f"{text} ct"
    return f"{number:.2f} ct"


def _public_sections_lookup() -> dict:
    sections = read_catalog_sections()
    lookup = {}
    for _, row in sections.iterrows():
        sid = str(row.get("section_id", "")).strip()
        if not sid:
            continue
        lookup[sid] = {
            "section_name_ru": str(row.get("section_name_ru", sid)),
            "is_public": _bool_text(row.get("is_public", "false")),
        }
    return lookup


def _public_section_ids() -> set[str]:
    return {sid for sid, item in _public_sections_lookup().items() if item.get("is_public")}


def _price_ready_reason(row: dict) -> tuple[bool, str, str]:
    price_status = str(row.get("price_status", "")).strip().lower()
    price_display = str(row.get("public_price_display", "")).strip()
    allow_por = _bool_text(row.get("allow_price_on_request", "false"))

    if price_status == "calculated":
        if not price_display:
            return False, "нет public_price_display", ""
        if not _positive_number(row.get("public_price_total_rub", "")):
            return False, "нет положительной public_price_total_rub", ""
        return True, "числовая публичная цена готова", "numeric"

    if price_status == "missing_supplier_price":
        if allow_por and price_display == "Цена по запросу":
            return True, "разрешена цена по запросу", "price_on_request"
        return False, "нет цены поставщика и не включена цена по запросу", ""

    return False, f"неподходящий price_status: {price_status or 'пусто'}", ""


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

    score_ready, score_reason = _score_ready_reason(row)
    if not score_ready:
        return False, score_reason

    price_ready, price_reason, _price_type = _price_ready_reason(row)
    if not price_ready:
        return False, price_reason

    return True, "готов к публикации"


def build_publish_preview(stones: pd.DataFrame | None = None, stone_ids: list[str] | None = None) -> dict:
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
            "kurgin_score": item.get("kurgin_score", ""),
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
        "summary": {"selected": int(len(preview_df)), "ready": int(len(ready_df)), "blocked": int(len(blocked_df))},
    }


def _backup_with_export(label: str):
    backup_dir = backup_existing_files(label)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    export_path = EXPORTS_DIR / PUBLIC_EXPORT_FILENAME
    if export_path.exists():
        shutil.copy2(export_path, backup_dir / PUBLIC_EXPORT_FILENAME)
    return backup_dir


def commit_publish(stone_ids: list[str]) -> dict:
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

    return {"updated": int(mask.sum()), "backup_dir": str(backup_dir), "preview": preview, "message": "Камни опубликованы."}


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

    return {"updated": int(mask.sum()), "backup_dir": str(backup_dir), "preview": preview, "message": "Камни сняты с публикации."}


def commit_archive(stone_ids: list[str]) -> dict:
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


def build_public_export_preview_7d() -> dict:
    ensure_data_files()
    stones = read_stones()
    sections = _public_sections_lookup()
    generated_at = _now_iso()
    rows = []

    for _, stone in stones.iterrows():
        row = stone.to_dict()
        status = str(row.get("status", "")).strip().lower()
        availability = str(row.get("availability_status", "")).strip().lower()
        section_id = str(row.get("catalog_section", "")).strip()
        section = sections.get(section_id, {})
        if status != "published" or availability != "in_stock" or not section.get("is_public"):
            continue

        can_publish, _reason = _classify_for_publish(row, _public_section_ids())
        if not can_publish:
            continue

        _price_ready, price_reason, price_type = _price_ready_reason(row)
        public_card_status = "public_numeric_price" if price_type == "numeric" else "public_price_on_request"
        visibility_reason = "published / in_stock / public section / numeric price" if price_type == "numeric" else "published / in_stock / public section / price on request"
        depth_mm = row.get("depth_mm", "")

        rows.append({
            "schema_version": PUBLIC_EXPORT_SCHEMA_VERSION,
            "exported_at": generated_at,
            "stone_id": row.get("stone_id", ""),
            "report_number": row.get("report_number", ""),
            "lab": row.get("lab", ""),
            "catalog_section": section_id,
            "section_name": section.get("section_name_ru", ""),
            "public_card_status": public_card_status,
            "public_visibility_reason": visibility_reason,
            "shape": row.get("shape", ""),
            "weight": row.get("weight", ""),
            "carat_label": _carat_label(row.get("weight", "")),
            "color": row.get("color", ""),
            "clarity": row.get("clarity", ""),
            "kurgin_score": row.get("kurgin_score", ""),
            "kurgin_score_range_label": _score_range_label(row),
            "public_price_display": row.get("public_price_display", ""),
            "price_display_type": price_type,
            "min_diameter": row.get("min_diameter", ""),
            "max_diameter": row.get("max_diameter", ""),
            "height": row.get("height", depth_mm),
            "depth_mm": depth_mm,
            "cut_grade": row.get("cut", ""),
            "symmetry": row.get("symmetry", ""),
            "polish": row.get("polish", ""),
            "fluorescence": _normalize_fluorescence(row.get("fluorescence", "")),
            "tags": row.get("tags", ""),
            "availability_status_public": availability,
            "detail_available": "false",
            "kurgin_report_available": "false",
            "lab_report_available": "false",
            "main_image_available": "false",
        })

    export_df = pd.DataFrame(rows)
    for col in PUBLIC_EXPORT_COLUMNS:
        if col not in export_df.columns:
            export_df[col] = ""
    export_df = export_df[PUBLIC_EXPORT_COLUMNS] if not export_df.empty else pd.DataFrame(columns=PUBLIC_EXPORT_COLUMNS)
    numeric = int((export_df["price_display_type"].astype(str) == "numeric").sum()) if not export_df.empty else 0
    por = int((export_df["price_display_type"].astype(str) == "price_on_request").sum()) if not export_df.empty else 0
    non_round_without_score = 0
    if not export_df.empty:
        non_round_without_score = int(((export_df["shape"].astype(str).str.upper() != "ROUND") & (export_df["kurgin_score"].astype(str).str.strip() == "")).sum())

    return {
        "summary": {
            "filename": PUBLIC_EXPORT_FILENAME,
            "schema_version": PUBLIC_EXPORT_SCHEMA_VERSION,
            "generated_at": generated_at,
            "rows": int(len(export_df)),
            "numeric": numeric,
            "price_on_request": por,
            "non_round_without_score": non_round_without_score,
        },
        "export_df": export_df,
    }


def write_public_export_file() -> dict:
    ensure_data_files()
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    export_data = build_public_export_preview_7d()
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
