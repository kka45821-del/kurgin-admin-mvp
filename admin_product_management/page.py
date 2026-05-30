import streamlit as st

from .batches_view import render_product_batches
from .detail_view import render_product_batch_detail
from .navigation import PRODUCT_MENU
from .pricing_flow import render_product_pricing_placeholder
from .publish_flow import render_product_publish
from .sections import render_product_all_stones, render_product_edit_placeholder
from .state_view import render_product_state
from .upload_flow import render_product_upload


def render_product_management_page():
    left_title, right_title = st.columns([1, 4])
    with left_title:
        if st.button("← Назад", use_container_width=True):
            st.session_state["admin_return_dashboard"] = True
            st.session_state["product_management_view"] = "main"
            st.rerun()
    with right_title:
        st.subheader("Управление товаром")
        st.caption("Отдельная рабочая зона: камни, загрузка, цена, публикация, партии и состояние.")

    st.divider()

    next_menu = st.session_state.pop("product_management_next_menu", None)
    if next_menu in PRODUCT_MENU:
        st.session_state["product_management_menu"] = next_menu

    if st.session_state.get("product_management_view") == "batch_detail":
        render_product_batch_detail(st.session_state.get("product_detail_batch", ""))
        return

    menu_col, content_col = st.columns([1, 4])
    with menu_col:
        selected = st.radio("Меню", PRODUCT_MENU, key="product_management_menu", label_visibility="collapsed")
    with content_col:
        if selected == "Загрузка":
            render_product_upload()
        elif selected == "Установить цену":
            render_product_pricing_placeholder()
        elif selected == "Опубликовать":
            render_product_publish()
        elif selected == "Загруженные партии":
            render_product_batches()
        elif selected == "Редактирование":
            render_product_edit_placeholder()
        elif selected == "Состояние":
            render_product_state()
        elif selected == "Все камни":
            render_product_all_stones()
