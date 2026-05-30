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
from admin_log import write_admin_action
from admin_pricing_rules import validate_round_main_large_score
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


def _is_blank(value) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text == "" or text.lower() in {"nan", "none", "null"}


def _infer_section_for_score_gate(row: pd.Series) -> str:
    section = "" if _is_blank(row.get("section")) else str(row.get("section")).strip().lower()
    if section:
        return section

    carat = pd.to_numeric(pd.Series([row.get("carat")]), errors="coerce").fillna(0).iloc[0]
    if 1.0 <= float(carat) < 3.0:
        return "main"
    if float(carat) >= 3.0:
        return "large"
    return ""


def score_gate_errors(normalized: pd.DataFrame) -> pd.DataFrame:
    """Return upload-blocking errors for Round main/large stones without KURGIN Score.

    This gate is stricter than pricing calculation: if any row fails, the whole
    Excel batch must not be saved. When Excel has no section column, section is
    inferred from carat for this gate only: 1.00–2.99 ct = main, 3.00+ ct = large.
    """
    rows = []
    if normalized.empty:
        return pd.DataFrame(rows)

    for idx, row in normalized.iterrows():
        stone = row.to_dict()
        inferred_section = _infer_section_for_score_gate(row)
        if inferred_section:
            stone["section"] = inferred_section

        validation = validate_round_main_large_score(stone)
        if not validation.get("blocked"):
            continue

        rows.append(
            {
                "type": "critical",
                "field": "karo_score",
                "rows": str(idx + 2),
                "count": 1,
                "message": "KURGIN Score обязателен для Round main/large. Загрузка всей партии заблокирована.",
                "stone_id": stone.get("stone_id") or stone.get("id") or "",
                "shape": stone.get("shape", ""),
                "carat": stone.get("carat", ""),
                "section": inferred_section or stone.get("section", ""),
            }
        )
    return pd.DataFrame(rows)


def render_upload_tab(allow_replace: bool = True, show_next_to_pricing: bool = False) -> None:
    st.subheader("Загрузка новой партии")
    st.caption("Единый импорт: KURGIN-шаблон, supplier packing list и результаты KURGIN Score.")
    st.warning(
        "MVP-предупреждение: импорт сейчас автоматически помечает камни как available/show_in_catalog/is_mvp_eligible. "
        "Перед публикацией обязательно проверь Publication Gate и публичный preview."
    )

    st.download_button(
        "Скачать Excel-шаблон каталога",
        data=template_bytes(),
        file_name="KURGIN_catalog_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    batch_number = st.text_input("Номер партии", value=next_batch_number())
    upload_date = st.date_input("Дата партии", value=date.today())
    supplier_name = st.text_input("Поставщик")
    notes = st.text_area("Заметка")

    purchase_total = st.number_input("Общая сумма покупки", min_value=0.0, value=0.0, step=1000.0)
    purchase_advance = st.number_input("Аванс", min_value=0.0, value=0.0, step=1000.0)
    purchase_debt = float(purchase_total or 0) - float(purchase_advance or 0)
    st.metric("Долг", f"{purchase_debt:,.0f} ₽".replace(",", " "))

    uploaded_file = st.file_uploader("Файл камней .xlsx", type=["xlsx"])
    if allow_replace:
        mode = st.radio("Режим", ["Добавить к текущим", "Заменить весь каталог"], horizontal=True)
    else:
        mode = "Добавить к текущим"
        st.info("Безопасный режим Product Management: только добавление к текущему каталогу. Замена всего каталога скрыта.")

    if uploaded_file is None:
        if show_next_to_pricing and st.session_state.get("product_management_last_batch"):
            st.success("Последняя сохранённая партия готова к шагу установки цены.")
            if st.button("Далее", key="product_upload_next_existing"):
                st.session_state["product_management_menu"] = "Установить цену"
                st.session_state["product_management_view"] = "main"
                st.rerun()
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
    st.caption(f"Всего строк на выбранном листе: {len(raw)}. Ниже показаны первые 20 строк для проверки.")
    st.dataframe(raw.head(20), use_container_width=True)

    normalized = normalize_excel(raw, batch_number.strip(), upload_date, supplier_name.strip(), notes)
    st.write("После нормализации")
    st.caption(f"Нормализовано камней: {len(normalized)}. Ниже показаны первые 20 строк; сохранение партии использует все строки.")
    st.dataframe(normalized.head(20), use_container_width=True)

    critical_errors, warnings = validate_catalog(normalized)
    score_errors = score_gate_errors(normalized)
    if not score_errors.empty:
        critical_errors = pd.concat([critical_errors, score_errors], ignore_index=True)

    st.subheader("Проверка загрузки")

    if critical_errors.empty:
        st.success("Критических ошибок не найдено")
    else:
        st.error("Есть критические ошибки. Партию нельзя сохранять, пока они не исправлены.")
        st.dataframe(critical_errors, use_container_width=True)

    if not warnings.empty:
        st.warning("Есть предупреждения. Их можно оставить для текущего этапа, особенно по цене. KURGIN Score обязателен для Round main/large.")
        st.dataframe(warnings, use_container_width=True)

    confirmed = st.checkbox("Подтверждаю загрузку партии и понимаю, что автоматические MVP-флаги нужно проверить перед публикацией")
    can_save = confirmed and critical_errors.empty and bool(batch_number.strip()) and bool(supplier_name.strip())

    if st.button("Сохранить партию", type="primary", disabled=not can_save):
        current = load_stones()
        result = pd.concat([current, normalized], ignore_index=True) if mode.startswith("Добавить") else normalized
        save_stones(result)
        upsert_batch_log(
            batch_number.strip(),
            upload_date,
            supplier_name.strip(),
            len(normalized),
            notes,
            purchase_total_rub=purchase_total,
            purchase_advance_rub=purchase_advance,
        )
        write_admin_action(
            action="import_excel_batch",
            entity=str(batch_number).strip(),
            rows_count=len(normalized),
            source="admin_upload",
            details=f"Поставщик: {supplier_name}; лист: {selected_sheet}; режим: {mode}; purchase_total_rub={purchase_total}; purchase_advance_rub={purchase_advance}; purchase_debt_rub={purchase_debt}",
        )
        st.session_state["product_management_last_batch"] = {
            "batch_number": str(batch_number).strip(),
            "upload_date": str(upload_date),
            "supplier_name": str(supplier_name).strip(),
            "notes": notes,
            "stones_count": int(len(normalized)),
            "purchase_total_rub": float(purchase_total or 0),
            "purchase_advance_rub": float(purchase_advance or 0),
            "purchase_debt_rub": float(purchase_debt or 0),
        }
        st.success(f"Партия {batch_number} сохранена. Камней: {len(normalized)}")

    if show_next_to_pricing and st.session_state.get("product_management_last_batch"):
        if st.button("Далее", key="product_upload_next_to_pricing"):
            st.session_state["product_management_menu"] = "Установить цену"
            st.session_state["product_management_view"] = "main"
            st.rerun()
