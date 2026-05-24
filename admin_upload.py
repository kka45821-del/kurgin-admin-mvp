from datetime import date

import pandas as pd
import streamlit as st

from admin_io import ALIASES, key_name, load_stones, next_batch_number, normalize_excel, save_stones, upsert_batch_log


def detected_mapping(raw: pd.DataFrame) -> pd.DataFrame:
    normalized_columns = {key_name(col): col for col in raw.columns}
    rows = []
    for target, aliases in ALIASES.items():
        found = ''
        for alias in aliases:
            if key_name(alias) in normalized_columns:
                found = str(normalized_columns[key_name(alias)])
                break
        rows.append({'поле KURGIN': target, 'найденная колонка Excel': found})
    return pd.DataFrame(rows)


def render_upload_tab() -> None:
    st.subheader('Загрузка новой партии')

    batch_number = st.text_input('Номер партии', value=next_batch_number())
    upload_date = st.date_input('Дата партии', value=date.today())
    supplier_name = st.text_input('Поставщик')
    uploaded_file = st.file_uploader('Файл камней .xlsx', type=['xlsx'])
    notes = st.text_area('Заметка')
    mode = st.radio('Режим', ['Добавить к текущим', 'Заменить весь каталог'], horizontal=True)

    if uploaded_file is None:
        return

    xls = pd.ExcelFile(uploaded_file)
    st.write('Листы в Excel')
    st.code('\n'.join(xls.sheet_names))

    default_index = xls.sheet_names.index('All Data') if 'All Data' in xls.sheet_names else 0
    selected_sheet = st.selectbox('Какой лист загружать как каталог камней', xls.sheet_names, index=default_index)

    sheet_rows = []
    for sheet in xls.sheet_names:
        preview = pd.read_excel(xls, sheet_name=sheet, nrows=5)
        sheet_rows.append({
            'лист': sheet,
            'строк preview': len(preview),
            'колонок': len(preview.columns),
            'первые колонки': ', '.join([str(c) for c in preview.columns[:12]]),
        })
    st.write('Диагностика листов')
    st.dataframe(pd.DataFrame(sheet_rows), use_container_width=True)

    raw = pd.read_excel(xls, sheet_name=selected_sheet)
    st.write('Колонки выбранного листа')
    st.code('\n'.join([str(c) for c in raw.columns]))

    st.write('Распознавание колонок')
    st.dataframe(detected_mapping(raw), use_container_width=True)

    st.write('Preview Excel')
    st.dataframe(raw.head(20), use_container_width=True)

    normalized = normalize_excel(raw, batch_number.strip(), upload_date, supplier_name.strip(), notes)
    st.write('После нормализации')
    st.dataframe(normalized.head(20), use_container_width=True)

    confirmed = st.checkbox('Подтверждаю загрузку партии')
    can_save = confirmed and bool(batch_number.strip()) and bool(supplier_name.strip())

    if st.button('Сохранить партию', type='primary', disabled=not can_save):
        current = load_stones()
        result = pd.concat([current, normalized], ignore_index=True) if mode.startswith('Добавить') else normalized
        save_stones(result)
        upsert_batch_log(batch_number.strip(), upload_date, supplier_name.strip(), len(normalized), notes)
        st.success(f'Партия {batch_number} сохранена. Камней: {len(normalized)}')
