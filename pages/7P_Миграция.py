from __future__ import annotations

import streamlit as st
import pandas as pd

from modules.db import test_database_connection, get_core_tables_status
from modules.db_migration import build_csv_to_postgres_preview, migrate_csv_to_postgres

CONFIRM_TEXT = "МИГРИРОВАТЬ CSV В POSTGRESQL"

st.set_page_config(page_title="KURGIN Admin — 7P Миграция", layout="wide")
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

st.title("7P.5 — Миграция CSV → PostgreSQL")
st.caption("Переносит текущие CSV-данные в PostgreSQL через upsert. Админка пока не переключается на чтение из базы.")

st.subheader("Птичий взгляд")
st.markdown(
    """
Цель этого шага — закрепить текущие камни и поставки в постоянной базе, чтобы после перезапуска Streamlit данные не зависели только от временных CSV.

Это не финальный переход на PostgreSQL. После миграции следующий отдельный шаг — переключить чтение Admin на базу.
"""
)

connection = test_database_connection()
if not connection.get("ok"):
    st.error("PostgreSQL подключение сейчас не работает. Сначала проверь страницу 7P PostgreSQL.")
    st.dataframe(pd.DataFrame([connection]), use_container_width=True, hide_index=True)
    st.stop()

core_status = get_core_tables_status()
if not core_status.get("ok") or not core_status.get("core_ready"):
    st.error("Минимальные таблицы PostgreSQL не готовы. Сначала заверши 7P Таблицы БД.")
    st.dataframe(pd.DataFrame([core_status]), use_container_width=True, hide_index=True)
    st.stop()

preview = build_csv_to_postgres_preview()
if not preview.get("ok"):
    st.error("Не удалось собрать preview миграции.")
    st.code(preview.get("error", ""), language="text")
    st.stop()

summary = preview.get("summary", {})
c1, c2, c3, c4 = st.columns(4)
c1.metric("Камней CSV", summary.get("stones_csv_rows", 0))
c2.metric("Поставок CSV", summary.get("shipments_csv_rows", 0))
c3.metric("Import log CSV", summary.get("import_log_csv_rows", 0))
c4.metric("Всего строк CSV", summary.get("total_csv_rows", 0))

st.subheader("Preview по таблицам")
st.dataframe(pd.DataFrame(preview.get("tables", [])), use_container_width=True, hide_index=True, height=240)

if preview.get("blockers"):
    st.error("Миграция пока заблокирована:")
    for item in preview.get("blockers", []):
        st.write(f"- {item}")
    st.stop()

st.success("Preview готов. Можно выполнить миграцию после подтверждения.")
st.warning("Миграция использует upsert: повторный запуск обновит существующие строки по ключу, но не создаст дубли. Удалений не будет.")

confirm = st.text_input(f"Для миграции введите: {CONFIRM_TEXT}")
if st.button("Мигрировать CSV в PostgreSQL", type="primary"):
    if confirm != CONFIRM_TEXT:
        st.error("Фраза подтверждения не совпадает.")
    else:
        result = migrate_csv_to_postgres()
        if not result.get("ok"):
            st.error("Миграция не выполнена.")
            st.code(result.get("error", ""), language="text")
        else:
            st.success("Миграция CSV → PostgreSQL выполнена.")
            upserted = result.get("upserted", {})
            st.dataframe(
                pd.DataFrame([
                    {"Таблица": "stones", "Upserted": upserted.get("stones", 0)},
                    {"Таблица": "shipments", "Upserted": upserted.get("shipments", 0)},
                    {"Таблица": "import_log", "Upserted": upserted.get("import_log", 0)},
                    {"Таблица": "public_exports", "Upserted": upserted.get("public_exports", 0)},
                ]),
                use_container_width=True,
                hide_index=True,
                height=180,
            )
            after = result.get("after", {})
            counts = after.get("counts", {})
            st.write("Строки в PostgreSQL после миграции:")
            st.dataframe(
                pd.DataFrame([{"Таблица": k, "Строк": v} for k, v in counts.items()]),
                use_container_width=True,
                hide_index=True,
                height=220,
            )
            st.rerun()

st.subheader("Что дальше")
st.markdown(
    """
После успешной миграции следующий разумный шаг — **7P.6: проверка чтения из PostgreSQL**.

Сначала добавляем read-only страницу, которая показывает камни из базы. Только после проверки можно переключать основную страницу `Камни` на PostgreSQL.
"""
)
