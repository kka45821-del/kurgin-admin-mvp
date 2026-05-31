import json
from pathlib import Path

SETTINGS_PATH = Path('data') / 'page_settings.json'


def load_public_price_mode() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    try:
        with SETTINGS_PATH.open('r', encoding='utf-8') as handle:
            value = json.load(handle)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def public_prices_request_only() -> bool:
    settings = load_public_price_mode()
    commerce = settings.get('commerce') if isinstance(settings, dict) else None
    if not isinstance(commerce, dict):
        return False
    return bool(commerce.get('public_prices_request_only', False))
