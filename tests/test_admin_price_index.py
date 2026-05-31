import pandas as pd

from admin_price_index import PRICE_INDEX_COLUMNS, validate_price_index


def row(**overrides):
    value = {
        "section": "main",
        "shape": "Round",
        "carat_min": 1.0,
        "carat_max": 1.5,
        "color_group": "D-F",
        "clarity_group": "VS-SI",
        "base_price_usd_per_ct": 1000,
        "usd_rub_rate": 90,
        "market_adjustment_percent": 0,
        "kurgin_score_min": 0,
        "is_active": True,
        "note": "test",
    }
    value.update(overrides)
    return value


def frame(*rows):
    return pd.DataFrame(list(rows), columns=PRICE_INDEX_COLUMNS)


def test_valid_main_large_index_rows_pass():
    report = validate_price_index(frame(
        row(section="main", carat_min=1.0, carat_max=2.99),
        row(section="large", carat_min=3.0, carat_max=99.99),
    ))
    assert report.empty


def test_invalid_section_is_error():
    report = validate_price_index(frame(row(section="small")))
    assert not report.empty
    assert "section должен быть main или large" in report.iloc[0]["message"]


def test_invalid_carat_range_is_error():
    report = validate_price_index(frame(row(carat_min=2.0, carat_max=1.0)))
    assert not report.empty
    assert "carat_max" in report.iloc[0]["message"]


def test_negative_prices_are_errors():
    report = validate_price_index(frame(row(base_price_usd_per_ct=-1), row(usd_rub_rate=-1)))
    assert len(report) == 2
    assert set(report["type"]) == {"error"}
