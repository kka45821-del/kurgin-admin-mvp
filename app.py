import os
from datetime import date
import pandas as pd
import streamlit as st
from admin_io import ALIASES, key_name, load_stones, save_stones, next_batch_number, normalize_excel, public_preview, upsert_batch_log
from admin_batches import render_batches_tab
from admin_publish import render_publish_tab
from admin_validation import validate_catalog

st.set_page_config(page_title='KURGIN Admin MVP', page_icon='⚙️', layout='wide')
ADMIN_PASSWORD = os.getenv('KURGIN_ADMIN_PASSWORD', 'admin123')

if 'login' not in st.session_state:
    st.session_state.login = False

st.title('KURGIN Admin MVP')
st.caption('Каталог, партии, tag1-tag6. Публичный сайт не трогаем.')

if not st.session_state.login:
    password = st.text_input('Пароль', type='password')
    if st.button('Войти', type='primary'):
        st.session_state.login = password == ADMIN_PASSWORD
        st.rerun()
    st.stop()

if st.button('Выйти'):
    st.session_state.login = False
    st.rerun()

tab_catalog, tab_upload, tab_batches, tab_preview, tab_publish = st.tabs(['Каталог', 'Загрузка партии', 'Партии', 'Публичный preview', 'Публикация'])

with tab_catalog:
    st.subheader('Каталог камней')
    df = load_stones()
    edited = st.data_editor(df, num_rows='dynamic', use_container_width=True)
    if st.button('Сохранить каталог', type='primary'):
        save_stones(edited)
        st.success('Каталог сохранён')

with tab_upload:
    st.subheader('Загрузка новой партии')
    batch_number = st.text_input('Номер партии', value=next_batch_number())
    upload_date = st.date_input('Дата партии', value=date.today())
    supplier_name = st.text_input('Поставщик')
    uploaded_file = st.file_uploader('Файл камней .xlsx', type=['xlsx'])
    notes = st.text_area('Заметка')
    mode = st.radio('Режим', ['Добавить к текущим', 'Заменить весь каталог'], horizontal=True)

    if uploaded_file is not None:
        raw = pd.read_excel(uploaded_file)
        st.write('Колонки в Excel')
        st.code('\n'.join([str(c) for c in raw.columns]))
        normalized_columns = {key_name(col): col for col in raw.columns}
        mapping_rows = []
        for target, aliases in ALIASES.items():
            found = ''
            for alias in aliases:
                if key_name(alias) in normalized_columns:
                    found = str(normalized_columns[key_name(alias)])
                    break
            mapping_rows.append({'поле KURGIN': target, 'найденная колонка Excel': found})
        st.write('Распознавание колонок')
        st.dataframe(pd.DataFrame(mapping_rows), use_container_width=True)
        st.write('Preview Excel')
        st.dataframe(raw.head(20), use_container_width=True)
        normalized = normalize_excel(raw, batch_number.strip(), upload_date, supplier_name.strip(), notes)
        st.write('После нормализации')
        st.dataframe(normalized.head(20), use_container_width=True)

        critical_errors, warnings = validate_catalog(normalized)
        st.subheader('Проверка загрузки')
        if critical_errors.empty:
            st.success('Критических ошибок не найдено')
        else:
            st.error('Есть критические ошибки. Партию нельзя сохранять, пока они не исправлены.')
            st.dataframe(critical_errors, use_container_width=True)
        if not warnings.empty:
            st.warning('Есть предупреждения. Их можно оставить для текущего этапа, особенно по цене и Karo Score.')
            st.dataframe(warnings, use_container_width=True)

        confirmed = st.checkbox('Подтверждаю загрузку партии')
        can_save = confirmed and critical_errors.empty and bool(batch_number.strip()) and bool(supplier_name.strip())
        if st.button('Сохранить партию', type='primary', disabled=not can_save):
            current = load_stones()
            result = pd.concat([current, normalized], ignore_index=True) if mode.startswith('Добавить') else normalized
            save_stones(result)
            upsert_batch_log(batch_number.strip(), upload_date, supplier_name.strip(), len(normalized), notes)
            st.success(f'Партия {batch_number} сохранена. Камней: {len(normalized)}')

with tab_batches:
    render_batches_tab()

with tab_preview:
    st.subheader('Публичный preview')
    preview = public_preview(load_stones())
    st.dataframe(preview, use_container_width=True)
    st.metric('Публичных камней', len(preview))

with tab_publish:
    render_publish_tab()