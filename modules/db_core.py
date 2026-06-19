from __future__ import annotations

from datetime import datetime
from typing import Any
import json

import pandas as pd

from .db import KURGIN_SCHEMA_NAME, _connect
from .db_admin import STATUS_VALUES, AVAILABILITY_VALUES, SECTION_VALUES
from .db_read import read_db_stones

PUBLIC_EXPORT_COLUMNS = [
    "schema_version", "exported_at", "stone_id", "report_number", "lab",
    "catalog_section", "section_name", "public_card_status", "public_visibility_reason",
    "shape", "weight", "carat_label", "color", "clarity", "kurgin_score",
    "kurgin_score_range_label", "public_price_display", "price_display_type",
    "min_diameter", "max_diameter", "height", "depth_mm", "cut_grade",
    "symmetry", "polish", "fluorescence", "tags", "availability_status_public",
    "detail_available", "kurgin_report_available", "lab_report_available", "main_image_available",
]


def _payload_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key, "") if isinstance(payload, dict) else ""
    return "" if value is None else str(value)


def _float_or_none(value):
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except Exception:
        return None


def _carat_label(value) -> str:
    number = _float_or_none(value)
    if number is None:
        text = str(value or "").strip()
        return f"{text} ct" if text else ""
    return f"{number:.2f} ct"


def _score_range_label(row: dict[str, Any]) -> str:
    shape = str(row.get("shape", "")).upper().strip()
    score = _float_or_none(row.get("kurgin_score", ""))
    if score is None:
        return "" if shape == "ROUND" else "Не применяется к форме"
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
    text = str(value or "").strip()
    if text.lower() in {"", "nan", "none", "<na>"}:
        return "None"
    return text


def mass_update_stones(
    stone_ids: list[str],
    status: str | None = None,
    availability_status: str | None = None,
    catalog_section: str | None = None,
) -> dict[str, Any]:
    ids = [str(x).strip() for x in (stone_ids or []) if str(x).strip()]
    if not ids:
        return {"ok": False, "updated": 0, "error": "Не выбраны камни."}
    if status is not None and status not in STATUS_VALUES:
        return {"ok": False, "updated": 0, "error": f"Некорректный status: {status}"}
    if availability_status is not None and availability_status not in AVAILABILITY_VALUES:
        return {"ok": False, "updated": 0, "error": f"Некорректный availability_status: {availability_status}"}
    if catalog_section is not None and catalog_section not in SECTION_VALUES:
        return {"ok": False, "updated": 0, "error": f"Некорректный catalog_section: {catalog_section}"}

    set_parts = []
    params: list[Any] = []
    payload_expr = "payload"

    if status is not None:
        set_parts.append("status = %s")
        params.append(status)
        payload_expr = f"jsonb_set({payload_expr}, '{{status}}', to_jsonb(%s::text), true)"
        params.append(status)
    if availability_status is not None:
        set_parts.append("availability_status = %s")
        params.append(availability_status)
        payload_expr = f"jsonb_set({payload_expr}, '{{availability_status}}', to_jsonb(%s::text), true)"
        params.append(availability_status)
    if catalog_section is not None:
        set_parts.append("catalog_section = %s")
        params.append(catalog_section)
        payload_expr = f"jsonb_set({payload_expr}, '{{catalog_section}}', to_jsonb(%s::text), true)"
        params.append(catalog_section)

    if not set_parts:
        return {"ok": False, "updated": 0, "error": "Нет изменений для записи."}

    placeholders = ",".join(["%s"] * len(ids))
    params.extend(ids)
    sql = f"""
        update {KURGIN_SCHEMA_NAME}.stones
        set {', '.join(set_parts)},
            payload = {payload_expr},
            updated_at = now()
        where stone_id in ({placeholders})
        returning stone_id
    """
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                updated_ids = [row[0] for row in cur.fetchall()]
            conn.commit()
        return {"ok": True, "updated": len(updated_ids), "updated_ids": updated_ids, "error": ""}
    except Exception as exc:
        return {"ok": False, "updated": 0, "error": str(exc)}


def build_public_export_from_db() -> dict[str, Any]:
    generated_at = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                select stone_id, status, availability_status, catalog_section,
                       report_number, stock_number, payload
                from {KURGIN_SCHEMA_NAME}.stones
                where status = 'published' and availability_status = 'in_stock'
                order by stone_id
                """
            )
            rows = cur.fetchall()

    export_rows = []
    skipped = 0
    for stone_id, status, availability, section, report_number, stock_number, payload in rows:
        payload = payload or {}
        price_display = _payload_text(payload, "public_price_display")
        price_status = _payload_text(payload, "price_status")
        allow_price_on_request = _payload_text(payload, "allow_price_on_request").lower() == "true"
        price_type = "numeric" if price_status == "calculated" and price_display else ""
        if not price_type and allow_price_on_request and price_display == "Цена по запросу":
            price_type = "price_on_request"
        if not price_type:
            skipped += 1
            continue

        row = {
            "shape": _payload_text(payload, "shape"),
            "kurgin_score": _payload_text(payload, "kurgin_score"),
        }
        public_card_status = "public_numeric_price" if price_type == "numeric" else "public_price_on_request"
        reason = "published / in_stock / public section / numeric price" if price_type == "numeric" else "published / in_stock / public section / price on request"
        depth_mm = _payload_text(payload, "depth_mm")
        export_rows.append({
            "schema_version": "public_stones_v1",
            "exported_at": generated_at,
            "stone_id": str(stone_id),
            "report_number": str(report_number or _payload_text(payload, "report_number")),
            "lab": _payload_text(payload, "lab"),
            "catalog_section": str(section or ""),
            "section_name": "Основной каталог" if section == "main" else "Крупные камни" if section == "large" else "",
            "public_card_status": public_card_status,
            "public_visibility_reason": reason,
            "shape": row["shape"],
            "weight": _payload_text(payload, "weight"),
            "carat_label": _carat_label(_payload_text(payload, "weight")),
            "color": _payload_text(payload, "color"),
            "clarity": _payload_text(payload, "clarity"),
            "kurgin_score": row["kurgin_score"],
            "kurgin_score_range_label": _score_range_label(row),
            "public_price_display": price_display,
            "price_display_type": price_type,
            "min_diameter": _payload_text(payload, "min_diameter"),
            "max_diameter": _payload_text(payload, "max_diameter"),
            "height": _payload_text(payload, "height") or depth_mm,
            "depth_mm": depth_mm,
            "cut_grade": _payload_text(payload, "cut"),
            "symmetry": _payload_text(payload, "symmetry"),
            "polish": _payload_text(payload, "polish"),
            "fluorescence": _normalize_fluorescence(_payload_text(payload, "fluorescence")),
            "tags": _payload_text(payload, "tags"),
            "availability_status_public": str(availability or ""),
            "detail_available": "false",
            "kurgin_report_available": "false",
            "lab_report_available": "false",
            "main_image_available": "false",
        })

    df = pd.DataFrame(export_rows)
    for col in PUBLIC_EXPORT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[PUBLIC_EXPORT_COLUMNS] if not df.empty else pd.DataFrame(columns=PUBLIC_EXPORT_COLUMNS)
    return {"export_df": df, "rows": int(len(df)), "skipped_without_public_price": skipped, "generated_at": generated_at}


def public_export_csv_bytes(df: pd.DataFrame) -> bytes:
    clean = df.copy() if df is not None else pd.DataFrame(columns=PUBLIC_EXPORT_COLUMNS)
    for col in PUBLIC_EXPORT_COLUMNS:
        if col not in clean.columns:
            clean[col] = ""
    clean = clean[PUBLIC_EXPORT_COLUMNS]
    return clean.to_csv(index=False).encode("utf-8-sig")


def record_public_export_metadata(rows_count: int, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        payload_text = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True)
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    insert into {KURGIN_SCHEMA_NAME}.public_exports (filename, rows_count, payload)
                    values (%s, %s, %s::jsonb)
                    returning export_id
                    """,
                    ("public_stones_v1.csv", int(rows_count), payload_text),
                )
                export_id = cur.fetchone()[0]
            conn.commit()
        return {"ok": True, "export_id": export_id, "error": ""}
    except Exception as exc:
        return {"ok": False, "export_id": "", "error": str(exc)}
