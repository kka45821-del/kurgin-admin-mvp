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


def test_score_coefficient_top_band():
    assert score_coefficient(98.5) == 1.7


def test_ceil_to_1000_rub():
    assert ceil_to_1000_rub(123100) == 124000
    assert ceil_to_1000_rub(124000) == 124000


def test_round_main_large_without_score_is_blocked():
    stone = {"shape": "Round", "section": "main", "carat": 1.2, "color": "F", "clarity": "VS1"}
    result = validate_round_main_large_score(stone)
    assert result["blocked"] is True
    assert result["status"] == "score_required"


def test_non_round_main_large_uses_coefficient_one():
    stone = {"shape": "Oval", "section": "main", "carat": 1.2, "color": "F", "clarity": "VS1"}
    result = calculate_price(stone, PRICE_TABLE, manual_usd_rub_rate=100)
    assert result["status"] == "calculated"
    assert result["score_coefficient"] == 1.0
    assert result["calculated_price_rub"] == 12000
    assert result["price_confirmed"] is False
    assert result["checkout_enabled"] is False


def test_empty_base_price_cell_returns_request_price():
    stone = {"shape": "Oval", "section": "main", "carat": 1.2, "color": "F", "clarity": "VS2"}
    result = calculate_price(stone, PRICE_TABLE, manual_usd_rub_rate=100)
    assert result["status"] == "request_price"
    assert result["public_action"] == "request_price"
    assert result["checkout_enabled"] is False
