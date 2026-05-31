from datetime import datetime, timezone
from typing import Any
import hashlib, json

PUBLIC_CATALOG_SCHEMA_VERSION = "public_catalog_v1"
FORBIDDEN_PUBLIC_FIELDS = {
    "supplier_rate", "supplier_total", "supplier_name", "notes_internal", "admin_price_note",
    "client_mode_price_rub", "jeweler_price_rub", "specialist_purchase_price_rub",
    "specialist_client_display_price_rub", "calculated_specialist_purchase_price_rub",
    "calculated_specialist_client_display_price_rub", "formula_internal", "index_row_id",
    "base_price_usd_per_carat", "raw_calculated_price_rub", "payment_secret",
}

def _i(v: Any) -> int:
    try: return int(float(str(v or 0).replace(' ', '').replace(',', '.')))
    except Exception: return 0

def build_public_stone(raw: dict[str, Any], *, request_only: bool = True) -> dict[str, Any]:
    price = _i(raw.get("calculated_public_price_rub") or raw.get("public_price_rub") or raw.get("site_price_rub"))
    return {
        "id": raw.get("stone_id") or raw.get("id"),
        "stone_id": raw.get("stone_id") or raw.get("id"),
        "title": raw.get("title") or "",
        "shape": raw.get("shape") or "",
        "carat": raw.get("carat") or 0,
        "color": raw.get("color") or "",
        "clarity": raw.get("clarity") or "",
        "lab": raw.get("lab") or "",
        "report_number": raw.get("report_number") or "",
        "kurgin_score": raw.get("kurgin_score") or raw.get("score") or 0,
        "section": raw.get("section") or "main",
        "public_visible": bool(raw.get("show_in_catalog", True)),
        "is_request_price": request_only or price <= 0,
        "public_price_rub": 0 if request_only else price,
        "priceText": "по запросу" if request_only or price <= 0 else f"{price:,}".replace(',', ' '),
        "public_action": "request_price" if request_only else "checkout",
        "checkout_enabled": False if request_only else bool(raw.get("checkout_enabled", False)),
        "currency": "RUB",
    }

def assert_no_forbidden_public_fields(stone: dict[str, Any]) -> None:
    found = FORBIDDEN_PUBLIC_FIELDS.intersection(stone.keys())
    if found:
        raise ValueError(f"Forbidden public fields: {sorted(found)}")

def snapshot_hash(payload: dict[str, Any]) -> str:
    clean = {k: v for k, v in payload.items() if k != "hash"}
    return hashlib.sha256(json.dumps(clean, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def build_public_catalog_snapshot(stones: list[dict[str, Any]], *, request_only: bool = True) -> dict[str, Any]:
    public = [build_public_stone(s, request_only=request_only) for s in stones]
    for s in public:
        assert_no_forbidden_public_fields(s)
    payload = {"source": "CVDLAB Admin", "schema": {"version": PUBLIC_CATALOG_SCHEMA_VERSION}, "updated_at": datetime.now(timezone.utc).isoformat(), "count": len(public), "stones": public}
    payload["hash"] = snapshot_hash(payload)
    return payload
