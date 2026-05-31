import pandas as pd

from admin_section_policy import infer_product_section, product_section_violations


def test_explicit_main_and_large_are_allowed():
    df = pd.DataFrame([
        {"stone_id": "M1", "section": "main", "carat": 1.5},
        {"stone_id": "L1", "section": "large", "carat": 3.1},
        {"stone_id": "RU1", "section": "Основной каталог", "carat": 1.2},
        {"stone_id": "RU2", "section": "Крупные", "carat": 4.0},
    ])
    violations = product_section_violations(df)
    assert violations.empty


def test_other_sections_are_blocked():
    df = pd.DataFrame([
        {"stone_id": "S1", "section": "small", "carat": 0.2},
        {"stone_id": "C1", "section": "colored", "carat": 1.0},
        {"stone_id": "P1", "section": "pairs", "carat": 0.8},
        {"stone_id": "SIDE1", "section": "side", "carat": 0.4},
        {"stone_id": "EX1", "section": "exclusive", "carat": 2.0},
    ])
    violations = product_section_violations(df)
    assert len(violations) == 5
    assert set(violations["section"]) == {"small", "colored", "pairs", "side", "exclusive"}


def test_missing_section_is_inferred_by_carat_for_product_flow():
    assert infer_product_section(pd.Series({"section": "", "carat": 1.1})) == "main"
    assert infer_product_section(pd.Series({"section": "", "carat": 3.0})) == "large"
    assert infer_product_section(pd.Series({"section": "", "carat": 0.7})) == "other"
