from __future__ import annotations

from datetime import date
import streamlit as st
import pandas as pd

from modules.paths import ensure_dirs
from modules.storage import (
    ensure_data_files, generate_import_id, read_shipments, read_stones, read_import_log,
    get_shipment_delete_preview, delete_shipment_completely, update_stone_admin_fields
)
from modules.excel_importer import read_workbook, normalize_stones, get_template_version
from modules.import_commit import commit_import
from modules.raw_lookup import get_stone_raw, transpose_one_row

st.set_page_config(page_title="KURGIN Admin — Этап 2", layout="wide")
st.markdown('''
<style>
.block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 1500px;}
div[data-testid="stVerticalBlock"] {gap: 0.45rem;}
.stDataFrame {font-size: 12px;}
h1, h2, h3 {margin-bottom: 0.3rem;}
</style>
''', unsafe_allow_html=True)

ensure_dirs()
ensure_data_files()

STATUS_LABELS = {"draft": "Черновик", "ready": "Готов", "published": "Опубликован", "archived": "Архив"}
STATUS_KEYS = {v: k for k, v in STATUS_LABELS.items()}
AVAIL_LABELS = {"in_stock": "В наличии", "reserved": "Забронирован", "sold": "Продан", "removed": "Снят с продажи"}
AVAIL_KEYS = {v: k for k, v in AVAIL_LABELS.items()}
SECTION_LABELS = {"main": "Основной каталог", "large": "Крупные камни", "": "Вне текущей версии"}
SECTION_KEYS = {"Основной каталог": "main", "Крупные камни": "large"}
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


def filter_stones(stones: pd.DataFrame) -> pd.DataFrame:
    view = stones.copy()

    c1, c2, c3 = st.columns(3)
    with c1:
        shipment_options = ["Все поставки"] + sorted(view["shipment_id"].dropna().astype(str).unique().tolist())
        selected_shipment = st.selectbox("Поставка", shipment_options)
    with c2:
        section_options = ["Все разделы", "Основной каталог", "Крупные камни"]
        selected_section = st.selectbox("Раздел", section_options)
    with c3:
        shape_options = ["Все формы", "ROUND", "Не ROUND"]
        selected_shape = st.selectbox("Форма", shape_options)

    c4, c5, c6 = st.columns(3)
    with c4:
        status_options = ["Все статусы"] + list(STATUS_LABELS.values())
        selected_status = st.selectbox("Статус записи", status_options)
    with c5:
        avail_options = ["Любое наличие"] + list(AVAIL_LABELS.values())
        selected_avail = st.selectbox("Наличие", avail_options)
    with c6:
        warning_filter = st.selectbox("Предупреждения", ["Все", "С предупреждениями", "Без предупреждений"])

    search = st.text_input("Поиск по stone_id / KURGIN Import ID / Report # / Stock #").strip()

    if selected_shipment != "Все поставки":
        view = view[view["shipment_id"].astype(str) == selected_shipment]
    if selected_section != "Все разделы":
        view = view[view["catalog_section"].astype(str) == SECTION_KEYS.get(selected_section, "")]
    if selected_shape == "ROUND":
        view = view[view["shape"].astype(str).str.upper() == "ROUND"]
    elif selected_shape == "Не ROUND":
        view = view[view["shape"].astype(str).str.upper() != "ROUND"]
    if selected_status != "Все статусы":
        view = view[view["status"].astype(str) == STATUS_KEYS.get(selected_status, "")]
    if selected_avail != "Любое наличие":
        view = view[view["availability_status"].astype(str) == AVAIL_KEYS.get(selected_avail, "")]
    if warning_filter == "С предупреждениями":
        view = view[view["warning_message"].astype(str).str.len() > 0]
    elif warning_filter == "Без предупреждений":
        view = view[view["warning_message"].astype(str).str.len() == 0]
    if search:
        cols = ["stone_id", "kurgin_import_id", "report_number", "stock_number"]
        mask = pd.Series(False, index=view.index)
        for col in cols:
            if col in view.columns:
                mask = mask | view[col].astype(str).str.contains(search, case=False, na=False)
        view = view[mask]

    return view


def stone_card(stones: pd.DataFrame, selected_id: str):
    row_df = stones[stones["stone_id"].astype(str) == str(selected_id)]
    if row_df.empty:
        st.warning("Камень не найден.")
        return
    row = row_df.iloc[0].to_dict()

    st.subheader("Карточка камня")
    st.markdown(
        f"**{row.get('stone_id', '')}** · {row.get('shape', '')} · {row.get('weight', '')} ct · "
        f"{row.get('color', '')} · {row.get('clarity', '')} · Score: {row.get('kurgin_score', '')}"
    )

    a, b, c = st.columns(3)
    with a:
        st.write("**Основные параметры**")
        st.write(f"Report #: {row.get('report_number', '')}")
        st.write(f"Stock #: {row.get('stock_number', '')}")
        st.write(f"Cut: {row.get('cut', '')}")
        st.write(f"Polish: {row.get('polish', '')}")
        st.write(f"Symmetry: {row.get('symmetry', '')}")
        st.write(f"Fluorescence: {row.get('fluorescence', '')}")
    with b:
        st.write("**Размеры**")
        st.write(f"Measurements: {row.get('measurements', '')}")
        st.write(f"Min Diameter: {row.get('min_diameter', '')}")
        st.write(f"Max Diameter: {row.get('max_diameter', '')}")
        st.write(f"Depth MM: {row.get('depth_mm', '')}")
        st.write(f"Score Status: {SCORE_LABELS.get(row.get('score_status', ''), row.get('score_status', ''))}")
    with c:
        st.write("**Поставка**")
        st.write(f"Номер: {row.get('shipment_id', '')}")
        st.write(f"Поставщик: {row.get('supplier_name', '')}")
        st.write(f"Дата: {row.get('shipment_date', '')}")
        st.write(f"Файл: {row.get('source_file', '')}")

    if row.get("warning_message", ""):
        st.warning(row.get("warning_message", ""))
    if row.get("validation_message", ""):
        st.info(row.get("validation_message", ""))

    st.write("**Административный блок**")
    e1, e2, e3 = st.columns(3)
    with e1:
        current_section_label = SECTION_LABELS.get(row.get("catalog_section", ""), "Основной каталог")
        section_label = st.selectbox("Раздел", ["Основной каталог", "Крупные камни"], index=0 if current_section_label == "Основной каталог" else 1)
    with e2:
        current_status_label = STATUS_LABELS.get(row.get("status", "draft"), "Черновик")
        status_label = st.selectbox("Статус записи", list(STATUS_KEYS.keys()), index=list(STATUS_KEYS.keys()).index(current_status_label) if current_status_label in STATUS_KEYS else 0)
    with e3:
        current_avail_label = AVAIL_LABELS.get(row.get("availability_status", "in_stock"), "В наличии")
        avail_label = st.selectbox("Наличие", list(AVAIL_KEYS.keys()), index=list(AVAIL_KEYS.keys()).index(current_avail_label) if current_avail_label in AVAIL_KEYS else 0)

    admin_note = st.text_area("Заметка администратора", value=row.get("admin_note", ""), height=80)
    validation_message = st.text_area("Комментарий проверки", value=row.get("validation_message", ""), height=80)

    if st.button("Сохранить административные изменения", type="primary"):
        result = update_stone_admin_fields(
            stone_id=row.get("stone_id", ""),
            catalog_section=SECTION_KEYS.get(section_label, row.get("catalog_section", "main")),
            status=STATUS_KEYS.get(status_label, row.get("status", "draft")),
            availability_status=AVAIL_KEYS.get(avail_label, row.get("availability_status", "in_stock")),
            admin_note=admin_note,
            validation_message=validation_message,
        )
        if result["updated"]:
            st.success(f"Сохранено. Backup: {result['backup_dir']}")
            st.rerun()
        else:
            st.error(result["message"])

    raw = get_stone_raw(row.get("import_id", ""), row.get("report_number", ""), row.get("stock_number", ""))

    with st.expander("Raw: Results по этому камню", expanded=False):
        st.dataframe(transpose_one_row(raw["results"]), use_container_width=True, hide_index=True, height=420)
    with st.expander("Raw: Details по этому камню", expanded=False):
        st.dataframe(transpose_one_row(raw["details"]), use_container_width=True, hide_index=True, height=520)
    with st.expander("Raw: Issues по этому камню", expanded=False):
        if raw["issues"].empty:
            st.info("Issues по этому камню не найдены.")
        else:
            st.dataframe(raw["issues"], use_container_width=True, hide_index=True, height=240)


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
        filtered = filter_stones(stones)
        st.caption(f"Найдено камней: {len(filtered)}")

        compact_table(filtered, [
            "stone_id", "report_number", "stock_number", "shape", "weight", "color", "clarity",
            "fluorescence", "min_diameter", "max_diameter", "depth_mm",
            "kurgin_score", "score_status", "catalog_section", "status", "availability_status",
            "shipment_id", "warning_message"
        ], height=420)

        st.divider()
        if filtered.empty:
            st.info("Нет камней по выбранным фильтрам.")
        else:
            selected_stone = st.selectbox("Открыть карточку камня", filtered["stone_id"].astype(str).tolist())
            stone_card(stones, selected_stone)

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
    st.info("Изменения правил принимаются только после обсуждения. Этап 2: фильтры, поиск, карточка камня и административное редактирование.")
