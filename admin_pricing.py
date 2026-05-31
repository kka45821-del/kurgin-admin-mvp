from __future__ import annotations

import pandas as pd
import streamlit as st

from admin_io import load_stones
from admin_price_table import render_admin_price_table
from admin_pricing_candidates import render_priced_batch_candidates
from admin_pricing_settings import render_pricing_formula_settings
from admin_pricing_shared import read_price_table
from admin_pricing_template import render_price_table_template_download
from admin_pricing_v02_lite_preview import render_v02_lite_preview


def render_pricing_tab() -> None:
    st.markdown("### Pricing Engine Preview")
    st.caption(
        "Безопасный preview: расчёт сам по себе не сохраняет цены, не подтверждает price_confirmed, "
        "не публикует catalog.json и не включает checkout."
    )

    stones = load_stones()
    price = pd.to_numeric(stones.get("price_rub", pd.Series(dtype=float)), errors="coerce").fillna(0) if not stones.empty else pd.Series(dtype=float)
    confirmed = (
        stones.get("price_confirmed", pd.Series(dtype=str)).astype(str).str.lower().isin(["true", "1", "yes", "да"])
        if not stones.empty
        else pd.Series(dtype=bool)
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Камней в stones.csv", len(stones))
    c2.metric("С текущей ценой", int((price > 0).sum()))
    c3.metric("Цена подтверждена", int(confirmed.sum()))

    render_priced_batch_candidates(stones)
    saved_price_table = render_admin_price_table()
    formula_settings = render_pricing_formula_settings()
    render_price_table_template_download()

    st.info("Если section пустой, Pricing Preview временно использует carat-rule: 1.00–2.99 ct = main, 3.00+ ct = large. В stones.csv это не сохраняется.")
    st.warning("Preview не сохраняет рассчитанные цены. Для публикации нужен отдельный шаг подтверждения.")
    st.info("Подтверждение цен сохраняет цены в stones.csv, но НЕ публикует catalog.json. Для сайта нужен отдельный Publication Gate.")
    st.warning("Legacy pricing confirmation удалён. Старый механизм массового подтверждения цен больше не доступен из этого файла.")

    uploaded_file = st.file_uploader("Price table Excel/CSV", type=["xlsx", "xls", "csv"])
    price_table_source = st.radio(
        "Price table source",
        ["Use saved admin price table", "Use uploaded price table"],
        horizontal=True,
    )

    if price_table_source == "Use uploaded price table":
        if uploaded_file is None:
            st.info("Загрузи price table или выбери saved admin price table.")
            return
        try:
            price_table = read_price_table(uploaded_file)
        except Exception as exc:
            st.error(f"Не удалось прочитать price table: {exc}")
            return
    else:
        price_table = saved_price_table

    st.markdown("#### Active price table preview")
    st.caption(f"Источник: {price_table_source}. Строк в price table: {len(price_table)}")
    st.dataframe(price_table.head(20), use_container_width=True)

    if stones.empty:
        st.info("stones.csv пустой. Сначала загрузи каталог камней.")
        return

    render_v02_lite_preview(stones, price_table, formula_settings=formula_settings)
