import streamlit as st

from admin_upload import render_upload_tab


def render_product_upload():
    st.markdown("### Загрузка")
    st.caption("Excel содержит параметры камня, не финальную цену. Финальная цена задаётся отдельно после проверки.")
    render_upload_tab(allow_replace=False, show_next_to_pricing=True)
