from __future__ import annotations

import streamlit as st
import pandas as pd

from modules.db import test_database_connection, get_database_config, mask_database_url

st.set_page_config(page_title="KURGIN Admin — 7P PostgreSQL", layout="wide")
st.markdown(
    """
<style>
.block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 1500px;}
div[data-testid="stVerticalBlock"] {gap: 0.45rem;}
.stDataFrame {font-size: 12px;}
h1, h2, h3 {margin-bottom: 0.3rem;}
</style>
""",
    unsafe_allow_html=True,
)

st.title("7P.2 — PostgreSQL подключение")
st.caption("Read-only проверка подключения к базе. Эта страница не создаёт таблицы и не пишет данные.")

st.subheader("Птичий взгляд")
st.markdown(
    """
Цель этого шага — не переписать админку сразу, а проверить, может ли KURGIN Admin видеть постоянную базу данных.

Правильная цепочка дальше: **проверить подключение → создать минимальную схему → перенести CSV в PostgreSQL → читать Admin из базы → оставить CSV как импорт/экспорт**.
"""
)

config = get_database_config()
if config is None:
    st.error("DATABASE_URL не настроен.")
    st.markdown(
        """
Нужно добавить строку подключения в **Streamlit Cloud → App settings → Secrets**.

Название секрета должно быть:

```toml
DATABASE_URL = "..."
```

Саму строку с паролем не присылай в чат. Возьми её в Timeweb в разделе базы данных / подключение к PostgreSQL.
"""
    )
    st.stop()

st.info(f"Источник настроек: {config.source}")
st.code(mask_database_url(config.url), language="text")

if st.button("Проверить подключение", type="primary"):
    result = test_database_connection()
    if result.get("ok"):
        st.success("Подключение к PostgreSQL работает.")
    else:
        st.error("Подключение не работает.")

    rows = [
        {"Параметр": "configured", "Значение": result.get("configured")},
        {"Параметр": "source", "Значение": result.get("source")},
        {"Параметр": "masked_url", "Значение": result.get("masked_url")},
        {"Параметр": "database", "Значение": result.get("database")},
        {"Параметр": "user", "Значение": result.get("user")},
        {"Параметр": "schema", "Значение": result.get("current_schema")},
        {"Параметр": "server_version", "Значение": result.get("server_version")},
        {"Параметр": "error", "Значение": result.get("error")},
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=320)

st.subheader("Что делать после успешной проверки")
st.markdown(
    """
После зелёного статуса подключения следующий маленький шаг:

1. Создать отдельную схему/таблицы KURGIN для камней, поставок и публикации.
2. Сделать one-way миграцию: текущие CSV → PostgreSQL.
3. Переключить чтение Admin на PostgreSQL.
4. Оставить `exports/public_stones_v1.csv` как публичный export для сайта.

До успешной проверки подключения не нужно переносить логику импорта или публикации.
"""
)
