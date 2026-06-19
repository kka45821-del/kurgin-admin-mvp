from __future__ import annotations

from typing import Any

import pandas as pd

from .db import KURGIN_SCHEMA_NAME, _connect
from .db_core import mass_update_stones, build_public_export_from_db


def _payload_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key, "") if isinstance(payload, dict) else ""
    return "" if value is None else str(value)


def _float_positive(value) -> bool:
    try:
        return float(str(value).replace(" ", "").replace(",", ".")) > 0
    except Exception:
        return False


def _is_true(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "да"}


def _price_group(payload: dict[str, Any]) -> str:
    price_status = _payload_text(payload, "price_status").strip()
    price_display = _payload_text(payload, "public_price_display").strip()
    allow_por = _is_true(_payload_text(payload, "allow_price_on_request"))
    total_rub = _payload_text(payload, "public_price_total_rub")

    if price_status == "calculated" and price_display and _float_positive(total_rub):
        return "numeric_ready"
    if allow_por and price_display == "Цена по запросу":
        return "price_on_request_ready"
    if price_status or price_display or allow_por:
        return "price_incomplete"
    return "missing_price"


def build_pricing_audit(limit: int = 5000) -> dict[str, Any]:
    limit = max(1, min(int(limit or 5000), 10000))
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                select stone_id, status, availability_status, catalog_section,
                       report_number, stock_number, payload, updated_at
                from {KURGIN_SCHEMA_NAME}.stones
                order by stone_id
                limit %s
                """,
                (limit,),
            )
            rows = cur.fetchall()

    records = []
    for stone_id, status, availability, section, report_number, stock_number, payload, updated_at in rows:
        payload = payload or {}
        group = _price_group(payload)
        public_ready = group in {"numeric_ready", "price_on_request_ready"}
        export_ready = str(status) == "published" and str(availability) == "in_stock" and public_ready
        records.append({
            "stone_id": str(stone_id or ""),
            "report_number": str(report_number or _payload_text(payload, "report_number")),
            "stock_number": str(stock_number or _payload_text(payload, "stock_number")),
            "shape": _payload_text(payload, "shape"),
            "weight": _payload_text(payload, "weight"),
            "color": _payload_text(payload, "color"),
            "clarity": _payload_text(payload, "clarity"),
            "status": str(status or ""),
            "availability_status": str(availability or ""),
            "catalog_section": str(section or ""),
            "price_group": group,
            "price_status": _payload_text(payload, "price_status"),
            "price_source": _payload_text(payload, "price_source"),
            "public_price_display": _payload_text(payload, "public_price_display"),
            "public_price_total_rub": _payload_text(payload, "public_price_total_rub"),
            "allow_price_on_request": _payload_text(payload, "allow_price_on_request"),
            "public_ready": "yes" if public_ready else "no",
            "export_ready": "yes" if export_ready else "no",
            "updated_at": str(updated_at or ""),
        })

    df = pd.DataFrame(records)
    if df.empty:
        df = pd.DataFrame(columns=[
            "stone_id", "report_number", "stock_number", "shape", "weight", "color", "clarity",
            "status", "availability_status", "catalog_section", "price_group", "price_status",
            "price_source", "public_price_display", "public_price_total_rub", "allow_price_on_request",
            "public_ready", "export_ready", "updated_at",
        ])

    def count_mask(col: str, value: str) -> int:
        return int((df[col].astype(str) == value).sum()) if col in df.columns else 0

    export_info = build_public_export_from_db()
    summary = {
        "total": int(len(df)),
        "numeric_ready": count_mask("price_group", "numeric_ready"),
        "price_on_request_ready": count_mask("price_group", "price_on_request_ready"),
        "price_incomplete": count_mask("price_group", "price_incomplete"),
        "missing_price": count_mask("price_group", "missing_price"),
        "published": count_mask("status", "published"),
        "in_stock": count_mask("availability_status", "in_stock"),
        "public_ready": count_mask("public_ready", "yes"),
        "export_ready": count_mask("export_ready", "yes"),
        "export_rows": int(export_info.get("rows", 0)),
        "export_skipped_without_public_price": int(export_info.get("skipped_without_public_price", 0)),
    }
    return {"df": df, "summary": summary, "export_info": export_info}


def enable_price_on_request(stone_ids: list[str]) -> dict[str, Any]:
    ids = [str(x).strip() for x in (stone_ids or []) if str(x).strip()]
    if not ids:
        return {"ok": False, "updated": 0, "error": "Не выбраны камни."}

    placeholders = ",".join(["%s"] * len(ids))
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    update {KURGIN_SCHEMA_NAME}.stones
                    set payload = jsonb_set(
                        jsonb_set(
                            jsonb_set(
                                jsonb_set(payload, '{{allow_price_on_request}}', to_jsonb('true'::text), true),
                                '{{public_price_display}}', to_jsonb('Цена по запросу'::text), true
                            ),
                            '{{price_status}}', to_jsonb('missing_supplier_price'::text), true
                        ),
                        '{{price_source}}', to_jsonb('not_calculated'::text), true
                    ),
                    updated_at = now()
                    where stone_id in ({placeholders})
                      and not (
                        payload->>'public_price_display' = 'Цена по запросу'
                        and lower(coalesce(payload->>'allow_price_on_request', '')) = 'true'
                      )
                    returning stone_id
                    """,
                    tuple(ids),
                )
                updated_ids = [row[0] for row in cur.fetchall()]
            conn.commit()
        return {"ok": True, "updated": len(updated_ids), "updated_ids": updated_ids, "error": ""}
    except Exception as exc:
        return {"ok": False, "updated": 0, "error": str(exc)}


def publish_price_ready(stone_ids: list[str]) -> dict[str, Any]:
    audit = build_pricing_audit()
    df = audit.get("df", pd.DataFrame())
    ids = set(str(x).strip() for x in (stone_ids or []) if str(x).strip())
    if not ids:
        return {"ok": False, "updated": 0, "error": "Не выбраны камни."}
    ready_ids = df[(df["stone_id"].astype(str).isin(ids)) & (df["public_ready"].astype(str) == "yes")]["stone_id"].astype(str).tolist()
    if not ready_ids:
        return {"ok": False, "updated": 0, "error": "Среди выбранных нет price-ready камней."}
    return mass_update_stones(ready_ids, status="published")
