import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="CVDLAB Admin v2", page_icon="◇", layout="wide")

SECTIONS = [
    "Command Center",
    "Risk Center",
    "Каталог",
    "Партии",
    "Индекс и формула",
    "Цены",
    "Публикация",
    "Сайт и тексты",
    "Корзины и заказы",
    "Партнёры",
    "Аналитика",
    "Настройки",
]

with st.sidebar:
    st.header("CVDLAB Admin v2")
    section = st.radio("Раздел", SECTIONS)

st.title(section)

def get_json(path: str):
    r = requests.get(API_URL + path, timeout=10)
    r.raise_for_status()
    return r.json()

if section == "Command Center":
    st.info("Платформенный foundation: PostgreSQL-first, API-first, Streamlit только UI.")
    cols = st.columns(4)
    cols[0].metric("PostgreSQL", "required")
    cols[1].metric("Public checkout", "off")
    cols[2].metric("Mock payments", "on")
    cols[3].metric("Public Index", "₽/ct")
elif section == "Risk Center":
    st.warning("Risk Center должен блокировать утечки public snapshot, дубли stone_id, stale site settings и неверные price channels.")
elif section == "Индекс и формула":
    st.subheader("KURGIN Index ₽/ct")
    st.json(get_json("/index/public-snapshot"))
elif section == "Публикация":
    tab1, tab2, tab3 = st.tabs(["Catalog", "Index", "Site settings"])
    with tab1: st.json(get_json("/catalog/public-snapshot"))
    with tab2: st.json(get_json("/index/public-snapshot"))
    with tab3: st.json(get_json("/site-settings/snapshot"))
elif section == "Сайт и тексты":
    st.json(get_json("/site-settings/snapshot"))
elif section == "Партнёры":
    st.info("Партнёрский кабинет: RU / EN / zh-CN / HY, явный доступ к партиям, 3 состояния партии, чат и документы.")
elif section == "Корзины и заказы":
    st.info("Все покупки: камни, Analyzer single run, подписки, private offer — через cart/order. Real provider позже.")
else:
    st.info("Раздел заложен в V1 foundation и будет развиваться через API/services.")
