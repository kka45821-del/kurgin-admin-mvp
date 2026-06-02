import pandas as pd

from kurgin.formula import score_catalog, score_single


def test_score_single_in_range():
    result = score_single(
        {
            "stone_id": "T-001",
            "type": "Diamond",
            "carat": 1.0,
            "color": "D",
            "clarity": "VVS1",
            "cut": "Excellent",
            "polish": "Excellent",
            "symmetry": "Excellent",
            "fluorescence": "None",
            "certificate": "GIA",
            "price_usd": 10000,
            "availability": "Available",
        }
    )
    assert 0 <= result["kurgin_score"] <= 100
    assert result["rating"] in {"Risk", "Review", "Strong", "Premium"}


def test_score_catalog_adds_expected_columns():
    df = pd.DataFrame(
        [
            {
                "stone_id": "T-001",
                "type": "Diamond",
                "carat": 1.0,
                "color": "G",
                "clarity": "VS1",
                "cut": "Excellent",
                "certificate": "GIA",
                "price_usd": 9000,
                "availability": "Available",
            }
        ]
    )
    scored = score_catalog(df)
    for column in ["quality_score", "value_score", "risk_score", "kurgin_score", "rating"]:
        assert column in scored.columns
