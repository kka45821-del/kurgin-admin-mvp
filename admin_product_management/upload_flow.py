import streamlit as st

from admin_upload import render_upload_tab


def render_product_upload():
    st.markdown("### Загрузка")
    st.caption("Этот контур принимает только товарные категории: Основной каталог и Крупные. Для остальных разделов будет отдельная загрузка.")
    render_upload_tab(
        allow_replace=False,
        show_next_to_pricing=True,
        allowed_sections={"main", "large"},
        section_context_label="Управление товаром: Основной каталог + Крупные",
    )
