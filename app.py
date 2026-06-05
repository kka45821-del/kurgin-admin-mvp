from __future__ import annotations

from datetime import date
import streamlit as st
import pandas as pd

from modules.paths import ensure_dirs
from modules.storage import (
    ensure_data_files, generate_import_id, read_shipments, read_stones, read_import_log, read_payments,
    get_shipment_delete_preview, delete_shipment_completely, update_stone_admin_fields,
    update_shipment_fields, add_payment, delete_payment, update_existing_stones_from_import
)
from modules.excel_importer import read_workbook, normalize_stones, get_template_version, split_conflicts, apply_report_corrections_to_results
from modules.import_commit import commit_import
from modules.raw_lookup import get_stone_raw, transpose_one_row
from modules.shipment_files import list_attachments, save_attachment, delete_attachment

st.set_page_config(page_title="KURGIN Admin — Этап 4", layout="wide")
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




def to_num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)


def shipment_summary_table(shipments, stones, payments):
    if shipments.empty:
        return pd.DataFrame()
    rows = []
    for _, sh in shipments.iterrows():
        sid = str(sh.get("shipment_id", ""))
        ss = stones[stones["shipment_id"].astype(str) == sid] if not stones.empty else pd.DataFrame()
        pp = payments[payments["shipment_id"].astype(str) == sid] if not payments.empty else pd.DataFrame()
        total_cost = float(pd.to_numeric(pd.Series([sh.get("total_purchase_cost", 0)]), errors="coerce").fillna(0).iloc[0])
        paid = float(to_num(pp["amount"]).sum()) if not pp.empty and "amount" in pp.columns else 0
        rows.append({
            "shipment_id": sid,
            "supplier_id": sh.get("supplier_id", ""),
            "supplier_name": sh.get("supplier_name", ""),
            "shipment_date": sh.get("shipment_date", ""),
            "shipment_name": sh.get("shipment_name", ""),
            "currency": sh.get("currency", ""),
            "stones_total": len(ss),
            "in_stock": int((ss["availability_status"].astype(str) == "in_stock").sum()) if not ss.empty else 0,
            "reserved": int((ss["availability_status"].astype(str) == "reserved").sum()) if not ss.empty else 0,
            "sold": int((ss["availability_status"].astype(str) == "sold").sum()) if not ss.empty else 0,
            "removed": int((ss["availability_status"].astype(str) == "removed").sum()) if not ss.empty else 0,
            "main": int((ss["catalog_section"].astype(str) == "main").sum()) if not ss.empty else 0,
            "large": int((ss["catalog_section"].astype(str) == "large").sum()) if not ss.empty else 0,
            "round": int((ss["shape"].astype(str).str.upper() == "ROUND").sum()) if not ss.empty else 0,
            "not_round": int((ss["shape"].astype(str).str.upper() != "ROUND").sum()) if not ss.empty else 0,
            "warnings": int((ss["warning_message"].astype(str).str.len() > 0).sum()) if not ss.empty else 0,
            "total_purchase_cost": total_cost,
            "paid_total": paid,
            "balance_due": total_cost - paid,
            "comment": sh.get("comment", ""),
        })
    return pd.DataFrame(rows)


def weight_bucket(value) -> str:
    try:
        w = float(value)
    except Exception:
        return "Нет веса"
    if 1.00 <= w < 1.50:
        return "1.00–1.49 ct"
    if 1.50 <= w < 2.00:
        return "1.50–1.99 ct"
    if 2.00 <= w < 2.50:
        return "2.00–2.49 ct"
    if 2.50 <= w < 3.00:
        return "2.50–2.99 ct"
    if 3.00 <= w < 4.00:
        return "3.00–3.99 ct"
    if 4.00 <= w < 5.00:
        return "4.00–4.99 ct"
    if w >= 5.00:
        return "5.00+ ct"
    return "Вне диапазонов"


def assortment_summary_table(stones: pd.DataFrame) -> pd.DataFrame:
    if stones.empty:
        return pd.DataFrame(columns=[
            "Форма", "Диапазон веса", "Цвет", "Чистота",
            "Всего", "В наличии", "Забронировано", "Продано", "Снято", "Архив",
        ])

    df = stones.copy()
    df["Форма"] = df.get("shape", "").astype(str).str.upper()
    df["Диапазон веса"] = df.get("weight", "").apply(weight_bucket)
    df["Цвет"] = df.get("color", "").astype(str)
    df["Чистота"] = df.get("clarity", "").astype(str)

    grouped = (
        df.groupby(["Форма", "Диапазон веса", "Цвет", "Чистота"], dropna=False)
        .agg(
            Всего=("stone_id", "count"),
            **{
                "В наличии": ("availability_status", lambda s: int((s.astype(str) == "in_stock").sum())),
                "Забронировано": ("availability_status", lambda s: int((s.astype(str) == "reserved").sum())),
                "Продано": ("availability_status", lambda s: int((s.astype(str) == "sold").sum())),
                "Снято": ("availability_status", lambda s: int((s.astype(str) == "removed").sum())),
                "Архив": ("status", lambda s: int((s.astype(str) == "archived").sum())),
            }
        )
        .reset_index()
    )

    order = {
        "1.00–1.49 ct": 1,
        "1.50–1.99 ct": 2,
        "2.00–2.49 ct": 3,
        "2.50–2.99 ct": 4,
        "3.00–3.99 ct": 5,
        "4.00–4.99 ct": 6,
        "5.00+ ct": 7,
        "Вне диапазонов": 8,
        "Нет веса": 9,
    }
    grouped["_sort"] = grouped["Диапазон веса"].map(order).fillna(99)
    grouped = grouped.sort_values(["Форма", "_sort", "Цвет", "Чистота"]).drop(columns=["_sort"])
    return grouped



def shipment_card(shipment_id, shipments, stones, payments):
    row_df = shipments[shipments["shipment_id"].astype(str) == str(shipment_id)]
    if row_df.empty:
        st.warning("Поставка не найдена.")
        return
    row = row_df.iloc[0].to_dict()
    ss = stones[stones["shipment_id"].astype(str) == str(shipment_id)] if not stones.empty else pd.DataFrame()
    pp = payments[payments["shipment_id"].astype(str) == str(shipment_id)] if not payments.empty else pd.DataFrame()
    st.subheader(f"Карточка поставки: {shipment_id}")
    total_cost = float(pd.to_numeric(pd.Series([row.get("total_purchase_cost", 0)]), errors="coerce").fillna(0).iloc[0])
    paid_total = float(to_num(pp["amount"]).sum()) if not pp.empty else 0
    balance = total_cost - paid_total
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Камней", len(ss))
    m2.metric("В наличии", int((ss["availability_status"].astype(str) == "in_stock").sum()) if not ss.empty else 0)
    m3.metric("Продано", int((ss["availability_status"].astype(str) == "sold").sum()) if not ss.empty else 0)
    m4.metric("Остаток к оплате", f"{balance:.2f}")
    with st.expander("Редактировать данные поставки", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            supplier_id = st.text_input("supplier_id", value=row.get("supplier_id", ""), key=f"supid_{shipment_id}")
            supplier_name = st.text_input("Поставщик", value=row.get("supplier_name", ""), key=f"sup_{shipment_id}")
        with c2:
            shipment_date = st.text_input("Дата поставки", value=row.get("shipment_date", ""), key=f"date_{shipment_id}")
            shipment_name = st.text_input("Название / номер", value=row.get("shipment_name", ""), key=f"name_{shipment_id}")
        with c3:
            currency = st.text_input("Валюта", value=row.get("currency", ""), key=f"cur_{shipment_id}")
            total_purchase_cost = st.number_input("Стоимость партии", value=total_cost, step=100.0, format="%.2f", key=f"cost_{shipment_id}")
        payment_comment = st.text_area("Комментарий по оплате", value=row.get("payment_comment", ""), height=70, key=f"paycom_{shipment_id}")
        comment = st.text_area("Общий комментарий", value=row.get("comment", ""), height=70, key=f"com_{shipment_id}")
        if st.button("Сохранить данные поставки", type="primary", key=f"save_ship_{shipment_id}"):
            result = update_shipment_fields(shipment_id, {
                "supplier_id": supplier_id, "supplier_name": supplier_name, "shipment_date": shipment_date,
                "shipment_name": shipment_name, "currency": currency, "total_purchase_cost": total_purchase_cost,
                "payment_comment": payment_comment, "comment": comment,
            })
            if result["updated"]:
                st.success(f"Поставка сохранена. Backup: {result['backup_dir']}")
                st.rerun()
            else:
                st.error(result["message"])
    with st.expander("Сводка по камням поставки", expanded=True):
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        s1.metric("Основной", int((ss["catalog_section"].astype(str) == "main").sum()) if not ss.empty else 0)
        s2.metric("Крупные", int((ss["catalog_section"].astype(str) == "large").sum()) if not ss.empty else 0)
        s3.metric("ROUND", int((ss["shape"].astype(str).str.upper() == "ROUND").sum()) if not ss.empty else 0)
        s4.metric("Не ROUND", int((ss["shape"].astype(str).str.upper() != "ROUND").sum()) if not ss.empty else 0)
        s5.metric("Бронь", int((ss["availability_status"].astype(str) == "reserved").sum()) if not ss.empty else 0)
        s6.metric("Предупр.", int((ss["warning_message"].astype(str).str.len() > 0).sum()) if not ss.empty else 0)
    with st.expander("Платежи по поставке", expanded=True):
        p1, p2, p3 = st.columns(3)
        with p1:
            payment_date = st.date_input("Дата платежа", value=date.today(), key=f"pdate_{shipment_id}")
        with p2:
            amount = st.number_input("Сумма", min_value=0.0, step=100.0, format="%.2f", key=f"pamount_{shipment_id}")
        with p3:
            pay_currency = st.text_input("Валюта платежа", value=row.get("currency", ""), key=f"pcur_{shipment_id}")
        pay_comment = st.text_input("Комментарий к платежу", key=f"pcomm_{shipment_id}")
        if st.button("Добавить платёж", key=f"addpay_{shipment_id}"):
            if amount <= 0:
                st.error("Сумма платежа должна быть больше 0.")
            else:
                result = add_payment(shipment_id, str(payment_date), amount, pay_currency, pay_comment)
                st.success(f"Платёж добавлен. Backup: {result['backup_dir']}")
                st.rerun()
        if pp.empty:
            st.info("Платежей пока нет.")
        else:
            compact_table(pp, ["payment_id", "payment_date", "amount", "currency", "comment", "created_at"], height=220)
            del_id = st.selectbox("Удалить платёж", [""] + pp["payment_id"].astype(str).tolist(), key=f"delpay_{shipment_id}")
            if del_id:
                confirm = st.text_input(f"Для удаления платежа введите его ID: {del_id}", key=f"confpay_{shipment_id}")
                if st.button("Удалить платёж", disabled=(confirm != del_id), key=f"delpaybtn_{shipment_id}"):
                    result = delete_payment(del_id)
                    st.success(f"Платёж удалён. Backup: {result['backup_dir']}")
                    st.rerun()
    with st.expander("Вложения поставки", expanded=True):
        attachments = list_attachments(shipment_id)
        st.caption(f"Файлов: {len(attachments)} / 5")
        uploaded_file = st.file_uploader("Прикрепить файл к поставке", key=f"attach_{shipment_id}")
        if uploaded_file is not None and st.button("Сохранить вложение", key=f"save_attach_{shipment_id}"):
            result = save_attachment(shipment_id, uploaded_file)
            if result["ok"]:
                st.success(f"{result['message']} Backup: {result['backup_dir']}")
                st.rerun()
            else:
                st.error(result["message"])
        for file in list_attachments(shipment_id):
            cols = st.columns([3, 1, 1])
            cols[0].write(file.name)
            cols[1].download_button("Скачать", data=file.read_bytes(), file_name=file.name, key=f"down_{shipment_id}_{file.name}")
            if cols[2].button("Удалить", key=f"del_attach_{shipment_id}_{file.name}"):
                result = delete_attachment(shipment_id, file.name)
                if result["ok"]:
                    st.success(f"{result['message']} Backup: {result['backup_dir']}")
                    st.rerun()
                else:
                    st.error(result["message"])
    with st.expander("Камни этой поставки", expanded=False):
        compact_table(ss, ["stone_id", "report_number", "shape", "weight", "color", "clarity", "kurgin_score", "catalog_section", "status", "availability_status", "warning_message"], height=360)



def conflict_resolution_ui(preview):
    conflicts_df, other_not_saved_df = split_conflicts(preview["saved_df"], preview["not_saved_df"])
    if conflicts_df.empty:
        return

    st.error(f"Найдены конфликты Report #: {len(conflicts_df)}")
    st.caption("Report # уникален. Один Report # = один камень. Конфликты нужно решить до подтверждения импорта.")

    existing_stones = read_stones()
    actions = {}

    with st.expander("Конфликты Report #", expanded=True):
        for idx, row in conflicts_df.iterrows():
            report = str(row.get("report_number", ""))
            existing = existing_stones[existing_stones["report_number"].astype(str) == report]
            st.markdown(f"### Report # {report}")

            c1, c2 = st.columns(2)
            with c1:
                st.write("**Новая строка из Excel**")
                st.write(f"Stone ID: {row.get('stone_id', '')}")
                st.write(f"Stock #: {row.get('stock_number', '')}")
                st.write(f"Shape: {row.get('shape', '')}")
                st.write(f"Weight: {row.get('weight', '')}")
                st.write(f"Color / Clarity: {row.get('color', '')} / {row.get('clarity', '')}")
                st.write(f"Score: {row.get('kurgin_score', '')}")
            with c2:
                st.write("**Уже есть в базе**")
                if existing.empty:
                    st.warning("Не найден в базе, хотя конфликт отмечен.")
                else:
                    ex = existing.iloc[0]
                    st.write(f"Stone ID: {ex.get('stone_id', '')}")
                    st.write(f"Поставка: {ex.get('shipment_id', '')}")
                    st.write(f"Shape: {ex.get('shape', '')}")
                    st.write(f"Weight: {ex.get('weight', '')}")
                    st.write(f"Color / Clarity: {ex.get('color', '')} / {ex.get('clarity', '')}")
                    st.write(f"Score: {ex.get('kurgin_score', '')}")

            action = st.radio(
                "Действие",
                ["Пропустить строку", "Обновить существующий камень", "Исправить Report # в новой строке"],
                key=f"conflict_action_{idx}",
                horizontal=True,
            )

            corrected_report = ""
            if action == "Исправить Report # в новой строке":
                corrected_report = st.text_input("Новый Report # для этой строки", key=f"correct_report_{idx}")

            actions[idx] = {"action": action, "old_report": report, "new_report": corrected_report}

    st.session_state["conflict_actions"] = actions


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
            st.error("Найдены конфликты Report #. Этап 4 позволяет исправить / обновить / пропустить.")
            conflict_resolution_ui(preview)
        else:
            st.success("Конфликтов Report # не найдено.")

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
            if st.button("Подтвердить импорт", type="primary", use_container_width=True):
                actions = st.session_state.get("conflict_actions", {})
                conflicts_df, other_not_saved_df = split_conflicts(preview["saved_df"], preview["not_saved_df"])

                corrections = {}
                update_rows = []
                unresolved = []

                if not conflicts_df.empty:
                    for idx, row in conflicts_df.iterrows():
                        action_data = actions.get(idx)
                        if not action_data:
                            unresolved.append(str(row.get("report_number", "")))
                            continue
                        action = action_data.get("action")
                        if action == "Исправить Report # в новой строке":
                            new_report = str(action_data.get("new_report", "")).strip()
                            if not new_report:
                                unresolved.append(str(row.get("report_number", "")))
                            else:
                                corrections[str(row.get("report_number", ""))] = new_report
                        elif action == "Обновить существующий камень":
                            update_rows.append(row)
                        elif action == "Пропустить строку":
                            pass

                if unresolved:
                    st.error("Не все конфликты решены: " + ", ".join(unresolved))
                else:
                    workbook_to_commit = preview["workbook"].copy()
                    saved_to_commit = preview["saved_df"].copy()

                    if corrections:
                        corrected_results = apply_report_corrections_to_results(workbook_to_commit["Results"], corrections)
                        workbook_to_commit["Results"] = corrected_results
                        corrected_saved, corrected_not_saved, corrected_stats = normalize_stones(
                            corrected_results,
                            workbook_to_commit["Details"],
                            workbook_to_commit["Issues"],
                            preview["shipment"],
                            preview["import_id"],
                            preview["original_filename"],
                        )
                        corrected_conflicts, corrected_other = split_conflicts(corrected_saved, corrected_not_saved)
                        if not corrected_conflicts.empty:
                            st.error("После исправления Report # всё ещё есть конфликты. Нажмите предпросмотр ещё раз и проверьте.")
                            st.stop()
                        saved_to_commit = pd.concat([saved_to_commit, corrected_saved], ignore_index=True)

                    update_df = pd.DataFrame(update_rows) if update_rows else pd.DataFrame()

                    commit_import(
                        preview["import_id"],
                        preview["uploaded_bytes"],
                        workbook_to_commit,
                        saved_to_commit,
                        int(len(other_not_saved_df)),
                        {**stats, "conflicts": 0, "saved": len(saved_to_commit), "not_saved": int(len(other_not_saved_df))},
                        preview["shipment"],
                        preview["original_filename"],
                        preview.get("template_version", ""),
                    )

                    if not update_df.empty:
                        update_result = update_existing_stones_from_import(
                            update_df,
                            preview["import_id"],
                            preview["original_filename"],
                        )
                        st.info(f"Обновлено существующих камней: {update_result['updated']}")

                    st.success("Поставка успешно импортирована.")
                    if "conflict_actions" in st.session_state:
                        del st.session_state["conflict_actions"]
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
    stones = read_stones()
    payments = read_payments()
    if shipments.empty:
        st.info("Поставок пока нет.")
    else:
        summary = shipment_summary_table(shipments, stones, payments)
        st.subheader("Общая сводка")
        f1, f2, f3 = st.columns(3)
        with f1:
            supplier_filter = st.selectbox("Поставщик", ["Все"] + sorted(summary["supplier_name"].dropna().astype(str).unique().tolist()))
        with f2:
            currency_filter = st.selectbox("Валюта", ["Все"] + sorted(summary["currency"].dropna().astype(str).unique().tolist()))
        with f3:
            search_ship = st.text_input("Поиск по номеру / названию поставки")
        filtered_summary = summary.copy()
        if supplier_filter != "Все":
            filtered_summary = filtered_summary[filtered_summary["supplier_name"].astype(str) == supplier_filter]
        if currency_filter != "Все":
            filtered_summary = filtered_summary[filtered_summary["currency"].astype(str) == currency_filter]
        if search_ship:
            mask = filtered_summary["shipment_id"].astype(str).str.contains(search_ship, case=False, na=False) | filtered_summary["shipment_name"].astype(str).str.contains(search_ship, case=False, na=False)
            filtered_summary = filtered_summary[mask]
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Поставок", len(filtered_summary))
        m2.metric("Камней", int(to_num(filtered_summary["stones_total"]).sum()) if not filtered_summary.empty else 0)
        m3.metric("В наличии", int(to_num(filtered_summary["in_stock"]).sum()) if not filtered_summary.empty else 0)
        m4.metric("Продано", int(to_num(filtered_summary["sold"]).sum()) if not filtered_summary.empty else 0)
        m5.metric("Остаток", f"{float(to_num(filtered_summary['balance_due']).sum()) if not filtered_summary.empty else 0:.2f}")
        compact_table(filtered_summary, ["shipment_id", "supplier_id", "supplier_name", "shipment_date", "shipment_name", "currency", "stones_total", "in_stock", "reserved", "sold", "removed", "total_purchase_cost", "paid_total", "balance_due", "comment"], height=320)
        st.divider()
        selected = st.selectbox("Открыть карточку поставки", filtered_summary["shipment_id"].astype(str).tolist() if not filtered_summary.empty else summary["shipment_id"].astype(str).tolist())
        shipment_card(selected, shipments, stones, payments)
        st.divider()
        st.subheader("Опасная команда: удалить поставку полностью")
        st.warning("Удаление уберёт поставку, камни этой поставки, платежи, запись импорта и raw-файлы. Перед удалением будет создан backup.")
        preview = get_shipment_delete_preview(selected)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Камней будет удалено", preview["stones_count"])
        c2.metric("Строк поставки", preview["shipment_rows"])
        c3.metric("Платежей", preview.get("payments_count", 0))
        c4.metric("Raw-папка", "есть" if preview["raw_dir_exists"] else "нет")
        confirm_text = st.text_input(f"Для подтверждения удаления введите номер поставки: {selected}")
        if st.button("Удалить поставку полностью", type="primary", disabled=(confirm_text != selected)):
            result = delete_shipment_completely(selected)
            st.success("Поставка удалена полностью.")
            st.write(result)
            st.rerun()

elif page == "Камни":
    st.title("Камни")
    stones = read_stones()
    if stones.empty:
        st.info("Камней пока нет.")
    else:
        filtered = filter_stones(stones)
        st.caption(f"Найдено камней: {len(filtered)}")

        with st.expander("Сводка ассортимента", expanded=True):
            summary = assortment_summary_table(filtered)
            if summary.empty:
                st.info("Нет данных для сводки.")
            else:
                st.dataframe(summary, use_container_width=True, hide_index=True, height=320)

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
    st.info("Этап 4: Конфликты Report # и повторные загрузки. Изменения правил принимаются только после обсуждения.")
