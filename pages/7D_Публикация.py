from __future__ import annotations

import streamlit as st
import pandas as pd

from modules.storage import ensure_data_files, read_stones, build_public_layer_preview, build_public_export_preview, build_public_stones_v1_csv_bytes
from modules.publish_stage_7d import (
    PUBLISH_CONFIRMATION_TEXT,
    UNPUBLISH_CONFIRMATION_TEXT,
    ARCHIVE_CONFIRMATION_TEXT,
    EXPORT_CONFIRMATION_TEXT,
    build_publish_preview,
    build_unpublish_preview,
    commit_publish,
    commit_unpublish,
    commit_archive,
    write_public_export_file,
)

st.set_page_config(page_title="KURGIN Admin — 7D Публикация", layout="wide")
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

ensure_data_files()

STATUS_LABELS = {"draft": "Черновик", "ready": "Готов", "published": "Опубликован", "archived": "Архив"}
AVAIL_LABELS = {"in_stock": "В наличии", "reserved": "Забронирован", "sold": "Продан", "removed": "Снят с продажи"}
SECTION_LABELS = {"main": "Основной каталог", "large": "Крупные камни", "": "Вне текущей версии"}


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


def filter_stones_for_publish(stones: pd.DataFrame) -> pd.DataFrame:
    view = stones.copy()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        shipment_options = ["Все поставки"] + sorted(view["shipment_id"].dropna().astype(str).unique().tolist()) if "shipment_id" in view.columns else ["Все поставки"]
        selected_shipment = st.selectbox("Поставка", shipment_options)
    with c2:
        section_options = ["Все разделы", "Основной каталог", "Крупные камни"]
        selected_section = st.selectbox("Раздел", section_options)
    with c3:
        status_options = ["Все статусы", "Черновик", "Готов", "Опубликован", "Архив"]
        selected_status = st.selectbox("Статус записи", status_options)
    with c4:
        avail_options = ["Любое наличие", "В наличии", "Забронирован", "Продан", "Снят с продажи"]
        selected_avail = st.selectbox("Наличие", avail_options)

    search = st.text_input("Поиск по stone_id / Report # / Stock #").strip()

    if selected_shipment != "Все поставки" and "shipment_id" in view.columns:
        view = view[view["shipment_id"].astype(str) == selected_shipment]
    if selected_section != "Все разделы" and "catalog_section" in view.columns:
        section_key = {"Основной каталог": "main", "Крупные камни": "large"}.get(selected_section, "")
        view = view[view["catalog_section"].astype(str) == section_key]
    if selected_status != "Все статусы" and "status" in view.columns:
        status_key = {v: k for k, v in STATUS_LABELS.items()}.get(selected_status, "")
        view = view[view["status"].astype(str) == status_key]
    if selected_avail != "Любое наличие" and "availability_status" in view.columns:
        avail_key = {v: k for k, v in AVAIL_LABELS.items()}.get(selected_avail, "")
        view = view[view["availability_status"].astype(str) == avail_key]
    if search:
        cols = ["stone_id", "report_number", "stock_number", "kurgin_import_id"]
        mask = pd.Series(False, index=view.index)
        for col in cols:
            if col in view.columns:
                mask = mask | view[col].astype(str).str.contains(search, case=False, na=False)
        view = view[mask]

    return view


def show_preview_table(df: pd.DataFrame, height: int = 360) -> None:
    if df.empty:
        st.info("Нет строк для показа.")
        return
    cols = [
        "stone_id", "report_number", "shipment_id", "shape", "weight", "color", "clarity",
        "status", "availability_status", "catalog_section", "public_price_display", "price_status", "action", "reason",
    ]
    cols = [c for c in cols if c in df.columns]
    st.dataframe(labelize(df[cols]), use_container_width=True, hide_index=True, height=height)


st.title("Этап 7D — публикация, снятие с публикации и публичный экспорт")
st.caption("Массовые действия меняют stones_master.csv только после preview, фразы подтверждения и backup. Публичный экспорт записывается отдельно в exports/public_stones_v1.csv.")

stones = read_stones()
if stones.empty:
    st.warning("В stones_master.csv пока нет камней.")
    st.stop()

filtered = filter_stones_for_publish(stones)

st.subheader("1. Отфильтрованные камни")
metric_cols = st.columns(5)
metric_cols[0].metric("В фильтре", len(filtered))
metric_cols[1].metric("Опубликованы", int((filtered["status"].astype(str) == "published").sum()) if "status" in filtered.columns else 0)
metric_cols[2].metric("Готовы", int((filtered["status"].astype(str) == "ready").sum()) if "status" in filtered.columns else 0)
metric_cols[3].metric("В наличии", int((filtered["availability_status"].astype(str) == "in_stock").sum()) if "availability_status" in filtered.columns else 0)
metric_cols[4].metric("Цена по запросу", int((filtered.get("allow_price_on_request", pd.Series([], dtype=str)).astype(str).str.lower() == "true").sum()) if "allow_price_on_request" in filtered.columns else 0)

base_cols = [
    "stone_id", "report_number", "shipment_id", "shape", "weight", "color", "clarity",
    "status", "availability_status", "catalog_section", "public_price_display", "price_status", "allow_price_on_request",
]
base_cols = [c for c in base_cols if c in filtered.columns]
st.dataframe(labelize(filtered[base_cols]), use_container_width=True, hide_index=True, height=360)

stone_options = filtered["stone_id"].dropna().astype(str).tolist() if "stone_id" in filtered.columns else []
selected_ids = st.multiselect("Выбрать камни вручную", stone_options)
use_all_filtered = st.checkbox("Использовать все камни из текущего фильтра", value=False)
action_ids = stone_options if use_all_filtered else selected_ids

st.divider()
st.subheader("2. Preview публикации")
publish_preview = build_publish_preview(filtered if use_all_filtered else stones, action_ids)
pub_summary = publish_preview.get("summary", {})
p1, p2, p3 = st.columns(3)
p1.metric("Выбрано", pub_summary.get("selected", 0))
p2.metric("Будет опубликовано", pub_summary.get("ready", 0))
p3.metric("Будет пропущено", pub_summary.get("blocked", 0))
show_preview_table(publish_preview.get("preview_df", pd.DataFrame()), height=320)

with st.expander("Подтверждение публикации", expanded=False):
    st.warning(f"Для публикации введите: {PUBLISH_CONFIRMATION_TEXT}")
    publish_confirm = st.text_input("Фраза подтверждения публикации", key="publish_confirm")
    if st.button("Опубликовать готовые выбранные камни", type="primary"):
        if publish_confirm != PUBLISH_CONFIRMATION_TEXT:
            st.error("Фраза подтверждения не совпадает.")
        else:
            result = commit_publish(action_ids)
            st.success(f"{result.get('message')} Обновлено: {result.get('updated', 0)}. Backup: {result.get('backup_dir', '')}")
            st.rerun()

st.divider()
st.subheader("3. Preview снятия с публикации")
unpublish_preview = build_unpublish_preview(filtered if use_all_filtered else stones, action_ids)
unpub_summary = unpublish_preview.get("summary", {})
u1, u2, u3 = st.columns(3)
u1.metric("Выбрано", unpub_summary.get("selected", 0))
u2.metric("Будет снято", unpub_summary.get("ready", 0))
u3.metric("Будет пропущено", unpub_summary.get("blocked", 0))
show_preview_table(unpublish_preview.get("preview_df", pd.DataFrame()), height=260)

with st.expander("Подтверждение снятия с публикации", expanded=False):
    st.warning(f"Для снятия с публикации введите: {UNPUBLISH_CONFIRMATION_TEXT}")
    unpublish_confirm = st.text_input("Фраза подтверждения снятия", key="unpublish_confirm")
    if st.button("Снять выбранные опубликованные камни", type="secondary"):
        if unpublish_confirm != UNPUBLISH_CONFIRMATION_TEXT:
            st.error("Фраза подтверждения не совпадает.")
        else:
            result = commit_unpublish(action_ids)
            st.success(f"{result.get('message')} Обновлено: {result.get('updated', 0)}. Backup: {result.get('backup_dir', '')}")
            st.rerun()

st.divider()
st.subheader("4. Архив выбранных камней")
st.caption("Архив меняет status на archived. Такие камни не попадают в публичный экспорт.")
with st.expander("Опасное действие: архив", expanded=False):
    st.warning(f"Для архива введите: {ARCHIVE_CONFIRMATION_TEXT}")
    archive_confirm = st.text_input("Фраза подтверждения архива", key="archive_confirm")
    if st.button("Отправить выбранные камни в архив"):
        if archive_confirm != ARCHIVE_CONFIRMATION_TEXT:
            st.error("Фраза подтверждения не совпадает.")
        else:
            result = commit_archive(action_ids)
            st.success(f"{result.get('message')} Обновлено: {result.get('updated', 0)}. Backup: {result.get('backup_dir', '')}")
            st.rerun()

st.divider()
st.subheader("5. Публичный экспорт")
public_data = build_public_layer_preview()
export_data = build_public_export_preview(public_data)
export_summary = export_data.get("summary", {})
export_df = export_data.get("export_df", pd.DataFrame())

e1, e2, e3, e4 = st.columns(4)
e1.metric("Строк в экспорте", export_summary.get("rows", 0))
e2.metric("Числовая цена", export_summary.get("numeric", 0))
e3.metric("Цена по запросу", export_summary.get("price_on_request", 0))
e4.metric("Schema", export_summary.get("schema_version", "public_stones_v1"))

st.dataframe(export_df, use_container_width=True, hide_index=True, height=360)
st.download_button(
    "Скачать public_stones_v1.csv без записи файла",
    data=build_public_stones_v1_csv_bytes(export_df),
    file_name=export_summary.get("filename", "public_stones_v1.csv"),
    mime="text/csv",
)

with st.expander("Записать exports/public_stones_v1.csv", expanded=False):
    st.warning(f"Для записи публичного экспорта введите: {EXPORT_CONFIRMATION_TEXT}")
    export_confirm = st.text_input("Фраза подтверждения экспорта", key="export_confirm")
    if st.button("Записать файл exports/public_stones_v1.csv", type="primary"):
        if export_confirm != EXPORT_CONFIRMATION_TEXT:
            st.error("Фраза подтверждения не совпадает.")
        else:
            result = write_public_export_file()
            summary = result.get("summary", {})
            st.success(f"Экспорт записан: {result.get('path')}. Строк: {summary.get('rows', 0)}. Backup: {result.get('backup_dir', '')}")
            st.rerun()
