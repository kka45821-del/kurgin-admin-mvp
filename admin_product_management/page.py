import streamlit as st

from .archive_view import render_product_archive
from .batches_view import render_product_batches
from .detail_view import render_product_batch_detail
from .navigation import PRODUCT_MENU
from .pricing_flow import render_product_pricing_placeholder
from .publish_flow import render_product_publish
from .sections import (
    render_product_all_stones,
    render_product_public_preview,
    render_product_showcase_sections,
)
from .state_view import render_product_state
from .upload_flow import render_product_upload


def render_product_edit_placeholder():
    st.markdown("### Редактирование")
    st.info("Здесь позже будет безопасное редактирование камней, партий и статусов.")
    st.write("- массовое опасное редактирование не включено;")
    st.write("- удаление, rollback и автоматическое изменение данных не добавлены;")
    st.write("- любые изменения данных требуют отдельного задания и проверки.")


def render_product_management_page():
    st.subheader("Управление товаром")
    st.caption(
        "Главная рабочая зона админки: камни, загрузка по фиксированному Excel-шаблону, "
        "партии, статусы, формирование цены, публичный предпросмотр и публикация."
    )

    st.warning("Этот раздел не создаёт checkout, payment, reserve, order, Verify или PDF/report.")
    st.divider()

    next_menu = st.session_state.pop("product_management_next_menu", None)
    if next_menu == "Publication Gate":
        next_menu = "Публикация"
    if next_menu == "Публичный preview":
        next_menu = "Публичный предпросмотр"
    if next_menu in PRODUCT_MENU:
        st.session_state["product_management_menu"] = next_menu

    if st.session_state.get("product_management_view") == "batch_detail":
        render_product_batch_detail(st.session_state.get("product_detail_batch", ""))
        return

    menu_col, content_col = st.columns([1, 4])
    with menu_col:
        selected = st.radio("Меню", PRODUCT_MENU, key="product_management_menu", label_visibility="collapsed")
    with content_col:
        if selected in {"Загрузка", "Загрузка Excel"}:
            render_product_upload()
        elif selected in {"Установить цену", "Формирование цены"}:
            render_product_pricing_placeholder()
        elif selected in {"Публикация", "Publication Gate"}:
            render_product_publish()
        elif selected in {"Загруженные партии", "Партии"}:
            render_product_batches()
        elif selected == "Архив":
            render_product_archive()
        elif selected == "Редактирование":
            render_product_edit_placeholder()
        elif selected in {"Состояние", "Статусы"}:
            render_product_state()
        elif selected == "Все камни":
            render_product_all_stones()
        elif selected in {"Публичный предпросмотр", "Публичный preview"}:
            render_product_public_preview()
        elif selected == "Разделы витрины":
            render_product_showcase_sections()
