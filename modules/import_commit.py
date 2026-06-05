from __future__ import annotations

from datetime import datetime
import pandas as pd

from .paths import RAW_DIR, STONES_FILE, SHIPMENTS_FILE, IMPORT_LOG_FILE
from .schema import STONES_COLUMNS, SHIPMENTS_COLUMNS, IMPORT_LOG_COLUMNS
from .storage import backup_existing_files, append_csv


def commit_import(import_id, uploaded_bytes, workbook, saved_stones, not_saved_count, stats, shipment, original_filename, excel_template_version):
    backup_dir = backup_existing_files(f"before_import_{import_id}")

    raw_dir = RAW_DIR / import_id
    raw_dir.mkdir(parents=True, exist_ok=True)

    original_path = raw_dir / "original.xlsx"
    original_path.write_bytes(uploaded_bytes)

    workbook["Results"].to_csv(raw_dir / "results_full.csv", index=False)
    workbook["Details"].to_csv(raw_dir / "details_full.csv", index=False)
    workbook["Issues"].to_csv(raw_dir / "issues_full.csv", index=False)
    workbook["System"].to_csv(raw_dir / "system_info.csv", index=False)

    imported_at = datetime.now().isoformat(timespec="seconds")

    shipment_row = pd.DataFrame([{
        "shipment_id": import_id,
        "import_id": import_id,
        "supplier_name": shipment.get("supplier_name", ""),
        "shipment_date": shipment.get("shipment_date", ""),
        "shipment_name": shipment.get("shipment_name", ""),
        "currency": shipment.get("currency", ""),
        "total_purchase_cost": shipment.get("total_purchase_cost", ""),
        "advance_paid": shipment.get("advance_paid", ""),
        "payment_comment": shipment.get("payment_comment", ""),
        "comment": shipment.get("comment", ""),
        "original_filename": original_filename,
        "stored_filename": "original.xlsx",
        "source_file_path": str(original_path),
        "created_at": imported_at,
    }])

    log_row = pd.DataFrame([{
        "import_id": import_id,
        "source_file": original_filename,
        "original_filename": original_filename,
        "stored_filename": "original.xlsx",
        "imported_at": imported_at,
        "excel_template_version": excel_template_version,
        "rows_total": stats.get("total", 0),
        "rows_saved": stats.get("saved", 0),
        "rows_not_saved": not_saved_count,
        "warnings_count": stats.get("warnings", 0),
        "conflicts_count": stats.get("conflicts", 0),
        "status": "confirmed",
        "message": "Поставка успешно импортирована",
    }])

    append_csv(STONES_FILE, STONES_COLUMNS, saved_stones)
    append_csv(SHIPMENTS_FILE, SHIPMENTS_COLUMNS, shipment_row)
    append_csv(IMPORT_LOG_FILE, IMPORT_LOG_COLUMNS, log_row)

    return {"backup_dir": str(backup_dir), "raw_dir": str(raw_dir), "original_path": str(original_path)}
