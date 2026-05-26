import os

import pandas as pd
import streamlit as st

from admin_batches import render_batches_tab
from admin_io import load_batches, load_stones, public_preview, save_stones
from admin_menu import (
    ACTIVE,
    FUTURE,
    RESTRICTED,
    STUB,
    STATUS_LABELS,
    find_item,
    visible_items,
    visible_sections,
)
from admin_publish import render_publish_tab
from admin_upload import render_upload_tab
from admin_validation import validate_catalog

st.set_page_config(page_title="KURGIN Admin", page_icon="◇", layout="wide")

ADMIN_PASSWORD = os.getenv("KURGIN_ADMIN_PASSWORD", "admin123")

BADGE_STYLE = {
    ACTIVE: "#0f7b0f",
    STUB: "#8a6d00",
    FUTURE: "#666666",
    RESTRICTED: "#9b1c1c",
}


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def render_status_badge(status: str):
    color = BADGE_STYLE.get(status, "#555")
    st.markdown(
        f"<span style='display:inline-block;padding:4px 10px;border-radius:999px;background:{color};color:white;font-size:12px'>{status_label(status)}</span>",
        unsafe_allow_html=True,
    )


def render_info_box(section: dict, item: dict | None):
    st.caption("Административный каркас KURGIN. Рабочие зоны подключаются постепенно, без смешивания будущих функций с текущим MVP.")
    st.divider()
    left, right = st.columns([2, 1])
    with left:
        st.subheader(item.get("title") if item else section.get("title"))
        st.write(item.get("description") if item else section.get("description"))
    with right:
        render_status_badge(item.get("status") if item else section.get("status"))


def render_stub_page(section: dict, item: dict | None):
    render_info_box(section, item)
    st.info("Раздел создан как часть административного каркаса, но рабочая логика ещё не подключена.")
    st.markdown("### Что здесь будет")
    st.write("- управление данными и статусами раздела;")
    st.write("- проверки перед включением функции;")
    st.write("- журнал изменений и понятные предупреждения;")
    st.write("- связь с публичной платформой только после отдельной проверки.")
    st.warning("Пока этот раздел не должен восприниматься как рабочая функция.")


def render_future_page(section: dict, item: dict | None):
    render_info_box(section, item)
    st.info("Этот раздел не входит в ближайший MVP. Он сохранён в структуре, чтобы не потерять будущую архитектуру.")


def render_restricted_page(section: dict, item: dict | None):
    render_info_box(section, item)
    st.error("Раздел ограничен. Он связан с юридическими, платёжными, пользовательскими или операционными рисками.")
    st.write("Не включать как рабочую функцию без отдельной проверки.")
    st.write("Нельзя смешивать: оплату и sold, заявку и заказ, поставщика и публичного продавца, Analyzer и сертификат, Index и точную цену.")


def render_dashboard(item: dict | None):
    stones = load_stones()
    public = public_preview(stones)
    batches = load_batches()
    critical, warnings = validate_catalog(stones) if not stones.empty else (pd.DataFrame(), pd.DataFrame())

    st.subheader("Общий статус платформы")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Всего камней", len(stones))
    c2.metric("Публичных", len(public))
    c3.metric("Партий", len(batches))
    c4.metric("Предупреждений", len(warnings))

    st.divider()
    st.subheader("Ошибки и риски")
    if critical.empty:
        st.success("Критических ошибок каталога не найдено.")
    else:
        st.error("Есть критические ошибки каталога.")
        st.dataframe(critical, use_container_width=True)

    if not warnings.empty:
        st.warning("Есть предупреждения. Для MVP допустимо, если это цена по запросу или будущие поля.")
        st.dataframe(warnings, use_container_width=True)

    st.subheader("Быстрые действия")
    st.write("- Для загрузки Excel: Каталог → Импорт Excel")
    st.write("- Для публикации: Каталог → Publication Gate")
    st.write("- Для просмотра данных: Каталог → Все камни")


def render_catalog_active(item: dict | None):
    item_id = item.get("id") if item else "catalog_all"

    if item_id == "catalog_import":
        render_upload_tab()
        return
    if item_id == "catalog_publication":
        render_publish_tab()
        return
    if item_id == "catalog_all":
        st.subheader("Все камни")
        df = load_stones()
        st.caption("Рабочая таблица каталога. Аккуратно редактировать только понятные поля.")
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("Сохранить каталог", type="primary"):
            save_stones(edited)
            st.success("Каталог сохранён")
        return
    if item_id == "catalog_sections":
        st.subheader("Разделы каталога")
        df = load_stones()
        public = public_preview(df)
        if public.empty or "section" not in public.columns:
            st.info("Пока нет опубликованных камней или поле section отсутствует.")
            return
        section_counts = public["section"].fillna("не задано").value_counts().rename_axis("section").reset_index(name="count")
        st.dataframe(section_counts, use_container_width=True)
        st.write("Правило MVP: 1.00–2.99 ct → основной каталог, 3.00+ ct → крупные. Остальные разделы будут подключаться позже.")
        return
    if item_id == "catalog_statuses":
        st.subheader("Статусы камней")
        df = load_stones()
        if df.empty or "current_status" not in df.columns:
            st.info("Статусы пока не найдены.")
            return
        st.dataframe(df["current_status"].fillna("не задано").value_counts().rename_axis("status").reset_index(name="count"), use_container_width=True)
        return
    if item_id == "catalog_prices":
        st.subheader("Цены")
        df = load_stones()
        if df.empty or "price_rub" not in df.columns:
            st.info("Ценовые поля пока не найдены.")
            return
        price = pd.to_numeric(df["price_rub"], errors="coerce").fillna(0)
        c1, c2 = st.columns(2)
        c1.metric("С ценой", int((price > 0).sum()))
        c2.metric("По запросу / без цены", int((price <= 0).sum()))
        st.warning("Цена 0 допустима для MVP как 'по запросу', но такие камни не готовы для ценового индекса.")
        return

    render_stub_page({"title": "Каталог", "description": "Каталог"}, item)


def render_content_active(item: dict | None):
    render_info_box({"title": "Контент", "description": "Тексты публичных страниц"}, item)
    st.write("На этом этапе здесь фиксируется структура будущего управления текстами. Финальные публичные тексты лучше включать после отдельной проверки.")


def render_navigation_active(item: dict | None):
    render_info_box({"title": "Навигация", "description": "Страницы и нижняя панель"}, item)
    st.write("Текущая нижняя панель публичного сайта:")
    st.write("- KURGIN")
    st.write("- Инструменты")
    st.write("- Каталог")
    st.write("- Избранное")
    st.write("- Корзина")
    st.write("- Профиль")


def render_settings_active(item: dict | None):
    render_info_box({"title": "Настройки", "description": "Режимы и источники данных"}, item)
    st.write("Текущий MVP-режим: данные каталога публикуются через kurgin-data, публичный сайт читает catalog.json.")
    st.write("Feature flags пока представлены как каркас, без изменения production-логики.")


def render_active_page(section: dict, item: dict | None):
    render_info_box(section, item)
    section_id = section.get("id")
    if section_id == "dashboard":
        render_dashboard(item)
    elif section_id == "catalog":
        render_catalog_active(item)
    elif section_id == "content":
        render_content_active(item)
    elif section_id == "navigation":
        render_navigation_active(item)
    elif section_id == "settings":
        render_settings_active(item)
    elif section_id == "requests":
        render_stub_page(section, item)
    else:
        st.info("Активная страница создана, рабочая логика будет подключена отдельно.")


def render_page(section: dict, item: dict | None):
    status = item.get("status") if item else section.get("status")
    if status == ACTIVE:
        render_active_page(section, item)
    elif status == STUB:
        render_stub_page(section, item)
    elif status == FUTURE:
        render_future_page(section, item)
    elif status == RESTRICTED:
        render_restricted_page(section, item)
    else:
        st.info("Раздел скрыт или не настроен.")


if "admin_login" not in st.session_state:
    st.session_state.admin_login = False

st.title("KURGIN Admin")
st.caption("Русская административная зона MVP. Текущая рабочая админка app.py не изменена.")

if not st.session_state.admin_login:
    password = st.text_input("Пароль", type="password")
    if st.button("Войти", type="primary"):
        st.session_state.admin_login = password == ADMIN_PASSWORD
        st.rerun()
    st.stop()

with st.sidebar:
    st.header("KURGIN Admin")
    sections = visible_sections()
    section_labels = [f"{s['icon']} {s['title']}" for s in sections]
    selected_label = st.radio("Раздел", section_labels, index=0)
    selected_section = sections[section_labels.index(selected_label)]

    items = visible_items(selected_section)
    selected_item = None
    if items:
        item_labels = [f"{i['title']} · {STATUS_LABELS.get(i['status'], i['status'])}" for i in items]
        selected_item_label = st.selectbox("Подраздел", item_labels)
        selected_item = items[item_labels.index(selected_item_label)]

    st.divider()
    st.caption("Опасные и будущие функции показаны как структура, но не включены как рабочая логика.")

render_page(selected_section, selected_item)
