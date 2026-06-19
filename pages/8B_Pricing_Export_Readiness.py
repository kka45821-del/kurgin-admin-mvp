from __future__ import annotations

import streamlit as st
import pandas as pd

from modules.db_pricing import build_pricing_audit, enable_price_on_request, publish_price_ready
from modules.db_core import build_public_export_from_db, public_export_csv_bytes, record_public_export_metadata

CONFIRM_PRICE_ON_REQUEST = "ВКЛЮЧИТЬ ЦЕНУ ПО ЗАПРОСУ"
CONFIRM_PUBLISH_READY = "ОПУБЛИКОВАТЬ ГОТОВЫЕ К ЭКСПОРТУ"
CONFIRM_EXPORT = "ПОДТВЕРЖДАЮ ЭКСПОРТ"

STATUS_LABELS = {"draft": "Черновик", "ready": "Готов", "published": "Опубликован", "archived": "Архив"}
AVAIL_LABELS = {"in_stock": "В наличии", "reserved": "Забронирован", "sold": "Продан", "removed": "Снят с продажи"}
SECTION_LABELS = {"main": "Основной каталог", "large": "Крупные камни", "": "Вне текущей версии"}
PRICE_GROUP_LABELS = {
    "numeric_ready": "Числовая цена готова",
    "price_on_request_ready": "Цена по запросу готова",
    "price_incomplete": "Цена неполная",
    "missing_price": "Нет публичной цены",
}

st.set_page_config(page_title="KURGIN Admin — 8B Pricing", layout="wide")
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
    for col, mapping in [
        ("status", STATUS_LABELS),
        ("availability_status", AVAIL_LABELS),
        ("catalog_section", SECTION_LABELS),
        ("price_group", PRICE_GROUP_LABELS),
    ]:
        if col in view.columns:
            view[col] = view[col].map(mapping).fillna(view[col])
    return view


st.title("8B — Pricing & Export Readiness")
st.caption("Крупный этап: ценовая готовность PostgreSQL, массовая ‘Цена по запросу’, публикация price-ready и export.")

st.subheader("Птичий взгляд")
st.markdown(
    """
Проблема уже не в базе и не в статусах: export был `0`, потому что у камней нет публичной цены. Этот этап делает каталог пригодным для витрины: либо числовая цена, либо явная **Цена по запросу**.
"""
)

audit = build_pricing_audit()
df = audit.get("df", pd.DataFrame())
summary = audit.get("summary", {})

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Всего", summary.get("total", 0))
m2.metric("Public-ready", summary.get("public_ready", 0))
m3.metric("Нет цены", summary.get("missing_price", 0))
m4.metric("Published", summary.get("published", 0))
m5.metric("Export rows", summary.get("export_rows", 0))

m6, m7, m8, m9 = st.columns(4)
m6.metric("Числовая цена", summary.get("numeric_ready", 0))
m7.metric("Цена по запросу", summary.get("price_on_request_ready", 0))
m8.metric("Цена неполная", summary.get("price_incomplete", 0))
m9.metric("Export-ready", summary.get("export_ready", 0))

if summary.get("export_rows", 0) == 0 and summary.get("missing_price", 0) > 0:
    st.warning("Export пустой, потому что камни не price-ready. Массовое включение ‘Цена по запросу’ решит это для выбранных камней.")
elif summary.get("export_rows", 0) > 0:
    st.success("Export уже содержит строки. Можно проверять CSV и подключение к витрине.")

st.subheader("Фильтры")
view = df.copy()
f1, f2, f3, f4 = st.columns(4)
with f1:
    price_options = ["Все"] + sorted([x for x in view["price_group"].dropna().astype(str).unique().tolist() if x])
    selected_price = st.selectbox("Ценовая группа", price_options)
with f2:
    status_options = ["Все"] + sorted([x for x in view["status"].dropna().astype(str).unique().tolist() if x])
    selected_status = st.selectbox("Статус", status_options)
with f3:
    avail_options = ["Все"] + sorted([x for x in view["availability_status"].dropna().astype(str).unique().tolist() if x])
    selected_avail = st.selectbox("Наличие", avail_options)
with f4:
    section_options = ["Все"] + sorted([x for x in view["catalog_section"].dropna().astype(str).unique().tolist() if x])
    selected_section = st.selectbox("Раздел", section_options)

search = st.text_input("Поиск по stone_id / report_number / stock_number").strip()
if selected_price != "Все":
    view = view[view["price_group"].astype(str) == selected_price]
if selected_status != "Все":
    view = view[view["status"].astype(str) == selected_status]
if selected_avail != "Все":
    view = view[view["availability_status"].astype(str) == selected_avail]
if selected_section != "Все":
    view = view[view["catalog_section"].astype(str) == selected_section]
if search:
    mask = pd.Series(False, index=view.index)
    for col in ["stone_id", "report_number", "stock_number"]:
        mask = mask | view[col].astype(str).str.contains(search, case=False, na=False)
    view = view[mask]

st.write(f"В фильтре: {len(view)}")
show_cols = [
    "stone_id", "report_number", "shape", "weight", "color", "clarity",
    "status", "availability_status", "catalog_section", "price_group",
    "public_price_display", "price_status", "allow_price_on_request", "export_ready",
]
st.dataframe(labelize(view[[c for c in show_cols if c in view.columns]]), use_container_width=True, hide_index=True, height=360)

stone_options = view["stone_id"].astype(str).tolist()
selected_ids = st.multiselect("Выбрать камни вручную", stone_options)
use_all_filtered = st.checkbox("Использовать все камни из текущего фильтра", value=False)
action_ids = stone_options if use_all_filtered else selected_ids
st.info(f"Выбрано для действия: {len(action_ids)}")

st.divider()
st.subheader("1. Массово включить ‘Цена по запросу’")
st.caption("Для камней без публичной цены будет записано: allow_price_on_request=true, public_price_display=Цена по запросу, price_status=missing_supplier_price.")
confirm_por = st.text_input(f"Для включения введите: {CONFIRM_PRICE_ON_REQUEST}")
if st.button("Включить ‘Цена по запросу’ для выбранных", type="primary"):
    if confirm_por != CONFIRM_PRICE_ON_REQUEST:
        st.error("Фраза подтверждения не совпадает.")
    else:
        result = enable_price_on_request(action_ids)
        if result.get("ok"):
            st.success(f"Обновлено камней: {result.get('updated', 0)}")
            st.rerun()
        else:
            st.error(result.get("error", "Ошибка записи."))

st.divider()
st.subheader("2. Опубликовать price-ready выбранные")
st.caption("Публикует только выбранные камни, у которых уже есть числовая цена или ‘Цена по запросу’.")
confirm_publish = st.text_input(f"Для публикации введите: {CONFIRM_PUBLISH_READY}")
if st.button("Опубликовать price-ready выбранные"):
    if confirm_publish != CONFIRM_PUBLISH_READY:
        st.error("Фраза подтверждения не совпадает.")
    else:
        result = publish_price_ready(action_ids)
        if result.get("ok"):
            st.success(f"Опубликовано/обновлено: {result.get('updated', 0)}")
            st.rerun()
        else:
            st.error(result.get("error", "Ошибка публикации."))

st.divider()
st.subheader("3. Export из PostgreSQL")
export_info = build_public_export_from_db()
export_df = export_info.get("export_df", pd.DataFrame())
e1, e2, e3 = st.columns(3)
e1.metric("Строк export", export_info.get("rows", 0))
e2.metric("Пропущено без публичной цены", export_info.get("skipped_without_public_price", 0))
e3.metric("Generated", export_info.get("generated_at", ""))
st.dataframe(export_df, use_container_width=True, hide_index=True, height=280)
st.download_button(
    "Скачать public_stones_v1.csv",
    data=public_export_csv_bytes(export_df),
    file_name="public_stones_v1.csv",
    mime="text/csv",
)
confirm_export = st.text_input(f"Для записи метаданных экспорта введите: {CONFIRM_EXPORT}")
if st.button("Записать метаданные экспорта"):
    if confirm_export != CONFIRM_EXPORT:
        st.error("Фраза подтверждения не совпадает.")
    else:
        result = record_public_export_metadata(
            rows_count=int(export_info.get("rows", 0)),
            payload={"generated_at": export_info.get("generated_at", ""), "stage": "8B", "skipped_without_public_price": export_info.get("skipped_without_public_price", 0)},
        )
        if result.get("ok"):
            st.success(f"Метаданные записаны. export_id: {result.get('export_id')}")
        else:
            st.error(result.get("error", "Ошибка записи метаданных."))

st.subheader("Что дальше")
st.markdown(
    """
Когда `Export rows` станет больше нуля, следующий крупный шаг — подключить PostgreSQL export к публичной витрине или сохранить CSV в стабильный публичный источник. После этого можно отдельно переносить числовое ценообразование.
"""
)
