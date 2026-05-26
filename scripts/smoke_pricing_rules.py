from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from admin_pricing_rules import (
    calculate_price,
    ceil_to_1000_rub,
    score_coefficient,
    validate_round_main_large_score,
)
from admin_upload import score_gate_errors

try:
    import pandas as pd
except ImportError as exc:
    raise SystemExit("pandas is required to run this smoke check") from exc


PRICE_TABLE = [
    {
        "section": "main",
        "carat_band_from": 1.0,
        "carat_band_to": 1.5,
        "color": "F",
        "clarity": "VS1",
        "base_price_usd_per_carat": 100,
        "is_active": True,
    },
    {
        "section": "main",
        "carat_band_from": 1.0,
        "carat_band_to": 1.5,
        "color": "F",
        "clarity": "VS2",
        "base_price_usd_per_carat": None,
        "is_active": True,
    },
]


def assert_score_gate_error_count(rows, expected_count: int, expected_section: str | None = None) -> None:
    errors = score_gate_errors(pd.DataFrame(rows))
    assert len(errors) == expected_count, errors.to_dict("records")
    if expected_section is not None:
        assert str(errors.iloc[0]["section"]) == expected_section, errors.to_dict("records")


def run() -> None:
    assert score_coefficient(98.5) == 1.7
    print("OK: score_coefficient")

    assert ceil_to_1000_rub(123100) == 124000
    print("OK: ceil_to_1000_rub")

    blocked = validate_round_main_large_score(
        {
            "shape": "Round",
            "section": "main",
            "carat": 1.2,
            "color": "F",
            "clarity": "VS1",
        }
    )
    assert blocked["blocked"] is True
    assert blocked["status"] == "score_required"
    print("OK: round main score gate")

    blocked_large = validate_round_main_large_score(
        {
            "shape": "Round",
            "section": "large",
            "carat": 3.2,
            "color": "F",
            "clarity": "VS1",
        }
    )
    assert blocked_large["blocked"] is True
    assert blocked_large["status"] == "score_required"
    print("OK: round large score gate")

    assert_score_gate_error_count(
        [
            {
                "shape": "Round",
                "section": "",
                "carat": 1.2,
                "color": "F",
                "clarity": "VS1",
                "karo_score": "",
            }
        ],
        expected_count=1,
        expected_section="main",
    )
    print("OK: empty section 1.2 ct inferred as main")

    assert_score_gate_error_count(
        [
            {
                "shape": "Round",
                "section": "",
                "carat": 3.2,
                "color": "F",
                "clarity": "VS1",
                "karo_score": "",
            }
        ],
        expected_count=1,
        expected_section="large",
    )
    print("OK: empty section 3.2 ct inferred as large")

    assert_score_gate_error_count(
        [
            {
                "shape": "Oval",
                "section": "main",
                "carat": 1.2,
                "color": "F",
                "clarity": "VS1",
                "karo_score": "",
            }
        ],
        expected_count=0,
    )
    print("OK: oval main not blocked by score gate")

    non_round = calculate_price(
        {
            "shape": "Oval",
            "section": "main",
            "carat": 1.2,
            "color": "F",
            "clarity": "VS1",
        },
        PRICE_TABLE,
        manual_usd_rub_rate=100,
    )
    assert non_round["status"] == "calculated"
    assert non_round["score_coefficient"] == 1.0
    print("OK: non-round coefficient")

    empty_price = calculate_price(
        {
            "shape": "Oval",
            "section": "main",
            "carat": 1.2,
            "color": "F",
            "clarity": "VS2",
        },
        PRICE_TABLE,
        manual_usd_rub_rate=100,
    )
    assert empty_price["status"] == "request_price"
    print("OK: empty base price cell")

    print("SMOKE_PRICING_RULES_OK")


if __name__ == "__main__":
    run()
