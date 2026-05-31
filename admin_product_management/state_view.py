import pandas as pd
import streamlit as st

from admin_io import load_batches, load_stones
from admin_publication_rules import public_visible_mask

from .actions import active_batch_mask
from .helpers import ensure_columns


def product_state_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    stones = load_stones()
    batches = load_batches()
    if stones.empty:
        return pd.DataFrame(), pd.DataFrame()

    work = stones.copy()
    if "batch_number" not in work.columns:
        work["batch_number"] = "не задано"
    work["batch_number"] = work["batch_number"].astype(str)
    visible_mask = public_visible_mask(work)

    grouped = work.groupby("batch_number", dropna=False).size().reset_index(name="количество камней всего")
    on_site = work[visible_mask].groupby("batch_number", dropna=False).size().reset_index(name="количество на сайте")
    result = grouped.merge(on_site, on="batch_number", how="left")
    result["количество на сайте"] = result["количество на сайте"].fillna(0).astype(int)

    if "current_status" in work.columns:
        sold = work[work["current_status"].astype(str).str.lower().eq("sold")].groupby("batch_number").size().reset_index(name="количество проданных")
        reserved = work[work["current_status"].astype(str).str.lower().eq("reserved")].groupby("batch_number").size().reset_index(name="количество забронированных")
        removed = work[work["current_status"].astype(str).str.lower().eq("removed_from_sale")].groupby("batch_number").size().reset_index(name="количество снятых")
        result = result.merge(sold, on="batch_number", how="left").merge(reserved, on="batch_number", how="left").merge(removed, on="batch_number", how="left")
    else:
        result["количество проданных"] = 0
        result["количество забронированных"] = 0
        result["количество снятых"] = 0

    for col in ["количество проданных", "количество забронированных", "количество снятых"]:
        if col not in result.columns:
            result[col] = 0
        result[col] = result[col].fillna(0).astype(int)

    result["количество в избранных"] = 0
    result["количество в корзине"] = 0

    if not batches.empty:
        meta = batches.copy()
        meta["batch_number"] = meta["batch_number"].astype(str)
        meta = meta.rename(columns={"upload_date": "дата", "supplier_name": "имя поставщика", "notes": "комментарий", "batch_status": "статус партии"})
        merge_cols = [c for c in ["batch_number", "дата", "имя поставщика", "комментарий", "статус партии"] if c in meta.columns]
        result = result.merge(meta[merge_cols], on="batch_number", how="left")
    else:
        result["дата"] = ""
        result["имя поставщика"] = ""
        result["комментарий"] = ""
        result["статус партии"] = ""

    cols = [
        "дата",
        "имя поставщика",
        "комментарий",
        "статус партии",
        "количество камней всего",
        "количество на сайте",
        "количество проданных",
        "количество снятых",
        "количество в избранных",
        "количество забронированных",
        "количество в корзине",
        "batch_number",
    ]
    result = ensure_columns(result, cols)
    return result[cols], work


def render_product_state():
    st.markdown("### Состояние")
    st.caption("sold / reserve / cart / favorites пока future-safe placeholders и не являются активной коммерческой логикой.")

    batches = load_batches()
    active_batches_count = int(active_batch_mask(batches).sum()) if not batches.empty else 0
    st.metric("Активных партий", active_batches_count)
    if active_batches_count == 0:
        st.info("Активных партий нет.")

    result, _ = product_state_rows()
    if result.empty:
        st.info("Камней пока нет.")
        return

    header = st.columns([1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    labels = [
        "дата",
        "имя поставщика",
        "комментарий",
        "статус",
        "всего",
        "на сайте",
        "продано",
        "снято",
        "избранное",
        "бронь",
        "корзина",
        "",
    ]
    for col, label in zip(header, labels):
        col.markdown(f"**{label}**")

    for _, row in result.iterrows():
        cols = st.columns([1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        cols[0].write(row.get("дата", ""))
        cols[1].write(row.get("имя поставщика", ""))
        cols[2].write(row.get("комментарий", ""))
        cols[3].write(row.get("статус партии", ""))
        cols[4].write(row.get("количество камней всего", 0))
        cols[5].write(row.get("количество на сайте", 0))
        cols[6].write(row.get("количество проданных", 0))
        cols[7].write(row.get("количество снятых", 0))
        cols[8].write(row.get("количество в избранных", 0))
        cols[9].write(row.get("количество забронированных", 0))
        cols[10].write(row.get("количество в корзине", 0))
        batch_number = str(row.get("batch_number", ""))
        if cols[11].button("Подробнее", key=f"batch_detail_{batch_number}"):
            st.session_state["product_management_view"] = "batch_detail"
            st.session_state["product_detail_batch"] = batch_number
            st.session_state["product_batch_detail_return_menu"] = "Состояние"
            st.rerun()
