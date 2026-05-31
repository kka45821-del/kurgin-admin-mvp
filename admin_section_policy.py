import pandas as pd

PRODUCT_SECTIONS = {"main", "large"}
OTHER_SECTIONS = {"small", "medium", "colored", "side", "pairs", "exclusive"}
SECTION_ALIASES = {
    "main": "main",
    "основной": "main",
    "основной каталог": "main",
    "large": "large",
    "крупные": "large",
    "medium": "medium",
    "средние": "medium",
    "small": "small",
    "мелкие": "small",
    "colored": "colored",
    "цветные": "colored",
    "side": "side",
    "боковые": "side",
    "pairs": "pairs",
    "парные": "pairs",
    "exclusive": "exclusive",
    "эксклюзив": "exclusive",
}


def normalize_section(value) -> str:
    text = str(value or "").strip().lower()
    return SECTION_ALIASES.get(text, text)


def infer_product_section(row: pd.Series) -> str:
    explicit = normalize_section(row.get("section"))
    if explicit:
        return explicit
    carat = pd.to_numeric(pd.Series([row.get("carat")]), errors="coerce").fillna(0).iloc[0]
    try:
        carat_value = float(carat)
    except (TypeError, ValueError):
        return ""
    if 1.0 <= carat_value < 3.0:
        return "main"
    if carat_value >= 3.0:
        return "large"
    return "other"


def product_section_violations(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["row", "stone_id", "section", "message"])
    rows = []
    for idx, row in df.iterrows():
        section = infer_product_section(row)
        if section in PRODUCT_SECTIONS:
            continue
        rows.append({
            "row": int(idx) + 2,
            "stone_id": str(row.get("stone_id", "") or ""),
            "section": section or "not_defined",
            "message": "Управление товаром принимает только Основной каталог и Крупные. Для остальных разделов будет отдельная загрузка.",
        })
    return pd.DataFrame(rows)
