from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
import hashlib, json

PUBLIC_INDEX_SCHEMA_VERSION = "public_index_v1"
FORBIDDEN_PUBLIC_INDEX_FIELDS = {"supplier_rate", "supplier_total", "kurgin_margin", "formula_internal", "index_row_id", "debug_trace"}

@dataclass(frozen=True)
class PublicIndexRow:
    color: str
    clarity: str
    carat_band_from: float
    carat_band_to: float
    score_range: str
    score_label: str
    public_index_rub_per_ct: int
    status: str = "active"
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def snapshot_hash(payload: dict[str, Any]) -> str:
    clean = {k: v for k, v in payload.items() if k != "hash"}
    return hashlib.sha256(json.dumps(clean, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def build_public_index_snapshot(rows: list[PublicIndexRow], *, active_index_version: str) -> dict[str, Any]:
    safe_rows = [r.to_dict() for r in rows]
    for row in safe_rows:
        found = FORBIDDEN_PUBLIC_INDEX_FIELDS.intersection(row.keys())
        if found:
            raise ValueError(f"Forbidden public index fields: {sorted(found)}")
    payload = {
        "source": "CVDLAB Admin",
        "schema": {"version": PUBLIC_INDEX_SCHEMA_VERSION},
        "currency": "RUB",
        "unit": "per_carat",
        "unit_label": "₽/ct",
        "active_index_version": active_index_version,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "rows": safe_rows,
        "disclaimer": {"ru": "KURGIN Index — публичный ориентир ₽/ct. Это не цена конкретного камня и не оферта."},
    }
    payload["hash"] = snapshot_hash(payload)
    return payload
