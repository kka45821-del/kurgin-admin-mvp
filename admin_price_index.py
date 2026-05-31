from pathlib import Path

import pandas as pd
import streamlit as st

from admin_log import write_admin_action

DATA = Path("data")
DATA.mkdir(exist_ok=True)
PRICE_INDEX_FILE = DATA / "price_index.csv"

PRICE_INDEX_COLUMNS = [
    "section",
    "shape",
    "carat_min",
    "carat_max",
    "color_group",
    "clarity_group",
    "base_price_usd_per_ct",
    "usd_rub_rate",
    "market_adjustment_percent",
    "kurgin_score_min",
    "is_active",
    "note",
]

DEFAULT_PRICE_INDEX_ROWS = [
    {
        "section": "main",
        "shape": "Round",
        "carat_min": 1.00,
        "carat_max": 1.49,
        "color_group": "D-F",
        "clarity_group": "VS-SI",
        "base_price_usd_per_ct": 0,
        "usd_rub_rate": 0,
        "market_adjustment_percent": 0,
        "kurgin_score_min": 0,
        "is_active": True,
        "note": "Основной каталог 1.00-1.49 ct",
    },
    {
        "section": "main",
        "shape": "Round",
        "carat_min": 1.50,
        "carat_max": 2.99,
        "color_group": "D-F",
        "clarity_group": "VS-SI",
        "base_price_usd_per_ct": 0,
        "usd_rub_rate": 0,
        "market_adjustment_percent": 0,
        "kurgin_score_min": 0,
        "is_active": True,
        "note": "Основной каталог 1.50-2.99 ct",
    },
    {
        "section": "large",
        "shape": "Round",
        "carat_min": 3.00,
        "carat_max": 4.99,
        "color_group": "D-F",
        "clarity_group": "VS-SI",
        "base_price_usd_per_ct": 0,
        "usd_rub_rate": 0,
        "market_adjustment_percent": 0,
        "kurgin_score_min": 0,
        "is_active": True,
        "note": "Крупные 3.00-4.99 ct",
    },
    {
        "section": "large",
        "shape": "Round",
        "carat_min": 5.00,
        "carat_max": 99.99,
        "color_group": "D-F",
        "clarity_group": "VS-SI",
        "base_price_usd_per_ct": 0,
        "usd_rub_rate": 0,
        "market_adjustment_percent": 0,
        "kurgin_score_min": 0,
        "is_active": True,
        "note": "Крупные 5.00+ ct",
    },
]

NUMBER_COLUMNS = [
    "carat_min",
    "carat_max",
    "base_price_usd_per_ct",
    "usd_rub_rate",
    "market_adjustment_percent",
    "kurgin_score_min",
]


def _default_price_index() -> pd.DataFrame:
    return pd.DataFrame(DEFAULT_PRICE_INDEX_ROWS, columns=PRICE_INDEX_COLUMNS)


def load_price_index() -> pd.DataFrame:
    if PRICE_INDEX_FILE.exists():
        df = pd.read_csv(PRICE_INDEX_FILE)
    else:
        df = _default_price_index()
    for col in PRICE_INDEX_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[PRICE_INDEX_COLUMNS].copy()
    for col in NUMBER_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["is_active"] = df["is_active"].astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y", "да"])
    return df


def save_price_index(df: pd.DataFrame) -> None:
    result = df.copy()
    for col in PRICE_INDEX_COLUMNS:
        if col not in result.columns:
            result[col] = ""
    result = result[PRICE_INDEX_COLUMNS].copy()
    for col in NUMBER_COLUMNS:
        result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0)
    result["is_active"] = result["is_active"].astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y", "да"])
    PRICE_INDEX_FILE.parent.mkdir(exist_ok=True)
    result.to_csv(PRICE_INDEX_FILE, index=False)


def validate_price_index(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if df.empty:
        rows.append({"type": "warning", "row": "all", "message": "Index table пустая."})
        return pd.DataFrame(rows)

    allowed_sections = {"main", "large"}
    for idx, row in df.iterrows():
        row_no = int(idx) + 1
        section = str(row.get("section", "") or "").strip().lower()
        if section not in allowed_sections:
            rows.append({"type": "error", "row": row_no, "message": "section должен быть main или large."})
        carat_min = float(row.get("carat_min", 0) or 0)
        carat_max = float(row.get("carat_max", 0) or 0)
        if carat_max <= carat_min:
            rows.append({"type": "error", "row": row_no, "message": "carat_max должен быть больше carat_min."})
        if float(row.get("base_price_usd_per_ct", 0) or 0) < 0:
            rows.append({"type": "error", "row": row_no, "message": "base_price_usd_per_ct не может быть отрицательным."})
        if float(row.get("usd_rub_rate", 0) or 0) < 0:
            rows.append({"type": "error", "row": row_no, "message": "usd_rub_rate не может быть отрицательным."})
    return pd.DataFrame(rows)


def render_price_index_table() -> None:
    st.markdown("### Index table")
    st.caption(
        "Ручная таблица базовых цен для Основного каталога и Крупных. "
        "Изменение индекса пока не меняет публичные цены автоматически: после этого нужен отдельный пересчёт и подтверждение цен."
    )

    index_df = load_price_index()
    edited = st.data_editor(
        index_df,
        num_rows="dynamic",
        use_container_width=True,
        key="price_index_editor",
        column_config={
            "section": st.column_config.SelectboxColumn("section", options=["main", "large"], required=True),
            "shape": st.column_config.TextColumn("shape"),
            "carat_min": st.column_config.NumberColumn("carat_min", min_value=0.0, step=0.01),
            "carat_max": st.column_config.NumberColumn("carat_max", min_value=0.0, step=0.01),
            "base_price_usd_per_ct": st.column_config.NumberColumn("base_price_usd_per_ct", min_value=0.0, step=10.0),
            "usd_rub_rate": st.column_config.NumberColumn("usd_rub_rate", min_value=0.0, step=0.1),
            "market_adjustment_percent": st.column_config.NumberColumn("market_adjustment_percent", step=1.0),
            "kurgin_score_min": st.column_config.NumberColumn("kurgin_score_min", min_value=0.0, max_value=100.0, step=1.0),
            "is_active": st.column_config.CheckboxColumn("is_active"),
        },
    )

    validation = validate_price_index(edited)
    if validation.empty:
        st.success("Index table валидна.")
    else:
        if (validation["type"] == "error").any():
            st.error("В Index table есть ошибки. Сохранение заблокировано.")
        else:
            st.warning("В Index table есть предупреждения.")
        st.dataframe(validation, use_container_width=True)

    save_disabled = not validation.empty and (validation["type"] == "error").any()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Сохранить Index table", type="primary", disabled=save_disabled):
            save_price_index(edited)
            write_admin_action(
                action="price_index_save",
                entity="data/price_index.csv",
                rows_count=len(edited),
                source="price_management",
                result="success",
                details="Manual price index table saved. Public prices are not recalculated automatically.",
            )
            st.success("Index table сохранена. Публичные цены не изменены автоматически.")
            st.rerun()
    with col2:
        if st.button("Сбросить к шаблону"):
            save_price_index(_default_price_index())
            write_admin_action(
                action="price_index_reset_default",
                entity="data/price_index.csv",
                rows_count=len(DEFAULT_PRICE_INDEX_ROWS),
                source="price_management",
                result="success",
                details="Manual price index table reset to default template.",
            )
            st.success("Index table сброшена к шаблону.")
            st.rerun()
