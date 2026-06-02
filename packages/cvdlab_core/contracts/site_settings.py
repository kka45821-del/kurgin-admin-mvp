from datetime import datetime, timezone
import hashlib, json

SITE_SETTINGS_SCHEMA_VERSION = "site_settings_v1"
SUPPORTED_LOCALES = ["ru", "en", "zh-CN", "hy"]
DEFAULT_TEXTS = {
    "partner.batch.on_site": {"ru": "На сайте", "en": "On site", "zh-CN": "网站展示中", "hy": "Կայքում"},
    "partner.batch.sold": {"ru": "Продано", "en": "Sold", "zh-CN": "已售出", "hy": "Վաճառված"},
    "partner.batch.removed": {"ru": "Снятые с продажи", "en": "Removed from sale", "zh-CN": "已下架", "hy": "Հանված վաճառքից"},
}

def _hash(payload: dict) -> str:
    clean = {k: v for k, v in payload.items() if k != "hash"}
    return hashlib.sha256(json.dumps(clean, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def build_site_settings_snapshot(settings: dict | None = None) -> dict:
    settings = settings or {}
    payload = {
        "source": "CVDLAB Admin",
        "schema": {"version": SITE_SETTINGS_SCHEMA_VERSION},
        "default_locale": "ru",
        "locales": SUPPORTED_LOCALES,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "pages": settings.get("pages", {"catalog": {"visible_public": True}, "partner": {"visible_public": False}}),
        "texts": settings.get("texts", DEFAULT_TEXTS),
        "feature_flags": settings.get("feature_flags", {}),
    }
    payload["hash"] = _hash(payload)
    return payload
