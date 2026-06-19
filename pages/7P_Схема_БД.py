from __future__ import annotations

import streamlit as st
import pandas as pd

from modules.db import (
    KURGIN_SCHEMA_NAME,
    test_database_connection,
    get_kurgin_schema_status,
    schema_sql_preview,
    create_kurgin_schema,
)

CONFIRM_TEXT = "СОЗДАТЬ СХЕМУ KURGIN"

st.set_page_config(page_title="KURGIN Admin — 7P Схема БД", layout="wide")
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

st.title("7P.3 — Схема PostgreSQL для KURGIN Admin")
st.caption("Безопасный шаг: создаётся отдельная схема и служебная таблица миграций. Данные камней пока не переносятся.")

st.subheader("Птичий взгляд")
st.markdown(
    f"""
Сейчас цель — закрепить постоянное хранилище без резкого переписывания админки.

Этот шаг создаёт отдельную область в базе: **`{KURGIN_SCHEMA_NAME}`**. Она отделяет KURGIN Admin от `public` и от возможных таблиц формулы. Это не перенос данных и не новая функция ради функции — это фундамент для следующего шага: CSV → PostgreSQL.
"""
)

connection = test_database_connection()
if not connection.get("ok"):
    st.error("PostgreSQL подключение сейчас не работает. Сначала вернись на страницу 7P PostgreSQL и добейся зелёного статуса.")
    st.dataframe(pd.DataFrame([connection]), use_container_width=True, hide_index=True)
    st.stop()

st.success(f"PostgreSQL доступен. База: {connection.get('database')}; пользователь: {connection.get('user')}.")

status = get_kurgin_schema_status()
if not status.get("ok"):
    st.error("Не удалось проверить схему.")
    st.code(status.get("error", ""), language="text")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Схема", status.get("schema", KURGIN_SCHEMA_NAME))
c2.metric("Существует", "да" if status.get("exists") else "нет")
c3.metric("Таблиц", len(status.get("tables", [])))

if status.get("tables"):
    st.write("Таблицы в схеме:")
    st.dataframe(pd.DataFrame({"table_name": status.get("tables", [])}), use_container_width=True, hide_index=True, height=180)

st.subheader("Preview SQL")
st.code(schema_sql_preview(), language="sql")

if status.get("exists"):
    st.info("Схема уже существует. Этот шаг повторно выполнять не нужно. Следующий разумный шаг — 7P.4: минимальные таблицы и миграция CSV → PostgreSQL.")
else:
    st.warning("Создание схемы не удаляет и не изменяет существующие данные. Будет создана только отдельная схема и служебная таблица schema_migrations.")
    confirm = st.text_input(f"Для создания схемы введите: {CONFIRM_TEXT}")
    if st.button("Создать схему KURGIN Admin", type="primary"):
        if confirm != CONFIRM_TEXT:
            st.error("Фраза подтверждения не совпадает.")
        else:
            result = create_kurgin_schema()
            if result.get("ok"):
                st.success("Схема kurgin_admin создана.")
                st.rerun()
            else:
                st.error("Не удалось создать схему.")
                st.code(result.get("error", ""), language="text")

st.subheader("Что дальше")
st.markdown(
    """
После создания схемы следующий маленький шаг — **7P.4**:

1. Создать минимальные таблицы `stones`, `shipments`, `import_log`, `public_exports`.
2. Не переписывать весь Admin сразу.
3. Сначала сделать one-way миграцию текущих CSV в PostgreSQL.
4. Потом переключить чтение камней из базы.

Так мы движемся к полноценной платформе без зацикливания на промежуточных улучшениях.
"""
)
