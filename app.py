import os
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title='KURGIN Admin MVP', page_icon='⚙️', layout='wide')

DATA = Path('data')
DATA.mkdir(exist_ok=True)
STONES = DATA / 'stones.csv'
BATCHES = DATA / 'upload_batches.csv'
ADMIN_PASSWORD = os.getenv('KURGIN_ADMIN_PASSWORD', 'admin123')

STONE_COLS = [
    'stone_id','title','shape','carat','color','clarity','lab','report_number',
    'price_rub','karo_score','tags','current_status','batch_number','upload_date',
    'supplier_name','show_in_catalog','is_mvp_eligible','has_lab_document',
    'physically_received','checked_by_kurgin','upload_confirmed','notes_internal'
]
BATCH_COLS = ['batch_number','upload_date','supplier_name','stones_count','upload_confirmed','notes']

ALIASES = {
    'stone_id':['stone_id','id','sku','report_number','report #'],
    'title':['title','name','description'],
    'shape':['shape','форма','огранка'],
    'carat':['carat','ct','weight','вес','карат'],
    'color':['color','colour','цвет'],
    'clarity':['clarity','чистота'],
    'lab':['lab','laboratory','issuer','лаборатория'],
    'report_number':['report_number','report','report #','certificate_number'],
    'price_rub':['price_rub','price','цена','rub'],
    'karo_score':['karo_score','score','kurgin_score','karo'],
    'tags':['tags','tag','теги','метки','бейджи']
}

def load(path, cols):
    df = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = ''
    return df[cols]

def save(df, path):
    path.parent.mkdir(exist_ok=True)
    df.to_csv(path, index=False)

def next_batch():
    log = load(BATCHES, BATCH_COLS)
    nums = []
    for v in log['batch_number'].astype(str):
        if v.startswith('P-'):
            try:
                nums.append(int(v.split('-')[-1]))
            except Exception:
                pass
    return f'P-{(max(nums)+1 if nums else 1):04d}'

def pick(raw, key):
    lower = {str(c).strip().lower(): c for c in raw.columns}
    for a in ALIASES.get(key, [key]):
        if a.lower() in lower:
            return raw[lower[a.lower()]].reset_index(drop=True)
    return pd.Series([''] * len(raw))

def normalize(raw, batch, dt, supplier, notes):
    out = pd.DataFrame({c: [''] * len(raw) for c in STONE_COLS})
    for c in ['stone_id','title','shape','carat','color','clarity','lab','report_number','price_rub','karo_score','tags']:
        out[c] = pick(raw, c)
    out['current_status'] = 'available'
    out['batch_number'] = batch
    out['upload_date'] = str(dt)
    out['supplier_name'] = supplier
    out['show_in_catalog'] = True
    out['is_mvp_eligible'] = True
    out['has_lab_document'] = True
    out['physically_received'] = True
    out['checked_by_kurgin'] = True
    out['upload_confirmed'] = True
    out['notes_internal'] = notes or 'uploaded_xlsx'
    for c in ['carat','price_rub','karo_score']:
        out[c] = pd.to_numeric(out[c], errors='coerce').fillna(0)
    empty = out['stone_id'].astype(str).str.strip().isin(['','nan','None'])
    out.loc[empty, 'stone_id'] = [f'{batch}-{i+1:04d}' for i in range(empty.sum())]
    empty_title = out['title'].astype(str).str.strip().isin(['','nan','None'])
    out.loc[empty_title, 'title'] = (
        out.loc[empty_title,'shape'].astype(str)+' '+out.loc[empty_title,'carat'].astype(str)+' '+
        out.loc[empty_title,'color'].astype(str)+' '+out.loc[empty_title,'clarity'].astype(str)
    )
    return out[STONE_COLS]

def public(df):
    if df.empty:
        return df
    x = df.copy()
    for c in ['show_in_catalog','is_mvp_eligible','has_lab_document','physically_received','checked_by_kurgin','upload_confirmed']:
        x[c] = x[c].astype(str).str.lower().isin(['true','1','yes','да'])
    return x[x['show_in_catalog'] & x['is_mvp_eligible'] & x['has_lab_document'] & x['physically_received'] & x['checked_by_kurgin'] & x['upload_confirmed'] & x['current_status'].astype(str).str.lower().eq('available')]

def batch_summary(stones, log):
    if stones.empty:
        return pd.DataFrame(columns=['batch_number','upload_date','supplier_name','stones_count'])
    s = stones.groupby('batch_number', dropna=False).size().reset_index(name='stones_count')
    if not log.empty:
        meta = log[['batch_number','upload_date','supplier_name']].drop_duplicates('batch_number', keep='last')
        s = s.merge(meta, on='batch_number', how='left')
    return s

if 'login' not in st.session_state:
    st.session_state.login = False

st.title('KURGIN Admin MVP')
st.caption('Каталог, партии и теги из Excel')

if not st.session_state.login:
    p = st.text_input('Пароль', type='password')
    if st.button('Войти', type='primary'):
        st.session_state.login = (p == ADMIN_PASSWORD)
        st.rerun()
    st.stop()

st.success('Админ-доступ открыт')
if st.button('Выйти'):
    st.session_state.login = False
    st.rerun()

t1,t2,t3,t4 = st.tabs(['Каталог','Загрузка партии','Партии','Публичный preview'])

with t1:
    st.subheader('Каталог камней')
    df = load(STONES, STONE_COLS)
    edited = st.data_editor(df, num_rows='dynamic', use_container_width=True)
    if st.button('Сохранить каталог', type='primary'):
        save(edited, STONES)
        st.success('Каталог сохранён')

with t2:
    st.subheader('Загрузка партии')
    a,b = st.columns(2)
    with a:
        batch = st.text_input('Номер партии', value=next_batch())
        dt = st.date_input('Дата партии', value=date.today())
        supplier = st.text_input('Поставщик')
    with b:
        file = st.file_uploader('Файл камней .xlsx', type=['xlsx'])
    notes = st.text_area('Заметка')
    mode = st.radio('Режим', ['Добавить к текущим','Заменить каталог'], horizontal=True)
    if file is not None:
        raw = pd.read_excel(file)
        st.write('Preview Excel')
        st.dataframe(raw.head(20), use_container_width=True)
        norm = normalize(raw, batch.strip(), dt, supplier.strip(), notes)
        st.write('После нормализации')
        st.dataframe(norm.head(20), use_container_width=True)
        st.info('Колонка tags / теги из Excel сохраняется в каталог без перезаписи.')
        ok = st.checkbox('Подтверждаю загрузку партии')
        if st.button('Сохранить партию', type='primary', disabled=not (ok and batch.strip() and supplier.strip())):
            cur = load(STONES, STONE_COLS)
            res = pd.concat([cur, norm], ignore_index=True) if mode.startswith('Добавить') else norm
            save(res, STONES)
            log = load(BATCHES, BATCH_COLS)
            row = pd.DataFrame([{'batch_number':batch.strip(),'upload_date':str(dt),'supplier_name':supplier.strip(),'stones_count':len(norm),'upload_confirmed':True,'notes':notes}])
            save(pd.concat([log,row], ignore_index=True), BATCHES)
            st.success(f'Партия {batch} сохранена. Камней: {len(norm)}')

with t3:
    st.subheader('Партии')
    stones = load(STONES, STONE_COLS)
    log = load(BATCHES, BATCH_COLS)
    summary = batch_summary(stones, log)
    if summary.empty:
        st.info('Партии пока не загружены')
    else:
        st.dataframe(summary, use_container_width=True)
        selected = st.selectbox('Выбрать партию', summary['batch_number'].astype(str).tolist())
        part = stones[stones['batch_number'].astype(str).eq(selected)]
        st.metric('Камней в выбранной партии', len(part))
        st.dataframe(part, use_container_width=True)

with t4:
    prev = public(load(STONES, STONE_COLS))
    st.subheader('Публичный preview')
    st.dataframe(prev, use_container_width=True)
    st.metric('Публичных камней', len(prev))
