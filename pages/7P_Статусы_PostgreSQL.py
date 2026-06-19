from __future__ import annotations

import streamlit as st
import pandas as pd

from modules.db_admin import (
    STATUS_VALUES,
    AVAILABILITY_VALUES,
    SECTION_VALUES,
    get_db_stone,
    update_db_stone_admin_fields,
    search_db_stones_for_admin,
)

STATUS_LABELS = {"draft": "Черновик", "ready": "Готов", "published": "Опубликован", "archived": "Архив"}
STATUS_KEYS = {v: k for k, v in STATUS_LABELS.items()}
AVAIL_LABELS = {"in_stock": "В наличии", "reserved": "Забронирован", "sold": "Продан", "removed": "Снят с продажи"}
AVAIL_KEYS = {v: k for k, v in AVAIL_LABELS.items()}
SECTION_LABELS = {"main": "Основной каталог", "large": "Крупные камни"}
SECTION_KEYS = {v: k for k, v in SECTION_LABELS.items()}
CONFIRM_TEXT = "СОХРАНИТЬ СТАТУСЫ В POSTGRESQL"

st.set_page_config(page_title="KURGIN Admin — 7P Статусы PostgreSQL", layout="wide")
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


st.title("7P.8 — Статусы и наличие в PostgreSQL")
st.caption("Первый write-шаг PostgreSQL: меняет только status, availability_status и catalog_section одного камня.")

st.subheader("Птичий взгляд")
st.markdown(
    """
Это первый узкий write-переход. Мы не трогаем цены, публикацию, удаление и импорт. Только проверяем, что PostgreSQL может сохранять административные статусы и переживать перезапуск.
"""
)

stones = search_db_stones_for_admin(limit=1000)
if stones.empty:
    st.error("В PostgreSQL нет камней для редактирования статусов.")
    st.stop()

st.subheader("Выбор камня")
search = st.text_input("Поиск по stone_id / report_number / stock_number").strip()
view = stones.copy()
if search:
    mask = pd.Series(False, index=view.index)
    for col in ["stone_id", "report_number", "stock_number"]:
        mask = mask | view[col].astype(str).str.contains(search, case=False, na=False)
    view = view[mask]

st.dataframe(labelize(view.head(100)), use_container_width=True, hide_index=True, height=260)
options = view["stone_id"].astype(str).tolist()
if not options:
    st.warning("По фильтру камни не найдены.")
    st.stop()

selected_id = st.selectbox("stone_id", options)
stone = get_db_stone(selected_id)
if not stone:
    st.error("Камень не найден в PostgreSQL.")
    st.stop()

payload = stone.get("payload") or {}

st.subheader("Текущие данные")
c1, c2, c3, c4 = st.columns(4)
c1.metric("stone_id", stone.get("stone_id", ""))
c2.metric("Report #", stone.get("report_number", ""))
c3.metric("Status", STATUS_LABELS.get(stone.get("status", ""), stone.get("status", "")))
c4.metric("Наличие", AVAIL_LABELS.get(stone.get("availability_status", ""), stone.get("availability_status", "")))

pcols = ["shape", "weight", "color", "clarity", "kurgin_score", "fluorescence"]
st.dataframe(
    pd.DataFrame([{col: str(payload.get(col, "")) for col in pcols}]),
    use_container_width=True,
    hide_index=True,
    height=90,
)

st.subheader("Изменить административные поля")
a, b, c = st.columns(3)
with a:
    status_label_options = [STATUS_LABELS[x] for x in STATUS_VALUES]
    current_status_label = STATUS_LABELS.get(str(stone.get("status", "draft")), "Черновик")
    new_status_label = st.selectbox("Статус записи", status_label_options, index=status_label_options.index(current_status_label) if current_status_label in status_label_options else 0)
with b:
    avail_label_options = [AVAIL_LABELS[x] for x in AVAILABILITY_VALUES]
    current_avail_label = AVAIL_LABELS.get(str(stone.get("availability_status", "in_stock")), "В наличии")
    new_avail_label = st.selectbox("Наличие", avail_label_options, index=avail_label_options.index(current_avail_label) if current_avail_label in avail_label_options else 0)
with c:
    section_label_options = [SECTION_LABELS[x] for x in SECTION_VALUES]
    current_section_label = SECTION_LABELS.get(str(stone.get("catalog_section", "main")), "Основной каталог")
    new_section_label = st.selectbox("Раздел", section_label_options, index=section_label_options.index(current_section_label) if current_section_label in section_label_options else 0)

new_status = STATUS_KEYS[new_status_label]
new_availability = AVAIL_KEYS[new_avail_label]
new_section = SECTION_KEYS[new_section_label]

changes = {
    "status": [stone.get("status", ""), new_status],
    "availability_status": [stone.get("availability_status", ""), new_availability],
    "catalog_section": [stone.get("catalog_section", ""), new_section],
}
change_rows = [
    {"Поле": key, "Было": before, "Будет": after, "Изменится": "да" if str(before) != str(after) else "нет"}
    for key, (before, after) in changes.items()
]
st.write("Preview изменений")
st.dataframe(pd.DataFrame(change_rows), use_container_width=True, hide_index=True, height=160)

has_changes = any(str(before) != str(after) for before, after in changes.values())
if not has_changes:
    st.info("Изменений нет.")
else:
    st.warning("Сохранение изменит только PostgreSQL. CSV пока не обновляется и остаётся fallback до полного переноса write-операций.")
    confirm = st.text_input(f"Для сохранения введите: {CONFIRM_TEXT}")
    if st.button("Сохранить статусы в PostgreSQL", type="primary"):
        if confirm != CONFIRM_TEXT:
            st.error("Фраза подтверждения не совпадает.")
        else:
            result = update_db_stone_admin_fields(
                stone_id=selected_id,
                status=new_status,
                availability_status=new_availability,
                catalog_section=new_section,
            )
            if result.get("ok"):
                st.success("Статусы сохранены в PostgreSQL.")
                st.rerun()
            else:
                st.error("Не удалось сохранить.")
                st.code(result.get("error", ""), language="text")

st.subheader("Что дальше")
st.markdown(
    """
После проверки одного камня следующий разумный шаг — массовые статусы в PostgreSQL или перевод публикации на PostgreSQL. Цены и удаление пока не трогаем.
"""
)
