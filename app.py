import pandas as pd
import streamlit as st

from admin_auth import logout_button, require_admin_login
from admin_batches import render_batches_tab
from admin_io import load_batches, load_stones, save_stones
from admin_log import load_admin_actions, write_admin_action
from admin_menu import ACTIVE, FUTURE, RESTRICTED, STUB, STATUS_LABELS, visible_items, visible_sections
from admin_page_settings import render_page_settings
from admin_pricing import render_pricing_tab
from admin_publication_rules import number_series, public_preview, public_visible_mask, publication_summary
from admin_publish import render_publish_tab
from admin_upload import render_upload_tab
from admin_validation import validate_catalog

st.set_page_config(page_title="KURGIN Admin MVP", page_icon="◇", layout="wide")

BADGE_STYLE = {ACTIVE: "#0f7b0f", STUB: "#8a6d00", FUTURE: "#666666", RESTRICTED: "#9b1c1c"}
PRODUCT_MENU = [
    "Все камни на сайте",
    "Загрузка",
    "Установить цену",
    "Опубликовать",
    "Загруженные партии",
    "Состояние",
]


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


def bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y", "да"])


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
    st.write("Управление товаром → Загрузка → Опубликовать")


def product_public_table() -> pd.DataFrame:
    stones = load_stones()
    if stones.empty:
        return pd.DataFrame()
    public = public_preview(stones)
    if public.empty:
        return pd.DataFrame()

    result = public.copy()
    result["KURGIN Score"] = result.get("karo_score", "")
    if "public_action" in result.columns:
        result["public_status"] = result["public_action"].astype(str)
    elif "public_sellable" in result.columns:
        result["public_status"] = result["public_sellable"].map({True: "ready_for_checkout", False: "request_price"})
    else:
        result["public_status"] = "ready_for_publish"

    columns = [
        "stone_id",
        "title",
        "shape",
        "carat",
        "color",
        "clarity",
        "lab",
        "report_number",
        "KURGIN Score",
        "section",
        "price_status",
        "public_status",
    ]
    for col in columns:
        if col not in result.columns:
            result[col] = ""
    return result[columns]


def render_product_all_stones():
    st.markdown("### Все камни на сайте")
    st.caption("Камни, которые проходят текущий public preview / готовы к публикации по действующим правилам MVP.")
    table = product_public_table()
    if table.empty:
        st.info("Нет камней, проходящих текущий public preview.")
        return
    st.dataframe(table, use_container_width=True)


def render_product_upload():
    st.markdown("### Загрузка")
    st.caption("Excel содержит параметры камня, не финальную цену. Финальная цена задаётся отдельно после проверки.")
    render_upload_tab()


def render_product_pricing_placeholder():
    st.markdown("### Установить цену")
    st.caption("Отдельный экран после загрузки. Pricing engine в этой задаче не реализуется.")
    st.info("Цена будет рассчитываться/устанавливаться на основе Index table в админке. Excel не является источником финальной цены.")

    stones = load_stones()
    if stones.empty:
        st.info("Камней пока нет.")
        return

    df = stones.copy()
    price = number_series(df["price_rub"]) if "price_rub" in df.columns else pd.Series(0, index=df.index)
    price_status = df["price_status"].astype(str).str.strip().str.lower() if "price_status" in df.columns else pd.Series("", index=df.index)
    price_confirmed = bool_series(df["price_confirmed"]) if "price_confirmed" in df.columns else pd.Series(False, index=df.index)
    availability_confirmed = bool_series(df["availability_confirmed"]) if "availability_confirmed" in df.columns else pd.Series(False, index=df.index)

    df["price_missing"] = price.le(0)
    df["needs_review"] = df["price_missing"] | price_status.isin(["", "missing", "needs_review", "index_pending", "index_suggested"])
    df["ready_for_publish"] = price.gt(0) & price_confirmed & availability_confirmed

    view_cols = [
        "stone_id",
        "title",
        "shape",
        "carat",
        "color",
        "clarity",
        "lab",
        "report_number",
        "price_rub",
        "price_status",
        "price_missing",
        "needs_review",
        "ready_for_publish",
    ]
    for col in view_cols:
        if col not in df.columns:
            df[col] = ""
    st.dataframe(df[df["price_missing"] | df["needs_review"]][view_cols], use_container_width=True)


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


def render_product_batches():
    st.markdown("### Загруженные партии")
    batches = load_batches()
    stones = load_stones()
    if batches.empty:
        st.info("Партии пока не загружены.")
        return

    counts = pd.DataFrame(columns=["batch_number", "количество камней всего"])
    if not stones.empty and "batch_number" in stones.columns:
        counts = stones.groupby("batch_number", dropna=False).size().reset_index(name="количество камней всего")
        counts["batch_number"] = counts["batch_number"].astype(str)

    result = batches.copy()
    result["batch_number"] = result["batch_number"].astype(str)
    result = result.merge(counts, on="batch_number", how="left")
    result["количество камней всего"] = result["количество камней всего"].fillna(result.get("stones_count", 0)).astype(int)
    result["статус"] = result.get("upload_confirmed", "").astype(str).map(lambda value: "uploaded" if value.lower() in ["true", "1", "yes", "да"] else "draft")
    result = result.rename(columns={"upload_date": "дата", "supplier_name": "имя поставщика", "notes": "комментарий"})

    cols = ["дата", "имя поставщика", "комментарий", "количество камней всего", "batch_number", "статус"]
    for col in cols:
        if col not in result.columns:
            result[col] = ""
    st.dataframe(result[cols], use_container_width=True)


def render_product_state():
    st.markdown("### Состояние")
    st.caption("sold / reserve / cart / favorites пока future-safe placeholders и не являются активной коммерческой логикой.")

    stones = load_stones()
    batches = load_batches()
    if stones.empty:
        st.info("Камней пока нет.")
        return

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
        result = result.merge(sold, on="batch_number", how="left").merge(reserved, on="batch_number", how="left")
    else:
        result["количество проданных"] = 0
        result["количество забронированных"] = 0

    for col in ["количество проданных", "количество забронированных"]:
        if col not in result.columns:
            result[col] = 0
        result[col] = result[col].fillna(0).astype(int)

    result["количество в избранных"] = 0
    result["количество в корзине"] = 0

    if not batches.empty:
        meta = batches.copy()
        meta["batch_number"] = meta["batch_number"].astype(str)
        meta = meta.rename(columns={"upload_date": "дата", "supplier_name": "имя поставщика", "notes": "комментарий"})
        result = result.merge(meta[[c for c in ["batch_number", "дата", "имя поставщика", "комментарий"] if c in meta.columns]], on="batch_number", how="left")
    else:
        result["дата"] = ""
        result["имя поставщика"] = ""
        result["комментарий"] = ""

    cols = [
        "дата",
        "имя поставщика",
        "комментарий",
        "количество камней всего",
        "количество на сайте",
        "количество проданных",
        "количество в избранных",
        "количество забронированных",
        "количество в корзине",
        "batch_number",
    ]
    for col in cols:
        if col not in result.columns:
            result[col] = ""
    st.dataframe(result[cols], use_container_width=True)

    selected = st.selectbox("Подробнее по партии", result["batch_number"].astype(str).tolist())
    if st.button("Подробнее"):
        st.dataframe(work[work["batch_number"].astype(str).eq(selected)], use_container_width=True)


def render_product_management_page():
    left_title, right_title = st.columns([1, 4])
    with left_title:
        if st.button("← Назад", use_container_width=True):
            st.session_state["admin_main_section_label"] = "◇ Обзор"
            st.rerun()
    with right_title:
        st.subheader("Управление товаром")
        st.caption("Отдельная рабочая зона: камни, загрузка, цена, публикация, партии и состояние.")

    st.divider()
    menu_col, content_col = st.columns([1, 4])
    with menu_col:
        selected = st.radio("Меню", PRODUCT_MENU, key="product_management_menu", label_visibility="collapsed")
    with content_col:
        if selected == "Все камни на сайте":
            render_product_all_stones()
        elif selected == "Загрузка":
            render_product_upload()
        elif selected == "Установить цену":
            render_product_pricing_placeholder()
        elif selected == "Опубликовать":
            render_product_publish()
        elif selected == "Загруженные партии":
            render_product_batches()
        elif selected == "Состояние":
            render_product_state()


def render_catalog_page(item: dict | None):
    item_id = item.get("id") if item else "catalog_all"

    if item_id == "catalog_all":
        df = load_stones()
        st.caption("Рабочая таблица каталога. Массово редактируй только понятные поля.")
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("Сохранить каталог", type="primary"):
            save_stones(edited)
            write_admin_action("catalog_save", "stones.csv", len(edited), "app.catalog_all", details="Ручное сохранение таблицы каталога")
            st.success("Каталог сохранён")
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
