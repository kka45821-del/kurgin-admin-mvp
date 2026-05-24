import os
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title='KURGIN Admin MVP', page_icon='⚙️', layout='wide')

DATA_DIR = Path('data')
DOC_DIR = DATA_DIR / 'supplier_documents'
DATA_DIR.mkdir(exist_ok=True)
DOC_DIR.mkdir(exist_ok=True)
STONES_FILE = DATA_DIR / 'stones.csv'
UPLOAD_LOG_FILE = DATA_DIR / 'upload_batches.csv'
ADMIN_PASSWORD = os.getenv('KURGIN_ADMIN_PASSWORD', 'admin123')

COLUMNS = [
    'stone_id', 'title', 'shape', 'carat', 'color', 'clarity', 'lab', 'report_number',
    'price_rub', 'availability_status', 'internal_status', 'price_status', 'karo_score',
    'section_id', 'tags', 'show_in_catalog', 'is_mvp_eligible', 'has_lab_document',
    'physically_received', 'checked_by_kurgin', 'batch_number', 'upload_date',
    'supplier_name', 'supplier_document_name', 'supplier_document_path',
    'upload_confirmed', 'upload_confirmed_at', 'notes_internal'
]

LOG_COLUMNS = [
    'batch_number', 'upload_date', 'supplier_name', 'document_name', 'document_path',
    'stones_count', 'upload_confirmed', 'upload_confirmed_at', 'notes'
]

ALIASES = {
    'stone_id': ['stone_id', 'id', 'sku', 'report_number', 'report #', 'certificate_number'],
    'title': ['title', 'name', 'description'],
    'shape': ['shape', 'форма', 'огранка'],
    'carat': ['carat', 'ct', 'weight', 'вес', 'карат'],
    'color': ['color', 'colour', 'цвет'],
    'clarity': ['clarity', 'чистота'],
    'lab': ['lab', 'laboratory', 'issuer', 'лаборатория'],
    'report_number': ['report_number', 'report', 'report #', 'certificate', 'certificate_number'],
    'price_rub': ['price_rub', 'price', 'цена', 'rub'],
    'karo_score': ['karo_score', 'score', 'kurgin_score', 'karo'],
}


def load_table(path: Path, columns: list[str]) -> pd.DataFrame:
    if path.exists():
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(columns=columns)
    for col in columns:
        if col not in df.columns:
            df[col] = ''
    return df[columns]


def save_table(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(exist_ok=True)
    df.to_csv(path, index=False)


def load_stones() -> pd.DataFrame:
    return load_table(STONES_FILE, COLUMNS)


def save_stones(df: pd.DataFrame) -> None:
    save_table(df, STONES_FILE)


def next_batch_number() -> str:
    log = load_table(UPLOAD_LOG_FILE, LOG_COLUMNS)
    nums = []
    for value in log['batch_number'].astype(str):
        if value.startswith('P-'):
            try:
                nums.append(int(value.split('-')[-1]))
            except Exception:
                pass
    return f'P-{(max(nums) + 1 if nums else 1):04d}'


def save_supplier_document(uploaded_file, batch_number: str) -> tuple[str, str]:
    if uploaded_file is None:
        return '', ''
    safe_name = uploaded_file.name.replace('/', '_').replace('\\', '_')
    path = DOC_DIR / f'{batch_number}__{safe_name}'
    path.write_bytes(uploaded_file.getvalue())
    return safe_name, str(path)


def pick_column(raw: pd.DataFrame, target: str) -> pd.Series:
    lower = {str(c).strip().lower(): c for c in raw.columns}
    for alias in ALIASES.get(target, [target]):
        if alias.lower() in lower:
            return raw[lower[alias.lower()]].reset_index(drop=True)
    return pd.Series([''] * len(raw))


def normalize_excel(raw, upload_date, supplier_name, doc_name, doc_path, batch_number, notes):
    out = pd.DataFrame({
        'stone_id': pick_column(raw, 'stone_id'),
        'title': pick_column(raw, 'title'),
        'shape': pick_column(raw, 'shape'),
        'carat': pick_column(raw, 'carat'),
        'color': pick_column(raw, 'color'),
        'clarity': pick_column(raw, 'clarity'),
        'lab': pick_column(raw, 'lab'),
        'report_number': pick_column(raw, 'report_number'),
        'price_rub': pick_column(raw, 'price_rub'),
        'availability_status': ['available'] * len(raw),
        'internal_status': ['available'] * len(raw),
        'price_status': ['confirmed'] * len(raw),
        'karo_score': pick_column(raw, 'karo_score'),
        'section_id': ['main'] * len(raw),
        'tags': [''] * len(raw),
        'show_in_catalog': [True] * len(raw),
        'is_mvp_eligible': [True] * len(raw),
        'has_lab_document': [True] * len(raw),
        'physically_received': [True] * len(raw),
        'checked_by_kurgin': [True] * len(raw),
        'batch_number': [batch_number] * len(raw),
        'upload_date': [str(upload_date)] * len(raw),
        'supplier_name': [supplier_name] * len(raw),
        'supplier_document_name': [doc_name] * len(raw),
        'supplier_document_path': [doc_path] * len(raw),
        'upload_confirmed': [True] * len(raw),
        'upload_confirmed_at': [pd.Timestamp.now().isoformat(timespec='seconds')] * len(raw),
        'notes_internal': [notes or 'uploaded_xlsx_confirmed'] * len(raw),
    })

    empty_id = out['stone_id'].astype(str).str.strip().isin(['', 'nan', 'None'])
    out.loc[empty_id, 'stone_id'] = [f'{batch_number}-{i+1:04d}' for i in range(empty_id.sum())]

    empty_title = out['title'].astype(str).str.strip().isin(['', 'nan', 'None'])
    out.loc[empty_title, 'title'] = (
        out.loc[empty_title, 'shape'].astype(str) + ' '
        + out.loc[empty_title, 'carat'].astype(str) + ' '
        + out.loc[empty_title, 'color'].astype(str) + ' '
        + out.loc[empty_title, 'clarity'].astype(str)
    )

    for col in ['carat', 'price_rub', 'karo_score']:
        out[col] = pd.to_numeric(out[col], errors='coerce').fillna(0)
    return out[COLUMNS]


def public_preview(df):
    if df.empty:
        return df
    x = df.copy()
    for col in ['show_in_catalog', 'is_mvp_eligible', 'has_lab_document', 'physically_received', 'checked_by_kurgin', 'upload_confirmed']:
        x[col] = x[col].astype(str).str.lower().isin(['true', '1', 'yes', 'да'])
    return x[
        x['show_in_catalog'] & x['is_mvp_eligible'] & x['has_lab_document']
        & x['physically_received'] & x['checked_by_kurgin'] & x['upload_confirmed']
        & x['availability_status'].astype(str).str.lower().eq('available')
        & x['internal_status'].astype(str).str.lower().eq('available')
        & x['price_status'].astype(str).str.lower().eq('confirmed')
    ]


if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

st.title('KURGIN Admin MVP')
st.caption('Отдельная админка каталога. Документы пока нужны только внутри админки.')

if not st.session_state.admin_logged_in:
    password = st.text_input('Пароль администратора', type='password')
    if st.button('Войти', type='primary'):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.rerun()
        else:
            st.error('Неверный пароль')
    st.stop()

c1, c2 = st.columns([5, 1])
with c1:
    st.success('Админ-доступ открыт')
with c2:
    if st.button('Выйти', use_container_width=True):
        st.session_state.admin_logged_in = False
        st.rerun()

st.warning('Каждый камень получает batch_number. Так видно, из какой партии он пришёл.')

tab1, tab2, tab3, tab4 = st.tabs(['Каталог', 'Загрузка партии .xlsx', 'Публичный preview', 'История партий'])

with tab1:
    st.subheader('Каталог камней')
    df = load_stones()
    edited = st.data_editor(df, num_rows='dynamic', use_container_width=True)
    if st.button('Сохранить каталог', type='primary'):
        save_stones(edited)
        st.success('Каталог сохранён')

with tab2:
    st.subheader('Загрузка партии')
    left, right = st.columns(2)
    with left:
        batch_number = st.text_input('Номер партии', value=next_batch_number())
        upload_dt = st.date_input('Дата партии', value=date.today())
        supplier_name = st.text_input('Имя поставщика')
    with right:
        supplier_document = st.file_uploader('Документ партии', type=['pdf', 'xlsx', 'xls', 'docx', 'png', 'jpg', 'jpeg'])
        uploaded = st.file_uploader('Файл камней .xlsx', type=['xlsx'])

    notes = st.text_area('Внутренняя заметка по партии', height=80)
    mode = st.radio('Режим', ['Добавить к текущим', 'Заменить текущий каталог'], horizontal=True)

    if uploaded is not None:
        try:
            raw = pd.read_excel(uploaded)
            st.write('Preview Excel')
            st.dataframe(raw.head(20), use_container_width=True)

            doc_name = supplier_document.name if supplier_document else ''
            normalized = normalize_excel(raw, upload_dt, supplier_name.strip(), doc_name, '', batch_number.strip(), notes)
            st.write('После нормализации')
            st.dataframe(normalized.head(20), use_container_width=True)

            confirm_upload = st.checkbox('Подтверждаю загрузку: номер партии, дата, поставщик, документ и список камней проверены')
            can_save = bool(batch_number.strip()) and bool(supplier_name.strip()) and confirm_upload
            if st.button('Сохранить подтверждённую партию', type='primary', disabled=not can_save):
                doc_name, doc_path = save_supplier_document(supplier_document, batch_number.strip())
                normalized = normalize_excel(raw, upload_dt, supplier_name.strip(), doc_name, doc_path, batch_number.strip(), notes)
                current = load_stones()
                result = pd.concat([current, normalized], ignore_index=True) if mode == 'Добавить к текущим' else normalized
                save_stones(result)

                log = load_table(UPLOAD_LOG_FILE, LOG_COLUMNS)
                new_log = pd.DataFrame([{
                    'batch_number': batch_number.strip(),
                    'upload_date': str(upload_dt),
                    'supplier_name': supplier_name.strip(),
                    'document_name': doc_name,
                    'document_path': doc_path,
                    'stones_count': len(normalized),
                    'upload_confirmed': True,
                    'upload_confirmed_at': pd.Timestamp.now().isoformat(timespec='seconds'),
                    'notes': notes,
                }])
                save_table(pd.concat([log, new_log], ignore_index=True), UPLOAD_LOG_FILE)
                st.success(f'Партия {batch_number} сохранена. Камней: {len(normalized)}')
        except Exception as exc:
            st.error(f'Ошибка загрузки Excel: {exc}')

with tab3:
    st.subheader('Что попадёт в публичный каталог')
    preview = public_preview(load_stones())
    st.dataframe(preview, use_container_width=True)
    st.metric('Публичных камней', len(preview))

with tab4:
    st.subheader('История партий')
    log = load_table(UPLOAD_LOG_FILE, LOG_COLUMNS)
    st.dataframe(log, use_container_width=True)
