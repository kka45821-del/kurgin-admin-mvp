import streamlit as st

from admin_io import load_stones
from admin_publication_rules import public_preview, publication_summary
from admin_publish import render_publish_tab


def render_product_publish():
    st.markdown("### Опубликовать")
    stones = load_stones()
    summary = publication_summary(stones)
    public = public_preview(stones)

    c1, c2, c3 = st.columns(3)
    c1.metric("К публикации", summary.get("visible", 0))
    c2.metric("Sellable", summary.get("sellable", 0))
    c3.metric("Blocked", summary.get("blocked", 0))

    if not public.empty and "section" in public.columns:
        st.markdown("#### Distribution by section")
        dist = public["section"].fillna("не задано").value_counts().rename_axis("section").reset_index(name="count")
        st.dataframe(dist, use_container_width=True)
    else:
        st.info("Нет публичных камней для распределения по section.")

    render_publish_tab()
    st.caption("Кнопка Далее переводит к списку партий. Она не утверждает, что публикация уже выполнена.")
    if st.button("Далее", key="product_publish_next_to_batches"):
        st.session_state["product_management_next_menu"] = "Загруженные партии"
        st.session_state["product_management_view"] = "main"
        st.rerun()
