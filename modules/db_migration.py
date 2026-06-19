from __future__ import annotations

import json
from typing import Any

import pandas as pd

from .db import KURGIN_SCHEMA_NAME, _connect, get_core_tables_status
from .storage import read_stones, read_shipments, read_import_log


MIGRATION_ID = "0003_csv_to_postgres"


def _records_from_df(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    clean = df.fillna("").copy()
    return [{str(k): ("" if v is None else str(v)) for k, v in row.items()} for row in clean.to_dict(orient="records")]


def _count_missing_key(records: list[dict[str, Any]], key: str) -> int:
    return sum(1 for row in records if not str(row.get(key, "")).strip())


def _db_count(table_name: str) -> int:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f"select count(*) from {KURGIN_SCHEMA_NAME}.{table_name}")
            return int(cur.fetchone()[0])


def build_csv_to_postgres_preview() -> dict[str, Any]:
    """Read-only preview of CSV rows that can be migrated into PostgreSQL."""
    core = get_core_tables_status()
    if not core.get("ok") or not core.get("core_ready"):
        return {
            "ok": False,
            "ready": False,
            "error": "Минимальные таблицы PostgreSQL не готовы.",
            "summary": {},
            "tables": [],
        }

    stones_records = _records_from_df(read_stones())
    shipments_records = _records_from_df(read_shipments())
    import_log_records = _records_from_df(read_import_log())

    tables = [
        {
            "table": "stones",
            "csv_rows": len(stones_records),
            "db_rows_before": _db_count("stones"),
            "missing_key": _count_missing_key(stones_records, "stone_id"),
            "key": "stone_id",
        },
        {
            "table": "shipments",
            "csv_rows": len(shipments_records),
            "db_rows_before": _db_count("shipments"),
            "missing_key": _count_missing_key(shipments_records, "shipment_id"),
            "key": "shipment_id",
        },
        {
            "table": "import_log",
            "csv_rows": len(import_log_records),
            "db_rows_before": _db_count("import_log"),
            "missing_key": _count_missing_key(import_log_records, "import_id"),
            "key": "import_id",
        },
        {
            "table": "public_exports",
            "csv_rows": 0,
            "db_rows_before": _db_count("public_exports"),
            "missing_key": 0,
            "key": "export_id",
        },
    ]

    blockers = []
    if len(stones_records) == 0:
        blockers.append("В CSV нет камней для миграции.")
    for item in tables[:3]:
        if item["csv_rows"] > 0 and item["missing_key"] > 0:
            blockers.append(f"{item['table']}: есть строки без ключа {item['key']}: {item['missing_key']}")

    return {
        "ok": True,
        "ready": len(blockers) == 0,
        "error": "",
        "blockers": blockers,
        "summary": {
            "stones_csv_rows": len(stones_records),
            "shipments_csv_rows": len(shipments_records),
            "import_log_csv_rows": len(import_log_records),
            "total_csv_rows": len(stones_records) + len(shipments_records) + len(import_log_records),
        },
        "tables": tables,
    }


def _json_payload(row: dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=False, sort_keys=True)


def _upsert_stones(cur, records: list[dict[str, Any]]) -> int:
    count = 0
    for row in records:
        stone_id = str(row.get("stone_id", "")).strip()
        if not stone_id:
            continue
        cur.execute(
            f"""
            insert into {KURGIN_SCHEMA_NAME}.stones (
                stone_id, status, availability_status, catalog_section,
                shipment_id, report_number, stock_number, payload, updated_at
            ) values (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, now())
            on conflict (stone_id) do update set
                status = excluded.status,
                availability_status = excluded.availability_status,
                catalog_section = excluded.catalog_section,
                shipment_id = excluded.shipment_id,
                report_number = excluded.report_number,
                stock_number = excluded.stock_number,
                payload = excluded.payload,
                updated_at = now()
            """,
            (
                stone_id,
                str(row.get("status", "draft") or "draft"),
                str(row.get("availability_status", "in_stock") or "in_stock"),
                str(row.get("catalog_section", "")),
                str(row.get("shipment_id", "")),
                str(row.get("report_number", "")),
                str(row.get("stock_number", "")),
                _json_payload(row),
            ),
        )
        count += 1
    return count


def _upsert_shipments(cur, records: list[dict[str, Any]]) -> int:
    count = 0
    for row in records:
        shipment_id = str(row.get("shipment_id", "")).strip()
        if not shipment_id:
            continue
        cur.execute(
            f"""
            insert into {KURGIN_SCHEMA_NAME}.shipments (
                shipment_id, supplier_name, shipment_date, payload, updated_at
            ) values (%s, %s, %s, %s::jsonb, now())
            on conflict (shipment_id) do update set
                supplier_name = excluded.supplier_name,
                shipment_date = excluded.shipment_date,
                payload = excluded.payload,
                updated_at = now()
            """,
            (
                shipment_id,
                str(row.get("supplier_name", "")),
                str(row.get("shipment_date", "")),
                _json_payload(row),
            ),
        )
        count += 1
    return count


def _upsert_import_log(cur, records: list[dict[str, Any]]) -> int:
    count = 0
    for row in records:
        import_id = str(row.get("import_id", "")).strip()
        if not import_id:
            continue
        cur.execute(
            f"""
            insert into {KURGIN_SCHEMA_NAME}.import_log (
                import_id, source_file, status, payload
            ) values (%s, %s, %s, %s::jsonb)
            on conflict (import_id) do update set
                source_file = excluded.source_file,
                status = excluded.status,
                payload = excluded.payload
            """,
            (
                import_id,
                str(row.get("source_file", "")),
                str(row.get("status", "")),
                _json_payload(row),
            ),
        )
        count += 1
    return count


def migrate_csv_to_postgres() -> dict[str, Any]:
    """Migrate current CSV rows into PostgreSQL using upsert. Does not delete rows."""
    preview = build_csv_to_postgres_preview()
    if not preview.get("ok") or not preview.get("ready"):
        return {"ok": False, "error": "; ".join(preview.get("blockers", [])) or preview.get("error", "Миграция не готова."), "preview": preview}

    stones_records = _records_from_df(read_stones())
    shipments_records = _records_from_df(read_shipments())
    import_log_records = _records_from_df(read_import_log())

    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                stones_upserted = _upsert_stones(cur, stones_records)
                shipments_upserted = _upsert_shipments(cur, shipments_records)
                import_log_upserted = _upsert_import_log(cur, import_log_records)
                cur.execute(
                    f"""
                    insert into {KURGIN_SCHEMA_NAME}.schema_migrations (migration_id, comment)
                    values (%s, %s)
                    on conflict (migration_id) do nothing
                    """,
                    (MIGRATION_ID, "Upsert CSV data into KURGIN Admin PostgreSQL tables"),
                )
            conn.commit()

        after = get_core_tables_status()
        return {
            "ok": True,
            "error": "",
            "upserted": {
                "stones": stones_upserted,
                "shipments": shipments_upserted,
                "import_log": import_log_upserted,
                "public_exports": 0,
            },
            "after": after,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "preview": preview}
