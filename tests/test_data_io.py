import pandas as pd

from kurgin.data_io import normalize_columns


def test_normalize_columns_aliases():
    df = pd.DataFrame({"SKU": ["A"], "Price": [100], "CT": [1.2], "Cert": ["GIA"]})
    normalized = normalize_columns(df)
    assert {"stone_id", "price_usd", "carat", "certificate"}.issubset(set(normalized.columns))
