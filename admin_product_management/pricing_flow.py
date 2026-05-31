import pandas as pd
import streamlit as st

from admin_io import load_stones
from admin_publication_rules import number_series

from .helpers import bool_series, ensure_columns, rub


def render_product_pricing_placeholder():
    st.markdown("### Установить цену")
    st.caption("Отдельный экран после загрузки. Pricing engine в этой задаче не реализуется.")
    st.info("Excel содержит параметры камней, цена устанавливается отдельно на основе Index table в админке.")

    last_batch = st.session_state.get("product_management_last_batch")
    if not last_batch:
        st.info("Сначала загрузите и сохраните партию в разделе Загрузка.")
        return

    st.markdown("#### Последняя загруженная партия")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Номер партии", last_batch.get("batch_number", ""))
    c2.metric("Дата загрузки", last_batch.get("upload_date", ""))
    c3.metric("Поставщик", last_batch.get("supplier_name", ""))
    c4.metric("Камней всего", last_batch.get("stones_count", 0))
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Общая сумма покупки", rub(last_batch.get("purchase_total_rub", 0)))
    c6.metric("Аванс", rub(last_batch.get("purchase_advance_rub", 0)))
    c7.metric("Долг", rub(last_batch.get("purchase_debt_rub", 0)))
    c8.caption(f"Комментарий: {last_batch.get('notes', '') or 'not available'}")

    stones = load_stones()
    if stones.empty:
        st.info("Камни последней партии пока не найдены в Admin catalog.")
        return

    batch_number = str(last_batch.get("batch_number", ""))
    if "batch_number" in stones.columns:
        df = stones[stones["batch_number"].astype(str).eq(batch_number)].copy()
    else:
        df = pd.DataFrame()

    if df.empty:
        st.warning("Партия сохранена в session state, но строки этой партии не найдены в текущем Admin catalog.")
        return

    for col in ["site_price_rub", "client_mode_price_rub", "jeweler_price_rub"]:
        if col not in df.columns:
            df[col] = 0

    site_price = number_series(df["site_price_rub"])
    legacy_price = number_series(df["price_rub"]) if "price_rub" in df.columns else pd.Series(0, index=df.index)
    site_price = site_price.mask(site_price.le(0) & legacy_price.gt(0), legacy_price)
    client_price = number_series(df["client_mode_price_rub"])
    jeweler_price = number_series(df["jeweler_price_rub"])
    price_status = df["price_status"].astype(str).str.strip().str.lower() if "price_status" in df.columns else pd.Series("", index=df.index)
    price_confirmed = bool_series(df["price_confirmed"]) if "price_confirmed" in df.columns else pd.Series(False, index=df.index)
    availability_confirmed = bool_series(df["availability_confirmed"]) if "availability_confirmed" in df.columns else pd.Series(False, index=df.index)

    df["price_missing"] = site_price.le(0)
    df["needs_review"] = df["price_missing"] | price_status.isin(["", "missing", "needs_review", "index_pending", "index_suggested"])
    df["ready_for_publish"] = site_price.gt(0) & price_confirmed & availability_confirmed
    df["цена на сайте"] = site_price
    df["цена в режиме клиента"] = client_price
    df["цена для ювелира"] = jeweler_price

    view_cols = [
        "stone_id",
        "title",
        "shape",
        "carat",
        "color",
        "clarity",
        "lab",
        "report_number",
        "price_rub",
        "site_price_rub",
        "client_mode_price_rub",
        "jeweler_price_rub",
        "цена на сайте",
        "цена в режиме клиента",
        "цена для ювелира",
        "price_status",
        "price_missing",
        "needs_review",
        "ready_for_publish",
    ]
    df = ensure_columns(df, view_cols)
    st.dataframe(df[view_cols], use_container_width=True)

    if st.button("Далее", key="product_pricing_next_to_publish"):
        st.session_state["product_management_publish_ready_batch"] = batch_number
        st.session_state["product_management_next_menu"] = "Опубликовать"
        st.session_state["product_management_view"] = "main"
        st.rerun()
