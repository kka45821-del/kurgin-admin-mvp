from __future__ import annotations

import streamlit as st
import pandas as pd

from modules.db_read import read_db_stones, db_stones_summary

STATUS_LABELS = {"draft": "Черновик", "ready": "Готов", "published": "Опубликован", "archived": "Архив"}
AVAIL_LABELS = {"in_stock": "В наличии", "reserved": "Забронирован", "sold": "Продан", "removed": "Снят с продажи"}
SECTION_LABELS = {"main": "Основной каталог", "large": "Крупные камни", "": "Вне текущей версии"}

st.set_page_config(page_title="KURGIN Admin — 7P Камни PostgreSQL", layout="wide")
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
    ]:
        if col in view.columns:
            view[col] = view[col].map(mapping).fillna(view[col])
    return view


st.title("7P.6 — Камни из PostgreSQL")
st.caption("Read-only проверка чтения из базы. Основная страница ‘Камни’ пока не переключена.")

st.subheader("Птичий взгляд")
st.markdown(
    """
Цель этого шага — убедиться, что PostgreSQL уже может быть источником чтения для KURGIN Admin.

Это ещё не финальное переключение. Сначала сверяем количество и таблицу: CSV и PostgreSQL должны показывать одинаковый набор камней.
"""
)

summary_result = db_stones_summary()
if not summary_result.get("ok"):
    st.error("Не удалось прочитать PostgreSQL summary.")
    st.code(summary_result.get("error", ""), language="text")
    st.stop()

summary = summary_result.get("summary", {})
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Камней в DB", summary.get("db_stones", 0))
c2.metric("Камней в CSV", summary.get("csv_stones", 0))
c3.metric("Delta DB-CSV", summary.get("delta", 0))
c4.metric("В наличии DB", summary.get("in_stock", 0))
c5.metric("Поставок DB", summary.get("shipments", 0))

if summary.get("delta", 0) == 0 and summary.get("db_stones", 0) > 0:
    st.success("DB и CSV совпадают по количеству камней. Можно проверять таблицу и готовить следующий шаг.")
elif summary.get("db_stones", 0) == 0:
    st.error("В PostgreSQL нет камней. Сначала выполни 7P Миграция.")
else:
    st.warning("Количество DB и CSV отличается. Перед переключением основной страницы нужно разобраться.")

limit = st.slider("Лимит строк для чтения", min_value=50, max_value=1000, value=500, step=50)
df = read_db_stones(limit=limit)

st.subheader("Фильтры read-only")
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

st.write(f"Показано строк: {len(view)} из прочитанных {len(df)}")
st.dataframe(labelize(view), use_container_width=True, hide_index=True, height=520)

st.subheader("Что дальше")
st.markdown(
    """
Если здесь DB и CSV совпадают, следующий разумный шаг — **7P.7: переключить основную страницу `Камни` на PostgreSQL read mode**.

Делать это нужно аккуратно: сначала только чтение из базы, без редактирования и без публикации. Затем отдельно переносить write-операции.
"""
)
