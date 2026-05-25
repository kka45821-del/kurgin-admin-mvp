from datetime import date
from io import BytesIO

import pandas as pd
import streamlit as st

from admin_io import (
    ALIASES,
    STONE_COLS,
    key_name,
    load_stones,
    next_batch_number,
    normalize_excel,
    save_stones,
    upsert_batch_log,
)
from admin_validation import validate_catalog


TEMPLATE_RULES = [
    {"section": "main", "required": "carat, color, clarity, report_number, KURGIN Score for Round", "warning": "price, measurements, fluorescence"},
    {"section": "large", "required": "carat, color, clarity, report_number, KURGIN Score for Round", "warning": "price, measurements, fluorescence"},
    {"section": "small", "required": "size_mm or carat, quantity", "warning": "price, report_number, KURGIN Score"},
    {"section": "colored", "required": "size_mm or carat, color_type", "warning": "price, report_number, KURGIN Score"},
    {"section": "pairs", "required": "size_mm or carat, quantity, pair_id", "warning": "price, report_number, KURGIN Score"},
    {"section": "side", "required": "size_mm or carat, quantity, side_type", "warning": "price, report_number, KURGIN Score"},
]


def template_bytes() -> bytes:
    out = BytesIO()
    example = {col: "" for col in STONE_COLS}
    example.update(
        {
            "stone_id": "KRG-001",
            "shape": "Round",
            "carat": 1.25,
            "color": "F",
            "clarity": "VS1",
            "lab": "IGI",
            "report_number": "LG000000",
            "karo_score": 92,
            "section": "main",
            "cut": "EX",
            "polish": "EX",
            "symmetry": "VG",
            "fluorescence": "none",
            "measurements": "6.85x6.88x4.20",
            "quantity": 1,
            "current_status": "available",
            "show_in_catalog": True,
            "is_mvp_eligible": True,
            "has_lab_document": True,
            "physically_received": True,
            "checked_by_kurgin": True,
            "upload_confirmed": True,
        }
    )
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        pd.DataFrame([example], columns=STONE_COLS).to_excel(writer, sheet_name="KURGIN_Template", index=False)
        pd.DataFrame(columns=STONE_COLS).to_excel(writer, sheet_name="Empty_Template", index=False)
        pd.DataFrame(TEMPLATE_RULES).to_excel(writer, sheet_name="Rules", index=False)
    return out.getvalue()


def alias_key_set() -> set[str]:
    values = set()
    for target, aliases in ALIASES.items():
        values.add(key_name(target))
        for alias in aliases:
            values.add(key_name(alias))
    return values


def find_target_for_column(column) -> str:
    normalized = key_name(column)
    for target, aliases in ALIASES.items():
        if normalized == key_name(target):
            return target
        for alias in aliases:
            if normalized == key_name(alias):
                return target
    return ""


def detected_mapping(raw: pd.DataFrame) -> pd.DataFrame:
    normalized_columns = {key_name(col): col for col in raw.columns}
    rows = []
    for target, aliases in ALIASES.items():
        found = ""
        for alias in [target] + aliases:
            if key_name(alias) in normalized_columns:
                found = str(normalized_columns[key_name(alias)])
                break
        rows.append({"поле KURGIN": target, "найденная колонка Excel": found})
    return pd.DataFrame(rows)


def column_control(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for col in raw.columns:
        target = find_target_for_column(col)
        rows.append(
            {
                "Excel column": str(col),
                "normalized": key_name(col),
                "KURGIN field": target,
                "recognized": bool(target),
            }
        )
    report = pd.DataFrame(rows)
    return report[report["recognized"]].copy(), report[~report["recognized"]].copy()


def detect_header_row(sheet_raw: pd.DataFrame) -> int | None:
    known = alias_key_set()
    best_idx = None
    best_hits = 0
    for idx, row in sheet_raw.head(80).iterrows():
        hits = sum(1 for value in row.tolist() if key_name(value) in known)
        if hits > best_hits:
            best_idx = idx
            best_hits = hits
    return best_idx if best_hits >= 4 else None


def read_sheet_smart(xls: pd.ExcelFile, sheet_name: str) -> tuple[pd.DataFrame, int | None]:
    raw_probe = pd.read_excel(xls, sheet_name=sheet_name, header=None)
    header_row = detect_header_row(raw_probe)
    if header_row is None:
        data = pd.read_excel(xls, sheet_name=sheet_name)
    else:
        data = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)
    data = data.dropna(how="all").dropna(axis=1, how="all")
    return data, header_row


def sheet_diagnostics(xls: pd.ExcelFile) -> pd.DataFrame:
    rows = []
    known = alias_key_set()
    for sheet in xls.sheet_names:
        probe = pd.read_excel(xls, sheet_name=sheet, header=None, nrows=40)
        header_row = detect_header_row(probe)
        if header_row is None:
            preview = pd.read_excel(xls, sheet_name=sheet, nrows=5)
            first_columns = ", ".join([str(c) for c in preview.columns[:12]])
            hits = 0
        else:
            header_values = [str(v) for v in probe.iloc[header_row].dropna().tolist()]
            first_columns = ", ".join(header_values[:12])
            hits = sum(1 for value in header_values if key_name(value) in known)
        rows.append(
            {
                "лист": sheet,
                "строка заголовков": "" if header_row is None else int(header_row) + 1,
                "распознано колонок": hits,
                "первые колонки": first_columns,
            }
        )
    return pd.DataFrame(rows)


def render_upload_tab() -> None:
    st.subheader("Загрузка новой партии")
    st.caption("Единый импорт: KURGIN-шаблон, supplier packing list и результаты KURGIN Score.")

    st.download_button(
        "Скачать Excel-шаблон каталога",
        data=template_bytes(),
        file_name="KURGIN_catalog_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    batch_number = st.text_input("Номер партии", value=next_batch_number())
    upload_date = st.date_input("Дата партии", value=date.today())
    supplier_name = st.text_input("Поставщик")
    uploaded_file = st.file_uploader("Файл камней .xlsx", type=["xlsx"])
    notes = st.text_area("Заметка")
    mode = st.radio("Режим", ["Добавить к текущим", "Заменить весь каталог"], horizontal=True)

    if uploaded_file is None:
        return

    xls = pd.ExcelFile(uploaded_file)

    st.write("Диагностика листов")
    diagnostics = sheet_diagnostics(xls)
    st.dataframe(diagnostics, use_container_width=True)

    preferred = ["All Data", "PACKING LIST LG", "KURGIN_Template", "Empty_Template"]
    default_index = 0
    for name in preferred:
        if name in xls.sheet_names:
            default_index = xls.sheet_names.index(name)
            break

    selected_sheet = st.selectbox("Какой лист загружать как каталог камней", xls.sheet_names, index=default_index)

    raw, header_row = read_sheet_smart(xls, selected_sheet)

    if header_row is not None:
        st.success(f"Строка заголовков найдена: {header_row + 1}")
    else:
        st.info("Строка заголовков не определялась отдельно. Используется первая строка листа.")

    recognized, unrecognized = column_control(raw)
    col_a, col_b = st.columns(2)
    col_a.metric("Распознано колонок", len(recognized))
    col_b.metric("Не распознано колонок", len(unrecognized))

    if not unrecognized.empty:
        st.warning("Есть нераспознанные колонки. Проверь, не потерялись ли важные данные.")
        st.dataframe(unrecognized[["Excel column", "normalized"]], use_container_width=True)

    with st.expander("Распознанные колонки", expanded=False):
        st.dataframe(recognized[["Excel column", "KURGIN field"]], use_container_width=True)

    st.write("Распознавание полей KURGIN")
    st.dataframe(detected_mapping(raw), use_container_width=True)

    st.write("Preview Excel")
    st.dataframe(raw.head(20), use_container_width=True)

    normalized = normalize_excel(raw, batch_number.strip(), upload_date, supplier_name.strip(), notes)
    st.write("После нормализации")
    st.dataframe(normalized.head(20), use_container_width=True)

    critical_errors, warnings = validate_catalog(normalized)
    st.subheader("Проверка загрузки")

    if critical_errors.empty:
        st.success("Критических ошибок не найдено")
    else:
        st.error("Есть критические ошибки. Партию нельзя сохранять, пока они не исправлены.")
        st.dataframe(critical_errors, use_container_width=True)

    if not warnings.empty:
        st.warning("Есть предупреждения. Их можно оставить для текущего этапа, особенно по цене и KURGIN Score.")
        st.dataframe(warnings, use_container_width=True)

    confirmed = st.checkbox("Подтверждаю загрузку партии")
    can_save = confirmed and critical_errors.empty and bool(batch_number.strip()) and bool(supplier_name.strip())

    if st.button("Сохранить партию", type="primary", disabled=not can_save):
        current = load_stones()
        result = pd.concat([current, normalized], ignore_index=True) if mode.startswith("Добавить") else normalized
        save_stones(result)
        upsert_batch_log(batch_number.strip(), upload_date, supplier_name.strip(), len(normalized), notes)
        st.success(f"Партия {batch_number} сохранена. Камней: {len(normalized)}")
