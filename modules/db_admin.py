from __future__ import annotations

from typing import Any

import pandas as pd

from .db import KURGIN_SCHEMA_NAME, _connect

STATUS_VALUES = ["draft", "ready", "published", "archived"]
AVAILABILITY_VALUES = ["in_stock", "reserved", "sold", "removed"]
SECTION_VALUES = ["main", "large"]


def get_db_stone(stone_id: str) -> dict[str, Any] | None:
    stone_id = str(stone_id).strip()
    if not stone_id:
        return None
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                select stone_id, status, availability_status, catalog_section,
                       shipment_id, report_number, stock_number, payload, updated_at
                from {KURGIN_SCHEMA_NAME}.stones
                where stone_id = %s
                """,
                (stone_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    keys = [
        "stone_id", "status", "availability_status", "catalog_section",
        "shipment_id", "report_number", "stock_number", "payload", "updated_at",
    ]
    return dict(zip(keys, row))


def update_db_stone_admin_fields(
    stone_id: str,
    status: str,
    availability_status: str,
    catalog_section: str,
) -> dict[str, Any]:
    stone_id = str(stone_id).strip()
    status = str(status).strip()
    availability_status = str(availability_status).strip()
    catalog_section = str(catalog_section).strip()

    if not stone_id:
        return {"ok": False, "error": "stone_id пустой."}
    if status not in STATUS_VALUES:
        return {"ok": False, "error": f"Некорректный status: {status}"}
    if availability_status not in AVAILABILITY_VALUES:
        return {"ok": False, "error": f"Некорректный availability_status: {availability_status}"}
    if catalog_section not in SECTION_VALUES:
        return {"ok": False, "error": f"Некорректный catalog_section: {catalog_section}"}

    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    update {KURGIN_SCHEMA_NAME}.stones
                    set status = %s,
                        availability_status = %s,
                        catalog_section = %s,
                        payload = jsonb_set(
                            jsonb_set(
                                jsonb_set(payload, '{{status}}', to_jsonb(%s::text), true),
                                '{{availability_status}}', to_jsonb(%s::text), true
                            ),
                            '{{catalog_section}}', to_jsonb(%s::text), true
                        ),
                        updated_at = now()
                    where stone_id = %s
                    returning stone_id
                    """,
                    (
                        status,
                        availability_status,
                        catalog_section,
                        status,
                        availability_status,
                        catalog_section,
                        stone_id,
                    ),
                )
                updated = cur.fetchone()
            conn.commit()
        if not updated:
            return {"ok": False, "error": "Камень не найден в PostgreSQL."}
        return {"ok": True, "error": "", "stone_id": stone_id}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def search_db_stones_for_admin(limit: int = 500) -> pd.DataFrame:
    limit = max(1, min(int(limit or 500), 1000))
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                select stone_id, report_number, stock_number, status,
                       availability_status, catalog_section, shipment_id, updated_at
                from {KURGIN_SCHEMA_NAME}.stones
                order by stone_id
                limit %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    return pd.DataFrame(
        rows,
        columns=[
            "stone_id", "report_number", "stock_number", "status",
            "availability_status", "catalog_section", "shipment_id", "updated_at",
        ],
    )
