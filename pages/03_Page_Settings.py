import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title='KURGIN Page Settings', page_icon='⚙️', layout='wide')

DATA = Path('data')
DATA.mkdir(exist_ok=True)
FILE = DATA / 'page_settings.json'
ADMIN_PASSWORD = os.getenv('KURGIN_ADMIN_PASSWORD', 'admin123')

PAGES = [
    ('home', 'KURGIN / Главная'),
    ('tools', 'Инструменты'),
    ('catalog', 'Каталог'),
    ('favorites', 'Избранное'),
    ('cart', 'Корзина'),
    ('profile', 'Профиль'),
]

def default_settings():
    return {
        'pages': {k: {'visible': True, 'title': v, 'subtitle': '', 'text': '', 'cta': ''} for k, v in PAGES},
        'catalog_sections': [
            {'key': 'main', 'label': 'Основной каталог', 'visible': True, 'order': 10},
            {'key': 'small', 'label': 'Мелкие', 'visible': False, 'order': 20},
            {'key': 'large', 'label': 'Крупные', 'visible': False, 'order': 30},
            {'key': 'exclusive', 'label': 'Эксклюзив', 'visible': False, 'order': 40},
        ],
        'catalog_filters': [
            {'key': 'shape', 'label': 'Форма', 'visible': True, 'order': 10},
            {'key': 'carat', 'label': 'Вес', 'visible': True, 'order': 20},
            {'key': 'color', 'label': 'Цвет', 'visible': True, 'order': 30},
            {'key': 'clarity', 'label': 'Чистота', 'visible': True, 'order': 40},
            {'key': 'karo_score', 'label': 'Karo Score', 'visible': True, 'order': 50},
            {'key': 'price_rub', 'label': 'Цена', 'visible': True, 'order': 60},
        ],
        'catalog_sorts': [
            {'key': 'karo_desc', 'label': 'по Karo Score ↓', 'visible': True, 'default': True, 'order': 10},
            {'key': 'price_asc', 'label': 'по цене ↑', 'visible': True, 'default': False, 'order': 20},
            {'key': 'price_desc', 'label': 'по цене ↓', 'visible': True, 'default': False, 'order': 30},
            {'key': 'carat_asc', 'label': 'по весу ↑', 'visible': True, 'default': False, 'order': 40},
            {'key': 'carat_desc', 'label': 'по весу ↓', 'visible': True, 'default': False, 'order': 50},
        ],
    }

def load_settings():
    if FILE.exists():
        with FILE.open('r', encoding='utf-8') as f:
            data = json.load(f)
        base = default_settings()
        for k, v in base.items():
            data.setdefault(k, v)
        return data
    return default_settings()

def save_settings(data):
    with FILE.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

st.title('KURGIN Page Settings')
st.caption('Редактирование слов, видимости страниц, фильтров, сортировок и разделов каталога. Публичный сайт пока не меняем.')

if 'page_settings_login' not in st.session_state:
    st.session_state.page_settings_login = False
if not st.session_state.page_settings_login:
    p = st.text_input('Пароль', type='password')
    if st.button('Войти', type='primary'):
        st.session_state.page_settings_login = p == ADMIN_PASSWORD
        st.rerun()
    st.stop()

settings = load_settings()
tabs = st.tabs([label for _, label in PAGES])

for tab, (key, label) in zip(tabs, PAGES):
    with tab:
        page = settings['pages'].setdefault(key, {'visible': True, 'title': label, 'subtitle': '', 'text': '', 'cta': ''})
        st.subheader(label)
        page['visible'] = st.checkbox('Показывать в нижней панели', value=bool(page.get('visible', True)), key=f'{key}_visible')
        page['title'] = st.text_input('Заголовок', value=str(page.get('title', label)), key=f'{key}_title')
        page['subtitle'] = st.text_input('Подзаголовок', value=str(page.get('subtitle', '')), key=f'{key}_subtitle')
        page['text'] = st.text_area('Текст / информация', value=str(page.get('text', '')), height=110, key=f'{key}_text')
        page['cta'] = st.text_input('Кнопка / CTA', value=str(page.get('cta', '')), key=f'{key}_cta')

        if key == 'catalog':
            st.divider()
            st.subheader('Разделы каталога')
            settings['catalog_sections'] = st.data_editor(pd.DataFrame(settings['catalog_sections']), num_rows='dynamic', use_container_width=True, key='sections').to_dict('records')
            st.subheader('Фильтры')
            settings['catalog_filters'] = st.data_editor(pd.DataFrame(settings['catalog_filters']), num_rows='dynamic', use_container_width=True, key='filters').to_dict('records')
            st.subheader('Сортировки')
            settings['catalog_sorts'] = st.data_editor(pd.DataFrame(settings['catalog_sorts']), num_rows='dynamic', use_container_width=True, key='sorts').to_dict('records')
        else:
            st.info('Детальная настройка этой страницы будет позже. Сейчас можно менять текст и видимость.')

if st.button('Сохранить настройки страниц', type='primary'):
    save_settings(settings)
    st.success('Настройки сохранены')

st.download_button('Скачать page_settings.json', json.dumps(settings, ensure_ascii=False, indent=2), file_name='page_settings.json')
