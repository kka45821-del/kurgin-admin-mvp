from __future__ import annotations
from pathlib import Path
from .paths import RAW_DIR
from .storage import backup_existing_files

ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".webp", ".txt"}
MAX_FILES_PER_SHIPMENT = 5

def attachments_dir(shipment_id: str) -> Path:
    path = RAW_DIR / str(shipment_id) / "attachments"
    path.mkdir(parents=True, exist_ok=True)
    return path

def list_attachments(shipment_id: str) -> list[Path]:
    path = attachments_dir(shipment_id)
    return sorted([p for p in path.iterdir() if p.is_file()])

def save_attachment(shipment_id: str, uploaded_file) -> dict:
    files = list_attachments(shipment_id)
    if len(files) >= MAX_FILES_PER_SHIPMENT:
        return {"ok": False, "message": "У поставки уже 5 файлов."}
    original_name = Path(uploaded_file.name).name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return {"ok": False, "message": f"Тип файла не разрешён: {suffix}"}
    backup_dir = backup_existing_files(f"before_add_attachment_{shipment_id}")
    path = attachments_dir(shipment_id) / original_name
    i = 1
    while path.exists():
        path = attachments_dir(shipment_id) / f"{Path(original_name).stem}_{i}{suffix}"
        i += 1
    path.write_bytes(uploaded_file.getvalue())
    return {"ok": True, "message": "Файл прикреплён.", "path": str(path), "backup_dir": str(backup_dir)}

def delete_attachment(shipment_id: str, filename: str) -> dict:
    path = attachments_dir(shipment_id) / Path(filename).name
    if not path.exists():
        return {"ok": False, "message": "Файл не найден."}
    backup_dir = backup_existing_files(f"before_delete_attachment_{shipment_id}")
    path.unlink()
    return {"ok": True, "message": "Файл удалён.", "backup_dir": str(backup_dir)}
