from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from modules.paths import ensure_dirs
from modules.storage import ensure_data_files, generate_import_id, read_shipments, read_stones, read_import_log
from modules.excel_importer import read_workbook, normalize_stones, get_template_version
from modules.import_commit import commit_import


st.set_page_config(page_title="KURGIN Admin — Этап 1", layout="wide")

st.markdown(
    '''
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 1400px;}
    div[data-testid="stVerticalBlock"] {gap: 0.45rem;}
    div[data-testid="stHorizontalBlock"] {gap: 0.6rem;}
    .stDataFrame {font-size: 12px;}
    h1, h2, h3 {margin-bottom: 0.3rem;}
    .small-note {font-size: 0.85rem; color: #666;}
    </style>
    ''',
    unsafe_allow_html=True,
)

ensure_dirs()
ensure_data_files()

STATUS_LABELS = {
    "draft": "Черновик",
    "ready": "Готов",
    "published": "Опубликован",
    "archived": "Архив",
}
AVAIL_LABELS = {
    "in_stock": "В наличии",
    "reserved": "Забронирован",
    "sold": "Продан",
    "removed": "Снят с продажи",
}
SECTION_LABELS = {
    "main": "Основной каталог",
    "large": "Крупные камни",
    "": "Вне текущей версии",
}
SCORE_LABELS = {
    "calculated": "Рассчитан",
    "not_available_for_shape": "Недоступен для формы",
}


def labelize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    view = df.copy()
    if "status" in view.columns:
        view["status"] = view["status"].map(STATUS_LABELS).fillna(view["status"])
    if "availability_status" in view.columns:
        view["availability_status"] = view["availability_status"].map(AVAIL_LABELS).fillna(view["availability_status"])
    if "catalog_section" in view.columns:
        view["catalog_section"] = view["catalog_section"].map(SECTION_LABELS).fillna(view["catalog_section"])
    if "score_status" in view.columns:
        view["score_status"] = view["score_status"].map(SCORE_LABELS).fillna(view["score_status"])
    return view


def compact_table(df: pd.DataFrame, columns: list[str], height: int = 360):
    cols = [c for c in columns if c in df.columns]
    st.dataframe(labelize(df[cols]), use_container_width=True, height=height, hide_index=True)


page = st.sidebar.radio(
    "Раздел",
    ["Загрузка поставки", "Поставки", "Камни", "Журнал импорта", "Правила"],
)

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
                    workbook["Results"],
                    workbook["Details"],
                    workbook["Issues"],
                    shipment,
                    import_id,
                    uploaded.name,
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
            st.error("Найдены конфликты ID. Этап 1 не перезаписывает существующие камни. Обработка конфликтов будет отдельным этапом.")
        else:
            st.success("Конфликтов ID не найдено.")

        with st.expander("Камни, которые будут сохранены", expanded=True):
            compact_table(
                preview["saved_df"],
                ["stone_id", "report_number", "stock_number", "shape", "weight", "color", "clarity", "kurgin_score", "score_status", "catalog_section", "status", "availability_status", "warning_message"],
                height=360,
            )

        with st.expander("Камни вне текущей версии / не сохраняются", expanded=False):
            ns = preview["not_saved_df"]
            if ns.empty:
                st.info("Нет строк, которые не сохраняются.")
            else:
                cols = ["stone_id", "report_number", "stock_number", "shape", "weight", "color", "clarity", "not_saved_reason", "validation_message"]
                compact_table(ns, cols, height=300)

        with st.expander("Служебные данные файла", expanded=False):
            st.dataframe(preview["workbook"]["System"], use_container_width=True, height=260, hide_index=True)

        b1, b2, b3 = st.columns(3)
        with b1:
            disabled = stats.get("conflicts", 0) > 0
            if st.button("Подтвердить импорт", type="primary", use_container_width=True, disabled=disabled):
                result = commit_import(
                    import_id=preview["import_id"],
                    uploaded_bytes=preview["uploaded_bytes"],
                    workbook=preview["workbook"],
                    saved_stones=preview["saved_df"],
                    not_saved_count=stats.get("not_saved", 0),
                    stats=stats,
                    shipment=preview["shipment"],
                    original_filename=preview["original_filename"],
                    excel_template_version=preview.get("template_version", ""),
                )
                st.session_state["last_import_id"] = preview["import_id"]
                del st.session_state["preview"]
                st.success("Поставка успешно импортирована.")
                st.info(f"Номер поставки: {st.session_state['last_import_id']}")
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
        show_cols = ["shipment_id", "supplier_name", "shipment_date", "shipment_name", "currency", "total_purchase_cost", "advance_paid", "created_at", "original_filename"]
        compact_table(shipments, show_cols, height=420)

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
        compact_table(
            view,
            ["stone_id", "report_number", "stock_number", "shape", "weight", "color", "clarity", "kurgin_score", "score_status", "catalog_section", "status", "availability_status", "shipment_id", "warning_message"],
            height=520,
        )

elif page == "Журнал импорта":
    st.title("Журнал импорта")
    log = read_import_log()
    if log.empty:
        st.info("Журнал пока пуст.")
    else:
        compact_table(log, ["import_id", "source_file", "imported_at", "rows_total", "rows_saved", "rows_not_saved", "warnings_count", "conflicts_count", "status", "message"], height=420)

elif page == "Правила":
    st.title("Правила")
    st.write("Основные rules-документы лежат в папке `rules/`.")
    st.info("Этап 1 не редактирует правила из интерфейса. Изменения правил принимаются только после обсуждения.")
