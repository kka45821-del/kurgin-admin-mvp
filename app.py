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
    'stone_id','title','shape','carat','color','clarity','lab','report_number',
    'price_rub','availability_status','internal_status','price_status',
    'karo_score','section_id','tags','show_in_catalog','is_mvp_eligible',
    'has_lab_document','physically_received','checked_by_kurgin',
    'upload_date','supplier_name','supplier_document_name','supplier_document_path','batch_id',
    'upload_confirmed','upload_confirmed_at','notes_internal'
]

LOG_COLUMNS = ['batch_id','upload_date','supplier_name','document_name','document_path','stones_count','upload_confirmed','upload_confirmed_at','notes']

ALIASES = {
    'stone_id': ['stone_id','id','sku','report_number','report #','certificate_number'],
    'title': ['title','name','description'],
    'shape': ['shape','форма','огранка'],
    'carat': ['carat','ct','weight','вес','карат'],
    'color': ['color','colour','цвет'],
    'clarity': ['clarity','чистота'],
    'lab': ['lab','laboratory','issuer','лаборатория'],
    'report_number': ['report_number','report','report #','certificate','certificate_number'],
    'price_rub': ['price_rub','price','цена','rub'],
    'karo_score': ['karo_score','score','kurgin_score','karo'],
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


def save_supplier_document(uploaded_file, batch_id: str) -> tuple[str, str]:
    if uploaded_file is None:
        return '', ''
    safe_name = uploaded_file.name.replace('/', '_').replace('\\', '_')
    path = DOC_DIR / f'{batch_id}__{safe_name}'
    path.write_bytes(uploaded_file.getvalue())
    return safe_name, str(path)


def normalize_excel(raw: pd.DataFrame, upload_date: str, supplier_name: str, doc_name: str, doc_path: str, batch_id: str) -> pd.DataFrame:
    src = raw.copy()
    src.columns = [str(c).strip() for c in src.columns]
    lower = {str(c).strip().lower(): c for c in src.columns}

    def pick(target: str):
        for alias in ALIASES.get(target, [target]):
            if alias.lower() in lower:
                return src[lower[alias.lower()]].reset_index(drop=True)
        return pd.Series([''] * len(src))

    out = pd.DataFrame({
        'stone_id': pick('stone_id'),
        'title': pick('title'),
        'shape': pick('shape'),
        'carat': pick('carat'),
        'color': pick('color'),
        'clarity': pick('clarity'),
        'lab': pick('lab'),
        'report_number': pick('report_number'),
        'price_rub': pick('price_rub'),
        'availability_status': ['available'] * len(src),
        'internal_status': ['available'] * len(src),
        'price_status': ['confirmed'] * len(src),
        'karo_score': pick('karo_score'),
        'section_id': ['main'] * len(src),
        'tags': [''] * len(src),
        'show_in_catalog': [True] * len(src),
        'is_mvp_eligible': [True] * len(src),
        'has_lab_document': [True] * len(src),
        'physically_received': [True] * len(src),
        'checked_by_kurgin': [True] * len(src),
        'upload_date': [upload_date] * len(src),
        'supplier_name': [supplier_name] * len(src),
        'supplier_document_name': [doc_name] * len(src),
        'supplier_document_path': [doc_path] * len(src),
        'batch_id': [batch_id] * len(src),
        'upload_confirmed': [True] * len(src),
        'upload_confirmed_at': [pd.Timestamp.now().isoformat(timespec='seconds')] * len(src),
        'notes_internal': ['uploaded_xlsx_confirmed'] * len(src),
    })

    empty_id = out['stone_id'].astype(str).str.strip().isin(['', 'nan', 'None'])
    out.loc[empty_id, 'stone_id'] = [f'{batch_id}-{i+1:04d}' for i in range(empty_id.sum())]

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


def public_preview(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    x = df.copy()
    bool_cols = ['show_in_catalog','is_mvp_eligible','has_lab_document','physically_received','checked_by_kurgin','upload_confirmed']
    for col in bool_cols:
        x[col] = x[col].astype(str).str.lower().isin(['true','1','yes','да'])
    return x[
        x['show_in_catalog']
        & x['is_mvp_eligible']
        & x['has_lab_document']
        & x['physically_received']
        & x['checked_by_kurgin']
        & x['upload_confirmed']
        & x['availability_status'].astype(str).str.lower().eq('available')
        & x['internal_status'].astype(str).str.lower().eq('available')
        & x['price_status'].astype(str).str.lower().eq('confirmed')
    ]


st.title('KURGIN Admin MVP')
st.caption('Отдельная админка каталога. Публичный сайт не трогаем.')

password = st.text_input('Пароль администратора', type='password')
if password != ADMIN_PASSWORD:
    st.warning('Введите пароль администратора. По умолчанию: admin123')
    st.stop()

st.success('Админ-доступ открыт')
st.warning('Публичный каталог должен показывать только confirmed-upload / eligible / available / confirmed камни.')

tab1, tab2, tab3, tab4 = st.tabs(['Каталог', 'Загрузка .xlsx', 'Публичный preview', 'История загрузок'])

with tab1:
    st.subheader('Каталог камней')
    df = load_stones()
    edited = st.data_editor(df, num_rows='dynamic', use_container_width=True)
    if st.button('Сохранить каталог', type='primary'):
        save_stones(edited)
        st.success('Каталог сохранён')

with tab2:
    st.subheader('Загрузка Excel .xlsx')
    col1, col2 = st.columns(2)
    with col1:
        upload_dt = st.date_input('Дата загрузки / партии', value=date.today())
        supplier_name = st.text_input('Имя поставщика')
    with col2:
        supplier_document = st.file_uploader('Документ поставщика к этой загрузке', type=['pdf','xlsx','xls','docx','png','jpg','jpeg'])
        uploaded = st.file_uploader('Файл камней .xlsx', type=['xlsx'])

    notes = st.text_area('Внутренняя заметка по партии', height=80)
    mode = st.radio('Режим', ['Добавить к текущим', 'Заменить текущий каталог'], horizontal=True)

    if uploaded is not None:
        if not supplier_name.strip():
            st.error('Укажи имя поставщика перед сохранением.')
        try:
            batch_id = f"BATCH-{str(upload_dt).replace('-', '')}-{supplier_name.strip().replace(' ', '_') or 'NO_SUPPLIER'}"
            raw = pd.read_excel(uploaded)
            st.write('Preview Excel')
            st.dataframe(raw.head(20), use_container_width=True)

            st.info('Перед сохранением проверь preview, дату, поставщика и документ. Потом поставь подтверждение.')
            confirm_upload = st.checkbox('Подтверждаю загрузку партии: дата, поставщик, документ и список камней проверены')

            doc_name = supplier_document.name if supplier_document is not None else ''
            normalized = normalize_excel(raw, str(upload_dt), supplier_name.strip(), doc_name, '', batch_id)
            normalized['notes_internal'] = notes or 'uploaded_xlsx_confirmed'

            st.write('После нормализации')
            st.dataframe(normalized.head(20), use_container_width=True)

            can_save = bool(supplier_name.strip()) and confirm_upload
            if st.button('Сохранить подтверждённую загрузку в каталог', type='primary', disabled=not can_save):
                doc_name, doc_path = save_supplier_document(supplier_document, batch_id)
                normalized['supplier_document_name'] = doc_name
                normalized['supplier_document_path'] = doc_path
                normalized['upload_confirmed'] = True
                normalized['upload_confirmed_at'] = pd.Timestamp.now().isoformat(timespec='seconds')

                current = load_stones()
                result = pd.concat([current, normalized], ignore_index=True) if mode == 'Добавить к текущим' else normalized
                save_stones(result)

                log = load_table(UPLOAD_LOG_FILE, LOG_COLUMNS)
                new_log = pd.DataFrame([{
                    'batch_id': batch_id,
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
                st.success(f'Подтверждённая загрузка сохранена. Камней: {len(normalized)}. Всего: {len(result)}')
        except Exception as exc:
            st.error(f'Ошибка загрузки Excel: {exc}')

with tab3:
    st.subheader('Что попадёт в публичный каталог')
    preview = public_preview(load_stones())
    st.dataframe(preview, use_container_width=True)
    st.metric('Публичных камней', len(preview))

with tab4:
    st.subheader('История загрузок')
    log = load_table(UPLOAD_LOG_FILE, LOG_COLUMNS)
    st.dataframe(log, use_container_width=True)
