from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import platform
import streamlit as st
import pandas as pd

from modules.paths import (
    ROOT,
    DATA_DIR,
    RAW_DIR,
    EXPORTS_DIR,
    BACKUPS_DIR,
    STONES_FILE,
    SHIPMENTS_FILE,
    IMPORT_LOG_FILE,
    PAYMENTS_FILE,
    CATALOG_SECTIONS_FILE,
    PRICE_SUPPLIER_FILE,
    PRICE_EXPENSE_RATES_FILE,
    PRICE_MARGINS_FILE,
    PRICE_SCORE_COEFFICIENTS_FILE,
    CURRENCY_RATES_FILE,
)
from modules.storage import ensure_data_files, read_stones, read_shipments, read_import_log, read_payments, read_catalog_sections

st.set_page_config(page_title="KURGIN Admin — 7P Хранилище", layout="wide")
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

ensure_data_files()

DATA_FILES = [
    ("Камни", STONES_FILE),
    ("Поставки", SHIPMENTS_FILE),
    ("Журнал импорта", IMPORT_LOG_FILE),
    ("Платежи поставок", PAYMENTS_FILE),
    ("Разделы каталога", CATALOG_SECTIONS_FILE),
    ("Цены поставщика", PRICE_SUPPLIER_FILE),
    ("Расходы", PRICE_EXPENSE_RATES_FILE),
    ("Маржи", PRICE_MARGINS_FILE),
    ("Коэффициенты KURGIN Score", PRICE_SCORE_COEFFICIENTS_FILE),
    ("Курсы валют", CURRENCY_RATES_FILE),
]

EXPORT_FILES = [
    ("Публичный экспорт", EXPORTS_DIR / "public_stones_v1.csv"),
]


def _fmt_time(ts: float | None) -> str:
    if ts is None:
        return ""
    return datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def _file_info(label: str, path: Path) -> dict:
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    modified = path.stat().st_mtime if exists else None
    rows = ""
    columns = ""
    read_error = ""
    if exists and path.suffix.lower() == ".csv":
        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
            rows = int(len(df))
            columns = int(len(df.columns))
        except Exception as exc:
            read_error = str(exc)
    return {
        "Файл": label,
        "Путь": str(path),
        "Существует": "да" if exists else "нет",
        "Размер байт": size,
        "Строк": rows,
        "Колонок": columns,
        "Изменён": _fmt_time(modified),
        "Ошибка чтения": read_error,
    }


def _count_raw_imports() -> int:
    if not RAW_DIR.exists():
        return 0
    return len([p for p in RAW_DIR.iterdir() if p.is_dir()])


def _count_backups() -> int:
    if not BACKUPS_DIR.exists():
        return 0
    return len([p for p in BACKUPS_DIR.iterdir() if p.is_dir()])


def _is_probably_streamlit_cloud() -> bool:
    markers = [
        os.environ.get("STREAMLIT_SERVER_PORT"),
        os.environ.get("STREAMLIT_SHARING_MODE"),
        os.environ.get("HOSTNAME"),
    ]
    cwd = str(Path.cwd())
    return any(markers) or "/mount/src" in cwd or "streamlit" in cwd.lower()


def _storage_risk_text() -> tuple[str, str]:
    if _is_probably_streamlit_cloud():
        return (
            "Высокий риск",
            "Приложение похоже на Streamlit Cloud/runtime. Файлы data/ и exports/ внутри контейнера могут исчезать после перезапуска, redeploy или пересборки, если не закреплены во внешнем постоянном хранилище.",
        )
    return (
        "Средний риск",
        "Файлы лежат в локальной папке проекта. На локальном компьютере они сохраняются, но при деплое на Streamlit Cloud без внешнего storage рабочие данные всё равно могут исчезать.",
    )


st.title("7P.1 — Хранилище и состояние данных")
st.caption("Read-only диагностика. Эта страница ничего не публикует, не удаляет и не меняет в CSV.")

stones = read_stones()
shipments = read_shipments()
import_log = read_import_log()
payments = read_payments()
sections = read_catalog_sections()

published_count = int((stones["status"].astype(str) == "published").sum()) if not stones.empty and "status" in stones.columns else 0
in_stock_count = int((stones["availability_status"].astype(str) == "in_stock").sum()) if not stones.empty and "availability_status" in stones.columns else 0
ready_count = int((stones["status"].astype(str) == "ready").sum()) if not stones.empty and "status" in stones.columns else 0
archived_count = int((stones["status"].astype(str) == "archived").sum()) if not stones.empty and "status" in stones.columns else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Камней в Admin", len(stones))
c2.metric("Поставок", len(shipments))
c3.metric("Опубликовано", published_count)
c4.metric("В наличии", in_stock_count)
c5.metric("Raw импортов", _count_raw_imports())

c6, c7, c8, c9 = st.columns(4)
c6.metric("Ready", ready_count)
c7.metric("Архив", archived_count)
c8.metric("Backups", _count_backups())
c9.metric("Платежей", len(payments))

risk_level, risk_text = _storage_risk_text()
if risk_level == "Высокий риск":
    st.error(f"{risk_level}: {risk_text}")
else:
    st.warning(f"{risk_level}: {risk_text}")

st.subheader("Птичий взгляд")
st.markdown(
    """
Сейчас эта страница отвечает на один вопрос: **есть ли у админки надёжная память после перезапуска**.

Если здесь `Камней в Admin = 0`, а публичная витрина показывает камни, значит публичный слой и админка читают разные источники или витрина показывает старый опубликованный файл/кэш. Это не ошибка карточки — это проблема единого источника данных.
"""
)

st.subheader("Папки проекта")
folder_rows = []
for label, path in [
    ("ROOT", ROOT),
    ("DATA_DIR", DATA_DIR),
    ("RAW_DIR", RAW_DIR),
    ("EXPORTS_DIR", EXPORTS_DIR),
    ("BACKUPS_DIR", BACKUPS_DIR),
]:
    folder_rows.append({
        "Папка": label,
        "Путь": str(path),
        "Существует": "да" if path.exists() else "нет",
        "Элементов": len(list(path.iterdir())) if path.exists() and path.is_dir() else 0,
    })
st.dataframe(pd.DataFrame(folder_rows), use_container_width=True, hide_index=True, height=220)

st.subheader("Рабочие CSV-файлы Admin")
file_rows = [_file_info(label, path) for label, path in DATA_FILES]
st.dataframe(pd.DataFrame(file_rows), use_container_width=True, hide_index=True, height=360)

st.subheader("Публичные export-файлы")
export_rows = [_file_info(label, path) for label, path in EXPORT_FILES]
st.dataframe(pd.DataFrame(export_rows), use_container_width=True, hide_index=True, height=160)

st.subheader("Краткая проверка согласованности")
checks = []
checks.append({
    "Проверка": "Admin содержит камни",
    "Статус": "OK" if len(stones) > 0 else "Проблема",
    "Комментарий": "stones_master.csv содержит строки" if len(stones) > 0 else "stones_master.csv пустой; после перезапуска админка не видит камни",
})
checks.append({
    "Проверка": "Есть публичный export",
    "Статус": "OK" if (EXPORTS_DIR / "public_stones_v1.csv").exists() else "Не найден",
    "Комментарий": "exports/public_stones_v1.csv есть" if (EXPORTS_DIR / "public_stones_v1.csv").exists() else "публичный export не записан в текущем runtime",
})
checks.append({
    "Проверка": "Опубликованные камни есть в Admin",
    "Статус": "OK" if published_count > 0 else "Нет",
    "Комментарий": f"published: {published_count}",
})
checks.append({
    "Проверка": "Поставки есть в Admin",
    "Статус": "OK" if len(shipments) > 0 else "Нет",
    "Комментарий": f"shipments: {len(shipments)}",
})
st.dataframe(pd.DataFrame(checks), use_container_width=True, hide_index=True, height=220)

with st.expander("Техническая среда", expanded=False):
    env_rows = [
        {"Ключ": "platform", "Значение": platform.platform()},
        {"Ключ": "python", "Значение": platform.python_version()},
        {"Ключ": "cwd", "Значение": str(Path.cwd())},
        {"Ключ": "ROOT", "Значение": str(ROOT)},
        {"Ключ": "STREAMLIT_SERVER_PORT", "Значение": os.environ.get("STREAMLIT_SERVER_PORT", "")},
        {"Ключ": "STREAMLIT_SHARING_MODE", "Значение": os.environ.get("STREAMLIT_SHARING_MODE", "")},
        {"Ключ": "HOSTNAME", "Значение": os.environ.get("HOSTNAME", "")},
    ]
    st.dataframe(pd.DataFrame(env_rows), use_container_width=True, hide_index=True, height=280)

st.subheader("Следующий разумный шаг после диагностики")
st.markdown(
    """
Если после перезапуска здесь снова `Камней в Admin = 0`, значит нужно делать **7P.2 — постоянное хранилище**.

Практический выбор:

1. **PostgreSQL** — правильный путь к полноценной платформе.
2. **Временное приватное CSV-хранилище** — быстрее, но это промежуточное решение и не должно храниться в публичном репозитории.

До решения 7P.2 не стоит загружать настоящие рабочие поставки как единственный источник истины.
"""
)
