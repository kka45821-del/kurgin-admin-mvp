from __future__ import annotations

from typing import Any

import pandas as pd

from .db import KURGIN_SCHEMA_NAME, _connect, get_core_tables_status
from .storage import read_stones


DB_STONE_VIEW_COLUMNS = [
    "stone_id",
    "report_number",
    "stock_number",
    "shape",
    "weight",
    "color",
    "clarity",
    "fluorescence",
    "kurgin_score",
    "status",
    "availability_status",
    "catalog_section",
    "shipment_id",
    "updated_at",
]


def _payload_value(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key, "") if isinstance(payload, dict) else ""
    return "" if value is None else str(value)


def read_db_stones(limit: int = 1000) -> pd.DataFrame:
    """Read KURGIN stones from PostgreSQL into a flat DataFrame.

    Read-only. Does not mutate database or CSV files.
    """
    limit = max(1, min(int(limit or 1000), 5000))
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                select
                    stone_id,
                    status,
                    availability_status,
                    catalog_section,
                    shipment_id,
                    report_number,
                    stock_number,
                    payload,
                    updated_at
                from {KURGIN_SCHEMA_NAME}.stones
                order by stone_id
                limit %s
                """,
                (limit,),
            )
            rows = cur.fetchall()

    records = []
    for row in rows:
        stone_id, status, availability, section, shipment_id, report_number, stock_number, payload, updated_at = row
        payload = payload or {}
        records.append({
            "stone_id": str(stone_id or ""),
            "report_number": str(report_number or _payload_value(payload, "report_number")),
            "stock_number": str(stock_number or _payload_value(payload, "stock_number")),
            "shape": _payload_value(payload, "shape"),
            "weight": _payload_value(payload, "weight"),
            "color": _payload_value(payload, "color"),
            "clarity": _payload_value(payload, "clarity"),
            "fluorescence": _payload_value(payload, "fluorescence"),
            "kurgin_score": _payload_value(payload, "kurgin_score"),
            "status": str(status or ""),
            "availability_status": str(availability or ""),
            "catalog_section": str(section or ""),
            "shipment_id": str(shipment_id or ""),
            "updated_at": str(updated_at or ""),
        })

    df = pd.DataFrame(records)
    for col in DB_STONE_VIEW_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[DB_STONE_VIEW_COLUMNS]


def db_stones_summary() -> dict[str, Any]:
    core = get_core_tables_status()
    if not core.get("ok") or not core.get("core_ready"):
        return {"ok": False, "error": "Core tables are not ready.", "summary": {}, "counts": {}}

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f"select count(*) from {KURGIN_SCHEMA_NAME}.stones")
            total = int(cur.fetchone()[0])
            cur.execute(f"select count(*) from {KURGIN_SCHEMA_NAME}.stones where status = 'published'")
            published = int(cur.fetchone()[0])
            cur.execute(f"select count(*) from {KURGIN_SCHEMA_NAME}.stones where availability_status = 'in_stock'")
            in_stock = int(cur.fetchone()[0])
            cur.execute(f"select count(*) from {KURGIN_SCHEMA_NAME}.shipments")
            shipments = int(cur.fetchone()[0])
            cur.execute(f"select count(*) from {KURGIN_SCHEMA_NAME}.import_log")
            import_log = int(cur.fetchone()[0])

    csv_stones = read_stones()
    csv_total = int(len(csv_stones))
    return {
        "ok": True,
        "error": "",
        "summary": {
            "db_stones": total,
            "csv_stones": csv_total,
            "delta": total - csv_total,
            "published": published,
            "in_stock": in_stock,
            "shipments": shipments,
            "import_log": import_log,
        },
        "counts": core.get("counts", {}),
    }
