from __future__ import annotations

import streamlit as st
import pandas as pd

from modules.db_read import read_db_stones, db_stones_summary
from modules.db_core import (
    mass_update_stones,
    build_public_export_from_db,
    public_export_csv_bytes,
    record_public_export_metadata,
)

STATUS_LABELS = {"draft": "Черновик", "ready": "Готов", "published": "Опубликован", "archived": "Архив"}
STATUS_KEYS = {v: k for k, v in STATUS_LABELS.items()}
AVAIL_LABELS = {"in_stock": "В наличии", "reserved": "Забронирован", "sold": "Продан", "removed": "Снят с продажи"}
AVAIL_KEYS = {v: k for k, v in AVAIL_LABELS.items()}
SECTION_LABELS = {"main": "Основной каталог", "large": "Крупные камни"}
SECTION_KEYS = {v: k for k, v in SECTION_LABELS.items()}
CONFIRM_MASS = "ПОДТВЕРЖДАЮ МАССОВОЕ ИЗМЕНЕНИЕ"
CONFIRM_PUBLISH = "ПОДТВЕРЖДАЮ ПУБЛИКАЦИЮ"
CONFIRM_UNPUBLISH = "ПОДТВЕРЖДАЮ СНЯТИЕ"
CONFIRM_EXPORT = "ПОДТВЕРЖДАЮ ЭКСПОРТ"

st.set_page_config(page_title="KURGIN Admin — 8A PostgreSQL Core", layout="wide")
st.markdown(
    """
<style>
.block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 1500px;}
div[data-testid="stVerticalBlock"] {gap: 0.45rem;}
.stDataFrame {font-size: 12px;}
h1, h2, h3 {margin-bottom: 0.3rem;}
</style>
""",
    unsafe_allow_html=True,
)


def labelize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    view = df.copy()
    for col, mapping in [("status", STATUS_LABELS), ("availability_status", AVAIL_LABELS), ("catalog_section", SECTION_LABELS)]:
        if col in view.columns:
            view[col] = view[col].map(mapping).fillna(view[col])
    return view


st.title("8A — PostgreSQL Admin Core")
st.caption("Управление каталогом из PostgreSQL: массовые статусы, публикация/снятие, CSV export. Цены и удаление пока не трогаются.")

st.subheader("Птичий взгляд")
st.markdown(
    """
Это укрупнённый рабочий шаг после проверки PostgreSQL. Цель — не делать бесконечные микрошаги, а довести базовое управление каталогом до рабочего состояния: **выбрал камни → изменил статус → опубликовал → получил export**.
"""
)

summary_result = db_stones_summary()
if not summary_result.get("ok"):
    st.error("PostgreSQL недоступен или таблицы не готовы.")
    st.code(summary_result.get("error", ""), language="text")
    st.stop()
summary = summary_result.get("summary", {})

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Камней DB", summary.get("db_stones", 0))
m2.metric("Delta DB-CSV", summary.get("delta", 0))
m3.metric("В наличии", summary.get("in_stock", 0))
m4.metric("Опубликовано", summary.get("published", 0))
m5.metric("Поставок", summary.get("shipments", 0))

if summary.get("delta", 0) != 0:
    st.warning("DB и CSV отличаются по количеству. Продолжать можно, но база уже считается рабочим источником для этой страницы.")

limit = st.slider("Лимит строк", min_value=100, max_value=1000, value=1000, step=100)
df = read_db_stones(limit=limit)

st.subheader("Фильтры")
view = df.copy()
f1, f2, f3, f4 = st.columns(4)
with f1:
    status_options = ["Все"] + sorted([x for x in view["status"].dropna().astype(str).unique().tolist() if x])
    selected_status = st.selectbox("Статус", status_options)
with f2:
    avail_options = ["Все"] + sorted([x for x in view["availability_status"].dropna().astype(str).unique().tolist() if x])
    selected_avail = st.selectbox("Наличие", avail_options)
with f3:
    section_options = ["Все"] + sorted([x for x in view["catalog_section"].dropna().astype(str).unique().tolist() if x])
    selected_section = st.selectbox("Раздел", section_options)
with f4:
    shape_options = ["Все"] + sorted([x for x in view["shape"].dropna().astype(str).unique().tolist() if x])
    selected_shape = st.selectbox("Форма", shape_options)

search = st.text_input("Поиск по stone_id / report_number / stock_number").strip()
if selected_status != "Все":
    view = view[view["status"].astype(str) == selected_status]
if selected_avail != "Все":
    view = view[view["availability_status"].astype(str) == selected_avail]
if selected_section != "Все":
    view = view[view["catalog_section"].astype(str) == selected_section]
if selected_shape != "Все":
    view = view[view["shape"].astype(str) == selected_shape]
if search:
    mask = pd.Series(False, index=view.index)
    for col in ["stone_id", "report_number", "stock_number"]:
        mask = mask | view[col].astype(str).str.contains(search, case=False, na=False)
    view = view[mask]

st.write(f"В фильтре: {len(view)}")
st.dataframe(labelize(view), use_container_width=True, hide_index=True, height=360)

stone_options = view["stone_id"].astype(str).tolist()
selected_ids = st.multiselect("Выбрать камни вручную", stone_options)
use_all_filtered = st.checkbox("Использовать все камни из текущего фильтра", value=False)
action_ids = stone_options if use_all_filtered else selected_ids
st.info(f"Выбрано для действия: {len(action_ids)}")

st.divider()
st.subheader("1. Массовое изменение административных полей")
ca, cb, cc = st.columns(3)
with ca:
    change_status = st.checkbox("Изменить status")
    new_status_label = st.selectbox("Новый status", list(STATUS_KEYS.keys()))
with cb:
    change_avail = st.checkbox("Изменить наличие")
    new_avail_label = st.selectbox("Новое наличие", list(AVAIL_KEYS.keys()))
with cc:
    change_section = st.checkbox("Изменить раздел")
    new_section_label = st.selectbox("Новый раздел", list(SECTION_KEYS.keys()))

preview_changes = []
if change_status:
    preview_changes.append({"Поле": "status", "Новое значение": STATUS_KEYS[new_status_label]})
if change_avail:
    preview_changes.append({"Поле": "availability_status", "Новое значение": AVAIL_KEYS[new_avail_label]})
if change_section:
    preview_changes.append({"Поле": "catalog_section", "Новое значение": SECTION_KEYS[new_section_label]})

st.dataframe(pd.DataFrame(preview_changes), use_container_width=True, hide_index=True, height=140)
confirm_mass = st.text_input(f"Для массового изменения введите: {CONFIRM_MASS}")
if st.button("Сохранить массовое изменение", type="primary"):
    if confirm_mass != CONFIRM_MASS:
        st.error("Фраза подтверждения не совпадает.")
    elif not action_ids:
        st.error("Камни не выбраны.")
    elif not preview_changes:
        st.error("Не выбрано ни одно поле для изменения.")
    else:
        result = mass_update_stones(
            action_ids,
            status=STATUS_KEYS[new_status_label] if change_status else None,
            availability_status=AVAIL_KEYS[new_avail_label] if change_avail else None,
            catalog_section=SECTION_KEYS[new_section_label] if change_section else None,
        )
        if result.get("ok"):
            st.success(f"Обновлено камней: {result.get('updated', 0)}")
            st.rerun()
        else:
            st.error(result.get("error", "Ошибка записи."))

st.divider()
st.subheader("2. Публикация и снятие с публикации")
p1, p2 = st.columns(2)
with p1:
    st.write("**Опубликовать выбранные**")
    st.caption("Ставит status = published. Экспорт попадёт только при наличии цены/цены по запросу.")
    confirm_pub = st.text_input(f"Для публикации введите: {CONFIRM_PUBLISH}")
    if st.button("Опубликовать выбранные"):
        if confirm_pub != CONFIRM_PUBLISH:
            st.error("Фраза подтверждения не совпадает.")
        else:
            result = mass_update_stones(action_ids, status="published")
            if result.get("ok"):
                st.success(f"Опубликовано/обновлено: {result.get('updated', 0)}")
                st.rerun()
            else:
                st.error(result.get("error", "Ошибка публикации."))
with p2:
    st.write("**Снять с публикации выбранные**")
    st.caption("Ставит status = ready. Камни исчезают из PostgreSQL export.")
    confirm_unpub = st.text_input(f"Для снятия введите: {CONFIRM_UNPUBLISH}")
    if st.button("Снять выбранные"):
        if confirm_unpub != CONFIRM_UNPUBLISH:
            st.error("Фраза подтверждения не совпадает.")
        else:
            result = mass_update_stones(action_ids, status="ready")
            if result.get("ok"):
                st.success(f"Снято/обновлено: {result.get('updated', 0)}")
                st.rerun()
            else:
                st.error(result.get("error", "Ошибка снятия."))

st.divider()
st.subheader("3. Public export из PostgreSQL")
export_info = build_public_export_from_db()
export_df = export_info.get("export_df", pd.DataFrame())
e1, e2, e3 = st.columns(3)
e1.metric("Строк export", export_info.get("rows", 0))
e2.metric("Пропущено без публичной цены", export_info.get("skipped_without_public_price", 0))
e3.metric("Generated", export_info.get("generated_at", ""))
st.dataframe(export_df, use_container_width=True, hide_index=True, height=280)
st.download_button(
    "Скачать public_stones_v1.csv из PostgreSQL",
    data=public_export_csv_bytes(export_df),
    file_name="public_stones_v1.csv",
    mime="text/csv",
)
confirm_export = st.text_input(f"Для записи метаданных экспорта введите: {CONFIRM_EXPORT}")
if st.button("Записать метаданные экспорта в PostgreSQL"):
    if confirm_export != CONFIRM_EXPORT:
        st.error("Фраза подтверждения не совпадает.")
    else:
        result = record_public_export_metadata(
            rows_count=int(export_info.get("rows", 0)),
            payload={"generated_at": export_info.get("generated_at", ""), "skipped_without_public_price": export_info.get("skipped_without_public_price", 0)},
        )
        if result.get("ok"):
            st.success(f"Метаданные экспорта записаны. export_id: {result.get('export_id')}")
        else:
            st.error(result.get("error", "Ошибка записи метаданных."))

st.subheader("Что дальше")
st.markdown(
    """
Если массовые статусы и публикация работают, следующий этап — перенос ценового блока на PostgreSQL или подключение этого export к публичной витрине. Удаление и архив лучше оставить отдельным опасным этапом.
"""
)
