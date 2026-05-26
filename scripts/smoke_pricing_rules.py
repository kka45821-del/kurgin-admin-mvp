from admin_pricing_rules import (
    calculate_price,
    ceil_to_1000_rub,
    score_coefficient,
    validate_round_main_large_score,
)


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
    print("OK: round score gate")

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
