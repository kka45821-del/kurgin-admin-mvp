import streamlit as st

from admin_io import load_stones
from admin_publication_rules import public_preview, publication_summary
from admin_publish import render_publish_tab

from .helpers import rub


def render_product_publish():
    st.markdown("### Опубликовать")

    last_batch = st.session_state.get("product_management_last_batch")
    ready_batch = st.session_state.get("product_management_publish_ready_batch")

    if not last_batch or not ready_batch or str(last_batch.get("batch_number", "")) != str(ready_batch):
        st.info("Сначала загрузите партию, затем проверьте её в разделе Установить цену и нажмите Далее.")
        st.caption("Publication Gate появится здесь только после прохождения шага Установить цену. Старый Catalog fallback остаётся доступен отдельно.")
        return

    st.markdown("#### Текущая партия")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Номер партии", last_batch.get("batch_number", ""))
    c2.metric("Дата загрузки", last_batch.get("upload_date", ""))
    c3.metric("Поставщик", last_batch.get("supplier_name", ""))
    c4.metric("Камней всего", last_batch.get("stones_count", 0))
    c5, c6, c7 = st.columns(3)
    c5.metric("Общая сумма покупки", rub(last_batch.get("purchase_total_rub", 0)))
    c6.metric("Аванс", rub(last_batch.get("purchase_advance_rub", 0)))
    c7.metric("Долг", rub(last_batch.get("purchase_debt_rub", 0)))

    stones = load_stones()
    if "batch_number" in stones.columns:
        batch_stones = stones[stones["batch_number"].astype(str).eq(str(ready_batch))].copy()
    else:
        batch_stones = stones.iloc[0:0].copy()

    if batch_stones.empty:
        st.warning("Текущая партия отмечена как готовая к публикации, но строки партии не найдены в Admin catalog.")
        return

    public = public_preview(batch_stones)
    summary = publication_summary(batch_stones)

    c1, c2, c3 = st.columns(3)
    c1.metric("К публикации", summary.get("visible", len(public)))
    c2.metric("Sellable", summary.get("sellable", 0))
    c3.metric("Blocked", summary.get("blocked", 0))

    if not public.empty and "section" in public.columns:
        st.markdown("#### Distribution by section")
        dist = public["section"].fillna("не задано").value_counts().rename_axis("section").reset_index(name="count")
        st.dataframe(dist, use_container_width=True)
    else:
        st.info("Нет публичных камней для распределения по section.")

    st.divider()
    st.warning("Внимание: кнопка публикации ниже публикует ВЕСЬ текущий публичный каталог из Admin data, а не только текущую партию.")
    render_publish_tab()
    st.caption("Кнопка Далее переводит к списку партий. Она не утверждает, что публикация уже выполнена.")
    if st.button("Далее", key="product_publish_next_to_batches"):
        st.session_state["product_management_next_menu"] = "Загруженные партии"
        st.session_state["product_management_view"] = "main"
        st.rerun()
