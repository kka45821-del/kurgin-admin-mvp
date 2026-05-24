import os
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title='KURGIN Admin MVP', page_icon='⚙️', layout='wide')

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
STONES_FILE = DATA_DIR / 'stones.csv'
ADMIN_PASSWORD = os.getenv('KURGIN_ADMIN_PASSWORD', 'admin123')

COLUMNS = [
    'stone_id','title','shape','carat','color','clarity','lab','report_number',
    'price_rub','availability_status','internal_status','price_status',
    'karo_score','section_id','tags','show_in_catalog','is_mvp_eligible',
    'has_lab_document','physically_received','checked_by_kurgin','notes_internal'
]

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


def load_stones() -> pd.DataFrame:
    if STONES_FILE.exists():
        df = pd.read_csv(STONES_FILE)
    else:
        df = pd.DataFrame(columns=COLUMNS)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ''
    return df[COLUMNS]


def save_stones(df: pd.DataFrame) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(STONES_FILE, index=False)


def normalize_excel(raw: pd.DataFrame) -> pd.DataFrame:
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
        'notes_internal': ['uploaded_xlsx'] * len(src),
    })

    empty_id = out['stone_id'].astype(str).str.strip().isin(['', 'nan', 'None'])
    out.loc[empty_id, 'stone_id'] = [f'KRG-UP-{i+1:04d}' for i in range(empty_id.sum())]

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
    bool_cols = ['show_in_catalog','is_mvp_eligible','has_lab_document','physically_received','checked_by_kurgin']
    for col in bool_cols:
        x[col] = x[col].astype(str).str.lower().isin(['true','1','yes','да'])
    return x[
        x['show_in_catalog']
        & x['is_mvp_eligible']
        & x['has_lab_document']
        & x['physically_received']
        & x['checked_by_kurgin']
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
st.warning('Публичный каталог должен показывать только eligible / available / confirmed камни.')

tab1, tab2, tab3 = st.tabs(['Каталог', 'Загрузка .xlsx', 'Публичный preview'])

with tab1:
    st.subheader('Каталог камней')
    df = load_stones()
    edited = st.data_editor(df, num_rows='dynamic', use_container_width=True)
    if st.button('Сохранить каталог', type='primary'):
        save_stones(edited)
        st.success('Каталог сохранён')

with tab2:
    st.subheader('Загрузка Excel .xlsx')
    uploaded = st.file_uploader('Файл .xlsx', type=['xlsx'])
    mode = st.radio('Режим', ['Добавить к текущим', 'Заменить текущий каталог'], horizontal=True)
    if uploaded is not None:
        try:
            raw = pd.read_excel(uploaded)
            st.write('Preview Excel')
            st.dataframe(raw.head(20), use_container_width=True)
            normalized = normalize_excel(raw)
            st.write('После нормализации')
            st.dataframe(normalized.head(20), use_container_width=True)
            if st.button('Сохранить .xlsx в каталог', type='primary'):
                current = load_stones()
                result = pd.concat([current, normalized], ignore_index=True) if mode == 'Добавить к текущим' else normalized
                save_stones(result)
                st.success(f'Сохранено камней: {len(normalized)}. Всего: {len(result)}')
        except Exception as exc:
            st.error(f'Ошибка загрузки Excel: {exc}')

with tab3:
    st.subheader('Что попадёт в публичный каталог')
    preview = public_preview(load_stones())
    st.dataframe(preview, use_container_width=True)
    st.metric('Публичных камней', len(preview))
