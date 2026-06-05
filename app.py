from __future__ import annotations

from datetime import date
import streamlit as st
import pandas as pd

from modules.paths import ensure_dirs
from modules.storage import (
    ensure_data_files, generate_import_id, read_shipments, read_stones, read_import_log,
    get_shipment_delete_preview, delete_shipment_completely
)
from modules.excel_importer import read_workbook, normalize_stones, get_template_version
from modules.import_commit import commit_import

st.set_page_config(page_title="KURGIN Admin — Этап 1", layout="wide")
st.markdown('''
<style>
.block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 1400px;}
div[data-testid="stVerticalBlock"] {gap: 0.45rem;}
.stDataFrame {font-size: 12px;}
h1, h2, h3 {margin-bottom: 0.3rem;}
</style>
''', unsafe_allow_html=True)

ensure_dirs()
ensure_data_files()

STATUS_LABELS = {"draft": "Черновик", "ready": "Готов", "published": "Опубликован", "archived": "Архив"}
AVAIL_LABELS = {"in_stock": "В наличии", "reserved": "Забронирован", "sold": "Продан", "removed": "Снят с продажи"}
SECTION_LABELS = {"main": "Основной каталог", "large": "Крупные камни", "": "Вне текущей версии"}
SCORE_LABELS = {"calculated": "Рассчитан", "not_available_for_shape": "Недоступен для формы"}
NUMERIC_COLUMNS = ["weight", "kurgin_score", "min_diameter", "max_diameter", "depth_mm"]


def labelize(df):
    if df.empty:
        return df
    view = df.copy()
    for col in NUMERIC_COLUMNS:
        if col in view.columns:
            view[col] = pd.to_numeric(view[col], errors="coerce")
    for col, mapping in [
        ("status", STATUS_LABELS),
        ("availability_status", AVAIL_LABELS),
        ("catalog_section", SECTION_LABELS),
        ("score_status", SCORE_LABELS),
    ]:
        if col in view.columns:
            view[col] = view[col].map(mapping).fillna(view[col])
    return view


def compact_table(df, columns, height=360):
    cols = [c for c in columns if c in df.columns]
    st.dataframe(labelize(df[cols]), use_container_width=True, height=height, hide_index=True)

page = st.sidebar.radio("Раздел", ["Загрузка поставки", "Поставки", "Камни", "Журнал импорта", "Правила"])

if page == "Загрузка поставки":
    st.title("Загрузка поставки")
    st.caption("Этап 1: безопасный импорт готового Excel KURGIN Score Result.")

    with st.form("shipment_form", clear_on_submit=False):
        c1, c2, c3 = st.columns([1.2, 1, 1])
        with c1:
            supplier_name = st.text_input("Поставщик *")
            shipment_name = st.text_input("Название / номер поставки *")
        with c2:
            shipment_date = st.date_input("Дата поставки *", value=date.today())
            currency = st.selectbox("Валюта *", ["USD", "EUR", "RUB", "AED"], index=0)
        with c3:
            total_purchase_cost = st.number_input("Стоимость закупки всей партии *", min_value=0.0, step=100.0, format="%.2f")
            advance_paid = st.number_input("Аванс *", min_value=0.0, step=100.0, format="%.2f")

        c4, c5 = st.columns(2)
        with c4:
            payment_comment = st.text_input("Комментарий по оплате")
        with c5:
            comment = st.text_input("Общий комментарий")

        uploaded = st.file_uploader("Excel-файл KURGIN Score Result *", type=["xlsx"])
        submitted = st.form_submit_button("Показать предпросмотр", use_container_width=True)

    if submitted:
        missing = []
        if not supplier_name:
            missing.append("Поставщик")
        if not shipment_name:
            missing.append("Название / номер поставки")
        if not uploaded:
            missing.append("Excel-файл")
        if total_purchase_cost <= 0:
            missing.append("Стоимость закупки всей партии")

        if missing:
            st.error("Заполните обязательные поля: " + ", ".join(missing))
        else:
            uploaded_bytes = uploaded.getvalue()
            workbook, errors = read_workbook(uploaded_bytes)

            if errors:
                st.error("Импорт заблокирован.")
                for err in errors:
                    st.warning(err)
            else:
                import_id = generate_import_id()
                shipment = {
                    "supplier_name": supplier_name,
                    "shipment_date": str(shipment_date),
                    "shipment_name": shipment_name,
                    "currency": currency,
                    "total_purchase_cost": total_purchase_cost,
                    "advance_paid": advance_paid,
                    "payment_comment": payment_comment,
                    "comment": comment,
                }
                saved_df, not_saved_df, stats = normalize_stones(
                    workbook["Results"], workbook["Details"], workbook["Issues"],
                    shipment, import_id, uploaded.name
                )
                template_version = get_template_version(workbook["System"])
                st.session_state["preview"] = {
                    "import_id": import_id,
                    "shipment": shipment,
                    "uploaded_bytes": uploaded_bytes,
                    "original_filename": uploaded.name,
                    "workbook": workbook,
                    "saved_df": saved_df,
                    "not_saved_df": not_saved_df,
                    "stats": stats,
                    "template_version": template_version,
                }

    preview = st.session_state.get("preview")
    if preview:
        st.divider()
        st.subheader("Предпросмотр импорта")

        stats = preview["stats"]
        shipment = preview["shipment"]
        balance = float(shipment.get("total_purchase_cost") or 0) - float(shipment.get("advance_paid") or 0)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Номер поставки", preview["import_id"])
        m2.metric("Найдено строк", stats.get("total", 0))
        m3.metric("Будет сохранено", stats.get("saved", 0))
        m4.metric("Не сохранится", stats.get("not_saved", 0))
        m5.metric("Предупреждения", stats.get("warnings", 0))

        c1, c2, c3 = st.columns(3)
        c1.write(f"**Поставщик:** {shipment.get('supplier_name')}")
        c1.write(f"**Поставка:** {shipment.get('shipment_name')}")
        c2.write(f"**Дата:** {shipment.get('shipment_date')}")
        c2.write(f"**Валюта:** {shipment.get('currency')}")
        c3.write(f"**Стоимость:** {shipment.get('total_purchase_cost')}")
        c3.write(f"**Аванс / остаток:** {shipment.get('advance_paid')} / {balance:.2f}")

        if preview.get("template_version"):
            st.caption(f"Версия / служебная информация: {preview.get('template_version')}")

        if stats.get("conflicts", 0):
            st.error("Найдены конфликты ID. Этап 1 не перезаписывает существующие камни.")
        else:
            st.success("Конфликтов ID не найдено.")

        with st.expander("Камни, которые будут сохранены", expanded=True):
            compact_table(preview["saved_df"], [
                "stone_id", "report_number", "stock_number", "shape", "weight", "color", "clarity",
                "fluorescence", "min_diameter", "max_diameter", "depth_mm",
                "kurgin_score", "score_status", "catalog_section", "status", "availability_status", "warning_message"
            ])

        with st.expander("Камни вне текущей версии / не сохраняются", expanded=False):
            ns = preview["not_saved_df"]
            if ns.empty:
                st.info("Нет строк, которые не сохраняются.")
            else:
                compact_table(ns, ["stone_id", "report_number", "stock_number", "shape", "weight", "color", "clarity", "not_saved_reason", "validation_message"])

        with st.expander("Служебные данные файла", expanded=False):
            st.dataframe(preview["workbook"]["System"], use_container_width=True, height=260, hide_index=True)

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("Подтвердить импорт", type="primary", use_container_width=True, disabled=stats.get("conflicts", 0) > 0):
                commit_import(
                    preview["import_id"], preview["uploaded_bytes"], preview["workbook"], preview["saved_df"],
                    stats.get("not_saved", 0), stats, preview["shipment"],
                    preview["original_filename"], preview.get("template_version", "")
                )
                st.success("Поставка успешно импортирована.")
                del st.session_state["preview"]
                st.rerun()
        with b2:
            if st.button("Отменить импорт", use_container_width=True):
                del st.session_state["preview"]
                st.info("Импорт отменён. Постоянные файлы не изменены.")
                st.rerun()
        with b3:
            st.caption("Чтобы изменить данные поставки, исправьте форму сверху и снова нажмите предпросмотр.")

elif page == "Поставки":
    st.title("Поставки")
    shipments = read_shipments()

    if shipments.empty:
        st.info("Поставок пока нет.")
    else:
        compact_table(shipments, [
            "shipment_id", "supplier_name", "shipment_date", "shipment_name", "currency",
            "total_purchase_cost", "advance_paid", "created_at", "original_filename"
        ], height=360)

        st.divider()
        st.subheader("Опасная команда: удалить поставку полностью")
        st.warning("Удаление уберёт поставку, камни этой поставки, запись импорта и raw-файлы. Перед удалением будет создан backup.")

        shipment_ids = sorted(shipments["shipment_id"].astype(str).tolist())
        selected = st.selectbox("Поставка для удаления", shipment_ids)
        preview = get_shipment_delete_preview(selected)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Камней будет удалено", preview["stones_count"])
        c2.metric("Строк поставки", preview["shipment_rows"])
        c3.metric("Строк import_log", preview["log_rows"])
        c4.metric("Raw-папка", "есть" if preview["raw_dir_exists"] else "нет")

        st.caption(f"Raw-папка: {preview['raw_dir']}")
        confirm_text = st.text_input(f"Для подтверждения введите номер поставки: {selected}")

        if st.button("Удалить поставку полностью", type="primary", disabled=(confirm_text != selected)):
            result = delete_shipment_completely(selected)
            st.success("Поставка удалена полностью.")
            st.write(f"Удалено камней: {result['stones_deleted']}")
            st.write(f"Удалено строк поставки: {result['shipment_rows_deleted']}")
            st.write(f"Удалено строк import_log: {result['log_rows_deleted']}")
            st.write(f"Raw-папка удалена: {'да' if result['raw_deleted'] else 'нет'}")
            st.write(f"Backup: {result['backup_dir']}")
            st.rerun()

elif page == "Камни":
    st.title("Камни")
    stones = read_stones()
    if stones.empty:
        st.info("Камней пока нет.")
    else:
        shipments = ["Все поставки"] + sorted(stones["shipment_id"].dropna().astype(str).unique().tolist())
        selected = st.selectbox("Поставка", shipments)
        view = stones if selected == "Все поставки" else stones[stones["shipment_id"].astype(str) == selected]
        st.caption("Этап 1: просмотр без редактирования.")
        compact_table(view, [
            "stone_id", "report_number", "stock_number", "shape", "weight", "color", "clarity",
            "fluorescence", "min_diameter", "max_diameter", "depth_mm",
            "kurgin_score", "score_status", "catalog_section", "status", "availability_status",
            "shipment_id", "warning_message"
        ], height=520)

elif page == "Журнал импорта":
    st.title("Журнал импорта")
    log = read_import_log()
    if log.empty:
        st.info("Журнал пока пуст.")
    else:
        compact_table(log, [
            "import_id", "source_file", "imported_at", "rows_total", "rows_saved", "rows_not_saved",
            "warnings_count", "conflicts_count", "status", "message"
        ], height=420)

elif page == "Правила":
    st.title("Правила")
    st.info("Изменения правил принимаются только после обсуждения. Этап 1 включает безопасное удаление конкретной поставки.")
