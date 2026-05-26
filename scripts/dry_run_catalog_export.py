from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from admin_io import load_stones
from admin_publication_rules import public_preview
from admin_publish import _catalog_payload


REQUIRED_STONE_FIELDS = [
    "public_visible",
    "public_sellable",
    "checkout_enabled",
    "public_action",
    "price_rub",
    "price_confirmed",
    "availability_confirmed",
    "price_status",
    "confirmed_public_price_rub",
    "calculated_price_rub",
    "pricing_run_timestamp",
]


def run() -> None:
    stones_df = load_stones()
    public_df = public_preview(stones_df)
    payload_text = _catalog_payload(stones_df)
    payload = json.loads(payload_text)
    stones = payload.get("stones", [])

    if stones_df.empty or not stones:
        print("DRY_RUN_CATALOG_EXPORT_EMPTY_OK")
        return

    missing_by_stone = []
    for stone in stones:
        stone_id = stone.get("stone_id") or stone.get("id") or "<unknown>"
        missing = [field for field in REQUIRED_STONE_FIELDS if field not in stone]
        if missing:
            missing_by_stone.append({"stone_id": stone_id, "missing": missing})

    assert not missing_by_stone, missing_by_stone
    assert int(payload.get("count", 0)) == len(stones), payload.get("count")
    assert len(stones) == len(public_df), (len(stones), len(public_df))

    print(f"DRY_RUN_CATALOG_EXPORT_OK stones={len(stones)}")


if __name__ == "__main__":
    run()
