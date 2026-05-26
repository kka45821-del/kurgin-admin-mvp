import os

import pandas as pd
import streamlit as st

from admin_batches import render_batches_tab
from admin_io import load_batches, load_stones, public_preview, save_stones
from admin_menu import ACTIVE, FUTURE, RESTRICTED, STUB, STATUS_LABELS, visible_items, visible_sections
from admin_publish import render_publish_tab
from admin_upload import render_upload_tab
from admin_validation import validate_catalog

st.set_page_config(page_title="KURGIN Admin MVP", page_icon="◇", layout="wide")
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


def render_header(section: dict, item: dict | None):
    left, right = st.columns([3, 1])
    with left:
        st.subheader(item.get("title") if item else section.get("title"))
        st.caption(item.get("description") if item else section.get("description"))
    with right:
        render_status_badge(item.get("status") if item else section.get("status"))
    st.divider()


def render_stub_page(section: dict, item: dict | None):
    render_header(section, item)
    st.info("Раздел создан в структуре админки, но рабочая логика ещё не подключена.")
    st.markdown("### Что здесь будет")
    st.write("- управление данными и статусами раздела;")
    st.write("- проверки перед включением функции;")
    st.write("- журнал изменений и понятные предупреждения;")
    st.write("- связь с публичной платформой только после отдельной проверки.")


def render_future_page(section: dict, item: dict | None):
    render_header(section, item)
    st.info("Этот раздел не входит в ближайший MVP. Он сохранён в структуре, чтобы не потерять будущую архитектуру.")


def render_restricted_page(section: dict, item: dict | None):
    render_header(section, item)
    st.error("Раздел ограничен. Он связан с юридическими, платёжными, пользовательскими или операционными рисками.")
    st.write("Не включать как рабочую функцию без отдельной проверки.")
    st.write("Нельзя смешивать: оплату и sold, заявку и заказ, поставщика и публичного продавца, Analyzer и сертификат, Index и точную цену.")


def render_dashboard(item: dict | None):
    stones = load_stones()
    public = public_preview(stones)
    batches = load_batches()
    critical, warnings = validate_catalog(stones) if not stones.empty else (pd.DataFrame(), pd.DataFrame())

    st.markdown("### Общий статус")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Всего камней", len(stones))
    c2.metric("Публичных", len(public))
    c3.metric("Партий", len(batches))
    c4.metric("Предупреждений", len(warnings))

    st.markdown("### Ошибки и риски")
    if critical.empty:
        st.success("Критических ошибок каталога не найдено.")
    else:
        st.error("Есть критические ошибки каталога.")
        st.dataframe(critical, use_container_width=True)

    if not warnings.empty:
        st.warning("Есть предупреждения. Для MVP допустимо, если это цена по запросу или будущие поля.")
        st.dataframe(warnings, use_container_width=True)

    st.markdown("### Быстрые действия")
    st.write("- Каталог → Импорт Excel")
    st.write("- Каталог → Публичный preview")
    st.write("- Каталог → Publication Gate")


def render_catalog_page(item: dict | None):
    item_id = item.get("id") if item else "catalog_all"

    if item_id == "catalog_all":
        st.markdown("### Все камни")
        df = load_stones()
        st.caption("Рабочая таблица каталога. Массово редактируй только понятные поля.")
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("Сохранить каталог", type="primary"):
            save_stones(edited)
            st.success("Каталог сохранён")
        return

    if item_id == "catalog_import":
        render_upload_tab()
        return

    if item_id == "catalog_batches":
        render_batches_tab()
        return

    if item_id == "catalog_preview":
        st.markdown("### Публичный preview")
        preview = public_preview(load_stones())
        st.metric("Публичных камней", len(preview))
        st.dataframe(preview, use_container_width=True)
        return

    if item_id == "catalog_publication":
        render_publish_tab()
        return

    if item_id == "catalog_sections":
        st.markdown("### Разделы каталога")
        df = load_stones()
        public = public_preview(df)
        if public.empty:
            st.info("Пока нет публичных камней.")
            return
        if "section" in public.columns:
            data = public["section"].fillna("не задано").value_counts().rename_axis("section").reset_index(name="count")
            st.dataframe(data, use_container_width=True)
        st.write("Правило MVP: 1.00–2.99 ct → основной каталог, 3.00+ ct → крупные. Остальные разделы подключаются позже.")
        return

    if item_id == "catalog_statuses":
        st.markdown("### Статусы камней")
        df = load_stones()
        if df.empty or "current_status" not in df.columns:
            st.info("Статусы пока не найдены.")
            return
        st.dataframe(df["current_status"].fillna("не задано").value_counts().rename_axis("status").reset_index(name="count"), use_container_width=True)
        return

    if item_id == "catalog_prices":
        st.markdown("### Цены")
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


def render_active_page(section: dict, item: dict | None):
    render_header(section, item)
    section_id = section.get("id")
    if section_id == "dashboard":
        render_dashboard(item)
    elif section_id == "catalog":
        render_catalog_page(item)
    elif section_id == "content":
        st.write("Здесь будет управление текстами публичных страниц. Сейчас фиксируется структура, без риска сломать рабочий каталог.")
    elif section_id == "navigation":
        st.write("Текущая нижняя панель публичного сайта: KURGIN, Инструменты, Каталог, Избранное, Корзина, Профиль.")
    elif section_id == "settings":
        st.write("Текущий MVP-режим: данные каталога публикуются через kurgin-data, публичный сайт читает catalog.json.")
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


if "login" not in st.session_state:
    st.session_state.login = False

st.title("KURGIN Admin MVP")
st.caption("Одна рабочая админка: каталог, импорт Excel, партии, preview и публикация. Будущие зоны показаны как каркас, но не включены как рабочие функции.")

if not st.session_state.login:
    password = st.text_input("Пароль", type="password")
    if st.button("Войти", type="primary"):
        st.session_state.login = password == ADMIN_PASSWORD
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
        item_labels = [f"{i['title']} · {status_label(i['status'])}" for i in items]
        selected_item_label = st.selectbox("Подраздел", item_labels)
        selected_item = items[item_labels.index(selected_item_label)]

    st.divider()
    if st.button("Выйти"):
        st.session_state.login = False
        st.rerun()
    st.caption("Ограниченные и будущие функции не считаются рабочими.")

render_page(selected_section, selected_item)
