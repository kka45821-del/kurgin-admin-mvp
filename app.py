import pandas as pd
import streamlit as st

from admin_auth import logout_button, require_admin_login
from admin_batches import render_batches_tab
from admin_io import load_batches, load_stones
from admin_log import load_admin_actions
from admin_menu import ACTIVE, FUTURE, RESTRICTED, STUB, STATUS_LABELS, visible_items, visible_sections
from admin_page_settings import render_page_settings
from admin_pricing import render_pricing_tab
from admin_product_management import render_product_management_page
from admin_publication_rules import public_preview, publication_summary
from admin_publish import render_publish_tab
from admin_upload import render_upload_tab
from admin_validation import validate_catalog

st.set_page_config(page_title="KURGIN Admin MVP", page_icon="◇", layout="wide")

BADGE_STYLE = {ACTIVE: "#0f7b0f", STUB: "#8a6d00", FUTURE: "#666666", RESTRICTED: "#9b1c1c"}


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
    st.write("- данные и статусы раздела будут подключены отдельно;")
    st.write("- future/restricted зоны не считаются рабочими функциями;")
    st.write("- публичная платформа не меняется без отдельной проверки.")


def render_future_page(section: dict, item: dict | None):
    render_header(section, item)
    st.info("Раздел не входит в ближайший MVP. Он сохранён в структуре, чтобы не потерять будущую архитектуру.")


def render_restricted_page(section: dict, item: dict | None):
    render_header(section, item)
    st.error("Раздел ограничен: юридические, платёжные, пользовательские или операционные риски.")
    st.write("Не включать как рабочую функцию без отдельной проверки.")


def render_dashboard():
    stones = load_stones()
    public = public_preview(stones)
    summary = publication_summary(stones)
    batches = load_batches()
    actions = load_admin_actions()
    critical, warnings = validate_catalog(stones) if not stones.empty else (pd.DataFrame(), pd.DataFrame())

    st.markdown("### Общий статус")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Всего камней", len(stones))
    c2.metric("Visible", summary.get("visible", len(public)))
    c3.metric("Sellable", summary.get("sellable", 0))
    c4.metric("Партий", len(batches))
    c5.metric("Действий", len(actions))

    st.markdown("### Ошибки и риски")
    if critical.empty:
        st.success("Критических ошибок каталога не найдено.")
    else:
        st.error("Есть критические ошибки каталога.")
        st.dataframe(critical, use_container_width=True)
    if not warnings.empty:
        st.warning("Есть предупреждения. Для MVP допустимо, если это цена по запросу или future-поля.")
        st.dataframe(warnings, use_container_width=True)

    st.markdown("### Быстрые действия")
    st.write("Управление товаром → Загрузка → Установить цену → Опубликовать → Загруженные партии")


def render_catalog_page(item: dict | None):
    item_id = item.get("id") if item else "catalog_all"

    if item_id == "catalog_all":
        df = load_stones()
        st.warning(
            "Legacy / fallback view. Основной рабочий контур: Управление товаром. "
            "Ручное массовое сохранение через старый Каталог отключено."
        )
        st.caption("Read-only диагностика stones.csv. Для рабочих операций используйте Управление товаром.")
        st.dataframe(df, use_container_width=True)
        return

    if item_id == "catalog_import":
        render_upload_tab()
        return

    if item_id == "catalog_batches":
        render_batches_tab()
        return

    if item_id == "catalog_preview":
        preview = public_preview(load_stones())
        st.metric("Публичных камней", len(preview))
        st.dataframe(preview, use_container_width=True)
        return

    if item_id == "catalog_publication":
        render_publish_tab()
        return

    if item_id == "catalog_sections":
        public = public_preview(load_stones())
        if public.empty or "section" not in public.columns:
            st.info("Пока нет публичных камней или поля section.")
            return
        data = public["section"].fillna("не задано").value_counts().rename_axis("section").reset_index(name="count")
        st.dataframe(data, use_container_width=True)
        st.write("MVP: 1.00–2.99 ct → основной; 3.00+ ct → крупные. Остальные разделы позже.")
        return

    if item_id == "catalog_statuses":
        df = load_stones()
        if df.empty or "current_status" not in df.columns:
            st.info("Статусы пока не найдены.")
            return
        st.dataframe(df["current_status"].fillna("не задано").value_counts().rename_axis("status").reset_index(name="count"), use_container_width=True)
        return

    if item_id == "catalog_prices":
        render_pricing_tab()
        return

    render_stub_page({"title": "Каталог", "description": "Каталог"}, item)


def render_settings_page(item: dict | None):
    item_id = item.get("id") if item else "settings_mode"
    if item_id == "settings_page_settings":
        render_page_settings()
    elif item_id == "settings_logs":
        st.markdown("### Журнал действий администратора")
        st.dataframe(load_admin_actions().sort_values("created_at", ascending=False), use_container_width=True)
    else:
        st.write("Текущий MVP: каталог публикуется через kurgin-data, публичный сайт читает catalog.json. Feature flags пока являются каркасом.")


def render_active_page(section: dict, item: dict | None):
    section_id = section.get("id")
    if section_id == "product_management":
        render_product_management_page()
        return

    render_header(section, item)
    if section_id == "dashboard":
        render_dashboard()
    elif section_id == "catalog":
        render_catalog_page(item)
    elif section_id == "settings":
        render_settings_page(item)
    elif section_id == "navigation":
        st.write("Текущая нижняя панель публичного сайта: KURGIN, Инструменты, Каталог, Избранное, Корзина, Профиль.")
    elif section_id == "content":
        st.write("Здесь будет управление текстами публичных страниц. Сейчас это каркас без изменения публичного сайта.")
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


st.title("KURGIN Admin MVP")
st.caption("Одна закрытая админка: импорт Excel, каталог, preview, publication gate, настройки и audit log.")
require_admin_login("login")

if st.session_state.pop("admin_return_dashboard", False):
    st.session_state["admin_main_section_label"] = "◇ Обзор"

with st.sidebar:
    st.header("KURGIN Admin")
    sections = visible_sections()
    section_labels = [f"{s['icon']} {s['title']}" for s in sections]
    default_label = st.session_state.get("admin_main_section_label", section_labels[0])
    default_index = section_labels.index(default_label) if default_label in section_labels else 0
    selected_label = st.radio("Раздел", section_labels, index=default_index, key="admin_main_section_label")
    selected_section = sections[section_labels.index(selected_label)]

    items = visible_items(selected_section)
    selected_item = None
    if items and selected_section.get("id") != "product_management":
        item_labels = [f"{i['title']} · {status_label(i['status'])}" for i in items]
        selected_item_label = st.selectbox("Подраздел", item_labels)
        selected_item = items[item_labels.index(selected_item_label)]

    st.divider()
    logout_button("login")
    st.caption("Future/restricted разделы не являются рабочими функциями.")

render_page(selected_section, selected_item)
