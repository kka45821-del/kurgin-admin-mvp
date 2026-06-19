from __future__ import annotations

import streamlit as st
import pandas as pd

from modules.db import (
    KURGIN_SCHEMA_NAME,
    KURGIN_CORE_TABLES,
    test_database_connection,
    get_kurgin_schema_status,
    get_core_tables_status,
    core_tables_sql_preview,
    create_core_tables,
)

CONFIRM_TEXT = "СОЗДАТЬ ТАБЛИЦЫ KURGIN"

st.set_page_config(page_title="KURGIN Admin — 7P Таблицы БД", layout="wide")
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

st.title("7P.4 — Минимальные таблицы PostgreSQL")
st.caption("Создаёт только структуру таблиц. CSV-данные пока не мигрируются, админка пока не переключается на базу.")

st.subheader("Птичий взгляд")
st.markdown(
    f"""
Мы не переписываем весь KURGIN Admin. Этот шаг создаёт четыре минимальные таблицы в **`{KURGIN_SCHEMA_NAME}`**, чтобы дальше можно было сделать one-way миграцию CSV → PostgreSQL.

Подход намеренно компактный: ключевые поля вынесены в колонки, полный исходный ряд хранится в `payload jsonb`. Это снижает риск большой преждевременной переделки и даёт путь к полноценной платформе.
"""
)

connection = test_database_connection()
if not connection.get("ok"):
    st.error("PostgreSQL подключение сейчас не работает. Сначала проверь страницу 7P PostgreSQL.")
    st.dataframe(pd.DataFrame([connection]), use_container_width=True, hide_index=True)
    st.stop()

schema_status = get_kurgin_schema_status()
if not schema_status.get("ok") or not schema_status.get("exists"):
    st.error("Схема kurgin_admin не найдена. Сначала создай её на странице 7P Схема БД.")
    st.dataframe(pd.DataFrame([schema_status]), use_container_width=True, hide_index=True)
    st.stop()

status = get_core_tables_status()
if not status.get("ok"):
    st.error("Не удалось проверить таблицы.")
    st.code(status.get("error", ""), language="text")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Схема", KURGIN_SCHEMA_NAME)
c2.metric("Core tables ready", "да" if status.get("core_ready") else "нет")
c3.metric("Таблиц в схеме", len(status.get("existing_tables", [])))

expected_rows = []
existing = set(status.get("existing_tables", []))
counts = status.get("counts", {})
for table_name in ["schema_migrations", *KURGIN_CORE_TABLES]:
    expected_rows.append({
        "Таблица": table_name,
        "Существует": "да" if table_name in existing else "нет",
        "Строк": counts.get(table_name, ""),
    })
st.dataframe(pd.DataFrame(expected_rows), use_container_width=True, hide_index=True, height=240)

if status.get("missing_core_tables"):
    st.warning("Не хватает таблиц: " + ", ".join(status.get("missing_core_tables", [])))
else:
    st.success("Минимальные таблицы уже созданы. Следующий шаг — 7P.5: миграция CSV → PostgreSQL.")

st.subheader("Preview SQL")
st.code(core_tables_sql_preview(), language="sql")

if status.get("core_ready"):
    st.info("Повторно создавать таблицы не нужно. Этот шаг завершён.")
else:
    st.warning("Создание таблиц не переносит CSV-данные и не меняет текущую работу админки. Это только структура PostgreSQL.")
    confirm = st.text_input(f"Для создания таблиц введите: {CONFIRM_TEXT}")
    if st.button("Создать минимальные таблицы", type="primary"):
        if confirm != CONFIRM_TEXT:
            st.error("Фраза подтверждения не совпадает.")
        else:
            result = create_core_tables()
            if result.get("ok"):
                st.success("Минимальные таблицы KURGIN созданы.")
                st.rerun()
            else:
                st.error("Не удалось создать таблицы.")
                st.code(result.get("error", ""), language="text")

st.subheader("Что дальше")
st.markdown(
    """
После создания таблиц следующий конкретный шаг — **7P.5: миграция CSV → PostgreSQL**.

Порядок без зацикливания:

1. Показать preview: сколько строк из CSV будет перенесено.
2. Перенести данные в PostgreSQL после подтверждения.
3. Проверить counts в таблицах.
4. Потом отдельно переключать чтение Admin на PostgreSQL.

До миграции не нужно трогать дизайн, PDF или публичную витрину.
"""
)
