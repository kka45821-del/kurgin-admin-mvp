from datetime import datetime

import pandas as pd
import streamlit as st

from admin_io import load_stones, save_stones
from admin_log import write_admin_action
from admin_publication_rules import number_series

from .helpers import bool_series, ensure_columns, rub


def _current_batch_frame(stones: pd.DataFrame, batch_number: str) -> pd.DataFrame:
    if stones.empty or "batch_number" not in stones.columns:
        return pd.DataFrame()
    return stones[stones["batch_number"].astype(str).eq(str(batch_number))].copy()


def _site_price_series(df: pd.DataFrame) -> pd.Series:
    site_price = number_series(df["site_price_rub"]) if "site_price_rub" in df.columns else pd.Series(0, index=df.index)
    legacy_price = number_series(df["price_rub"]) if "price_rub" in df.columns else pd.Series(0, index=df.index)
    return site_price.mask(site_price.le(0) & legacy_price.gt(0), legacy_price)


def _confirm_batch_prices(stones: pd.DataFrame, batch_number: str) -> int:
    mask = stones["batch_number"].astype(str).eq(str(batch_number)) if "batch_number" in stones.columns else pd.Series(False, index=stones.index)
    batch = stones[mask].copy()
    if batch.empty:
        return 0

    site_price = _site_price_series(batch)
    valid = site_price.gt(0)
    if not valid.any():
        return 0

    target_index = batch.index[valid]
    target_prices = site_price.loc[target_index]
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    for col in ["site_price_rub", "price_rub", "confirmed_public_price_rub"]:
        if col not in stones.columns:
            stones[col] = ""
    for col in ["price_confirmed", "availability_confirmed", "price_status", "price_source", "pricing_run_timestamp"]:
        if col not in stones.columns:
            stones[col] = ""

    stones.loc[target_index, "site_price_rub"] = target_prices
    stones.loc[target_index, "price_rub"] = target_prices
    stones.loc[target_index, "confirmed_public_price_rub"] = target_prices
    stones.loc[target_index, "price_confirmed"] = True
    stones.loc[target_index, "availability_confirmed"] = True
    stones.loc[target_index, "price_status"] = "confirmed"
    stones.loc[target_index, "price_source"] = stones.loc[target_index, "price_source"].replace("", "index")
    stones.loc[target_index, "pricing_run_timestamp"] = timestamp

    save_stones(stones)
    write_admin_action(
        action="confirm_batch_prices",
        entity=str(batch_number),
        rows_count=int(valid.sum()),
        source="product_management_pricing",
        result="success",
        details=f"Owner confirmed prices for batch {batch_number}; confirmed_at={timestamp}",
    )
    return int(valid.sum())


def render_product_pricing_placeholder():
    st.markdown("### Установить и подтвердить цену")
    st.caption("Цена берётся из Index table / текущих price fields, но становится официальной только после подтверждения владельцем.")
    st.info("Excel подтверждает физическое наличие и проверку камня. Финальная цена для сайта и будущей оплаты подтверждается отдельно здесь.")

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
    df = _current_batch_frame(stones, batch_number)

    if df.empty:
        st.warning("Партия сохранена в session state, но строки этой партии не найдены в текущем Admin catalog.")
        return

    for col in ["site_price_rub", "client_mode_price_rub", "jeweler_price_rub", "confirmed_public_price_rub"]:
        if col not in df.columns:
            df[col] = 0

    site_price = _site_price_series(df)
    client_price = number_series(df["client_mode_price_rub"])
    jeweler_price = number_series(df["jeweler_price_rub"])
    price_status = df["price_status"].astype(str).str.strip().str.lower() if "price_status" in df.columns else pd.Series("", index=df.index)
    price_confirmed = bool_series(df["price_confirmed"]) if "price_confirmed" in df.columns else pd.Series(False, index=df.index)
    availability_confirmed = bool_series(df["availability_confirmed"]) if "availability_confirmed" in df.columns else pd.Series(False, index=df.index)

    df["price_missing"] = site_price.le(0)
    df["needs_review"] = df["price_missing"] | price_status.isin(["", "missing", "needs_review", "index_pending", "index_suggested"])
    df["ready_for_publish"] = site_price.gt(0) & price_confirmed & availability_confirmed & price_status.isin(["confirmed", "final", "manual_confirmed", "approved", "index_confirmed"])
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
        "confirmed_public_price_rub",
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

    missing_count = int(df["price_missing"].sum())
    needs_review_count = int(df["needs_review"].sum())
    ready_count = int(df["ready_for_publish"].sum())
    c9, c10, c11 = st.columns(3)
    c9.metric("Без цены", missing_count)
    c10.metric("Требуют подтверждения", needs_review_count)
    c11.metric("Уже готовы", ready_count)

    confirm_disabled = missing_count > 0
    if confirm_disabled:
        st.warning("Нельзя подтвердить цены партии, пока есть камни без цены на сайте.")

    confirm_owner = st.checkbox("Я владелец и подтверждаю новые цены этой партии", key="owner_confirm_batch_prices")
    if st.button("Подтвердить новые цены партии", type="primary", disabled=confirm_disabled or not confirm_owner):
        confirmed = _confirm_batch_prices(stones, batch_number)
        if confirmed:
            st.success(f"Подтверждено цен: {confirmed}")
            st.session_state["product_management_publish_ready_batch"] = batch_number
            st.session_state["product_management_next_menu"] = "Publication Gate"
            st.session_state["product_management_view"] = "main"
            st.rerun()
        else:
            st.error("Не удалось подтвердить цены: нет строк с положительной ценой.")

    if st.button("Далее без подтверждения", key="product_pricing_next_to_publish"):
        st.session_state["product_management_publish_ready_batch"] = batch_number
        st.session_state["product_management_next_menu"] = "Publication Gate"
        st.session_state["product_management_view"] = "main"
        st.rerun()
