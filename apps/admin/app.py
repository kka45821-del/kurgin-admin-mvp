from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = 6

st.set_page_config(
    page_title="KURGIN Admin",
    page_icon="◇",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --k-bg: #0f1115;
        --k-panel: #171a21;
        --k-panel-soft: #1f2430;
        --k-border: rgba(255,255,255,.10);
        --k-text-muted: rgba(255,255,255,.62);
        --k-accent: #d9c184;
        --k-good: #58c783;
        --k-warn: #f1c75b;
        --k-bad: #ef6f6c;
    }
    .block-container {padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1480px;}
    [data-testid="stSidebar"] {background: #101218; border-right: 1px solid var(--k-border);}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {letter-spacing: .02em;}
    [data-testid="stSidebar"] label {font-size: .88rem; color: var(--k-text-muted);}
    [data-testid="stSidebar"] [role="radiogroup"] label {
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 12px;
        padding: .55rem .65rem;
        margin: .18rem 0;
        background: rgba(255,255,255,.025);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        border-color: rgba(217,193,132,.45);
        background: rgba(217,193,132,.07);
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(255,255,255,.055), rgba(255,255,255,.025));
        border: 1px solid var(--k-border);
        border-radius: 16px;
        padding: 14px 16px;
    }
    div[data-testid="stMetric"] label {color: var(--k-text-muted);}
    .k-card {
        border: 1px solid var(--k-border);
        border-radius: 18px;
        padding: 16px 18px;
        background: linear-gradient(180deg, rgba(255,255,255,.055), rgba(255,255,255,.025));
        min-height: 92px;
    }
    .k-muted {color: var(--k-text-muted); font-size: .92rem;}
    .k-section-title {font-size: 1.05rem; font-weight: 700; margin-bottom: .35rem;}
    .k-pill {display:inline-block; padding:.2rem .55rem; border-radius:999px; border:1px solid var(--k-border); font-size:.78rem; color:var(--k-text-muted);}
    .stDataFrame, [data-testid="stDataFrame"] {font-size: 12px;}
    [data-testid="stVerticalBlock"] {gap: .65rem;}
    button[kind="primary"] {border-radius: 12px;}
    </style>
    """,
    unsafe_allow_html=True,
)

SECTIONS = [
    "Главная",
    "Каталог камней",
    "Индекс ₽/ct",
    "Публикация",
    "Тексты сайта",
    "Risk Center",
    "Настройки",
]

CATALOG_COLUMNS = [
    "status",
    "stone_id",
    "title",
    "shape",
    "carat",
    "color",
    "clarity",
    "lab",
    "report_number",
    "kurgin_score",
    "public_price_rub",
    "show_in_catalog",
    "checkout_enabled",
    "section",
]

INDEX_COLUMNS = [
    "status",
    "color",
    "clarity",
    "carat_band_from",
    "carat_band_to",
    "score_range",
    "score_label",
    "public_index_rub_per_ct",
]

TEXT_COLUMNS = ["key", "ru", "en", "zh-CN", "hy", "public_visible"]


def sample_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "status": "draft",
                "stone_id": "KRG-001",
                "title": "Round 1.01 ct D VS1",
                "shape": "Round",
                "carat": 1.01,
                "color": "D",
                "clarity": "VS1",
                "lab": "IGI",
                "report_number": "LG000001",
                "kurgin_score": 92,
                "public_price_rub": 0,
                "show_in_catalog": True,
                "checkout_enabled": False,
                "section": "main",
            },
            {
                "status": "ready",
                "stone_id": "KRG-002",
                "title": "Oval 1.50 ct E VS2",
                "shape": "Oval",
                "carat": 1.50,
                "color": "E",
                "clarity": "VS2",
                "lab": "IGI",
                "report_number": "LG000002",
                "kurgin_score": 0,
                "public_price_rub": 0,
                "show_in_catalog": False,
                "checkout_enabled": False,
                "section": "reserve",
            },
        ],
        columns=CATALOG_COLUMNS,
    )


def sample_index() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "status": "active",
                "color": "D",
                "clarity": "VS1",
                "carat_band_from": 1.0,
                "carat_band_to": 1.5,
                "score_range": "standard",
                "score_label": "Standard",
                "public_index_rub_per_ct": 780000,
            },
            {
                "status": "draft",
                "color": "E",
                "clarity": "VS2",
                "carat_band_from": 1.0,
                "carat_band_to": 1.5,
                "score_range": "premium",
                "score_label": "Premium",
                "public_index_rub_per_ct": 820000,
            },
        ],
        columns=INDEX_COLUMNS,
    )


def sample_texts() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "key": "partner.batch.on_site",
                "ru": "На сайте",
                "en": "On site",
                "zh-CN": "网站展示中",
                "hy": "Կայքում",
                "public_visible": True,
            },
            {
                "key": "partner.batch.sold",
                "ru": "Продано",
                "en": "Sold",
                "zh-CN": "已售出",
                "hy": "Վաճառված",
                "public_visible": True,
            },
            {
                "key": "partner.batch.removed",
                "ru": "Снятые с продажи",
                "en": "Removed from sale",
                "zh-CN": "已下架",
                "hy": "Հանված վաճառքից",
                "public_visible": False,
            },
        ],
        columns=TEXT_COLUMNS,
    )


def init_state() -> None:
    st.session_state.setdefault("catalog_df", sample_catalog())
    st.session_state.setdefault("index_df", sample_index())
    st.session_state.setdefault("texts_df", sample_texts())
    st.session_state.setdefault("request_only", True)
    st.session_state.setdefault("active_index_version", "demo_index_v1")
    st.session_state.setdefault("last_local_save", "ещё не сохранялось")


def api_get(path: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        response = requests.get(f"{API_URL}{path}", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json(), None
    except Exception as exc:  # noqa: BLE001 - Streamlit UI should not crash on API downtime.
        return None, str(exc)


def rub(value: Any) -> str:
    try:
        return f"{int(float(value)):,}".replace(",", " ") + " ₽"
    except Exception:
        return "0 ₽"


def now_label() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def build_catalog_snapshot(df: pd.DataFrame, request_only: bool = True) -> dict[str, Any]:
    rows = df.fillna("").to_dict("records")
    public_rows: list[dict[str, Any]] = []
    for row in rows:
        visible = bool(row.get("show_in_catalog")) and row.get("status") in {"ready", "active", "published"}
        if not visible:
            continue
        price = int(float(row.get("public_price_rub") or 0))
        public_rows.append(
            {
                "id": row.get("stone_id"),
                "stone_id": row.get("stone_id"),
                "title": row.get("title"),
                "shape": row.get("shape"),
                "carat": row.get("carat"),
                "color": row.get("color"),
                "clarity": row.get("clarity"),
                "lab": row.get("lab"),
                "report_number": row.get("report_number"),
                "kurgin_score": row.get("kurgin_score"),
                "section": row.get("section"),
                "public_visible": True,
                "is_request_price": request_only or price <= 0,
                "public_price_rub": 0 if request_only else price,
                "priceText": "по запросу" if request_only or price <= 0 else rub(price).replace(" ₽", ""),
                "public_action": "request_price" if request_only else "checkout",
                "checkout_enabled": False if request_only else bool(row.get("checkout_enabled")),
                "currency": "RUB",
            }
        )
    return {
        "source": "KURGIN Admin local draft",
        "schema": {"version": "public_catalog_v1"},
        "updated_at": now_label(),
        "count": len(public_rows),
        "stones": public_rows,
    }


def build_index_snapshot(df: pd.DataFrame, version: str) -> dict[str, Any]:
    rows = df[df["status"].isin(["active", "published"])].fillna("").to_dict("records")
    return {
        "source": "KURGIN Admin local draft",
        "schema": {"version": "public_index_v1"},
        "currency": "RUB",
        "unit": "per_carat",
        "unit_label": "₽/ct",
        "active_index_version": version,
        "updated_at": now_label(),
        "rows": rows,
        "disclaimer": {"ru": "KURGIN Index — публичный ориентир ₽/ct. Это не цена конкретного камня и не оферта."},
    }


def dataframe_download(df: pd.DataFrame, filename: str) -> None:
    st.download_button(
        "Скачать CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


def json_download(payload: dict[str, Any], filename: str, label: str = "Скачать JSON") -> None:
    st.download_button(
        label,
        data=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name=filename,
        mime="application/json",
        use_container_width=True,
    )


def health_badge() -> tuple[str, dict[str, Any] | None]:
    data, error = api_get("/health")
    if error:
        return "API offline", None
    return f"API {data.get('status', 'unknown')}", data


def compact_editor(df: pd.DataFrame, key: str, column_config: dict[str, Any], disabled: list[str] | None = None) -> pd.DataFrame:
    return st.data_editor(
        df,
        key=key,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        height=430,
        column_config=column_config,
        disabled=disabled or [],
    )


init_state()
api_state, api_health = health_badge()

with st.sidebar:
    st.markdown("# ◇ KURGIN")
    st.caption("Admin MVP · компактная рабочая панель")
    section = st.radio("Раздел", SECTIONS, label_visibility="collapsed")
    st.divider()
    st.caption("API")
    st.code(API_URL, language=None)
    if api_health:
        st.success(api_state)
    else:
        st.error(api_state)
    st.caption(f"Локальное сохранение: {st.session_state.last_local_save}")

st.title(section)

if section == "Главная":
    catalog = st.session_state.catalog_df
    index = st.session_state.index_df
    texts = st.session_state.texts_df
    visible = int((catalog["show_in_catalog"] == True).sum())  # noqa: E712 - pandas comparison.
    ready = int(catalog["status"].isin(["ready", "active", "published"]).sum())
    active_index = int(index["status"].isin(["active", "published"]).sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Камней в таблице", len(catalog))
    c2.metric("Готовы к сайту", ready)
    c3.metric("Включены в каталог", visible)
    c4.metric("Строк индекса active", active_index)
    c5.metric("Текстовых ключей", len(texts))

    st.markdown("### Что уже можно делать")
    a, b, c = st.columns(3)
    with a:
        st.markdown(
            """
            <div class="k-card"><div class="k-section-title">Редактировать таблицы</div>
            <div class="k-muted">Каталог, индекс и тексты редактируются прямо в ячейках. Строки можно добавлять вручную.</div></div>
            """,
            unsafe_allow_html=True,
        )
    with b:
        st.markdown(
            """
            <div class="k-card"><div class="k-section-title">Проверять публикацию</div>
            <div class="k-muted">Есть предпросмотр public snapshot без внутренних закупочных и служебных полей.</div></div>
            """,
            unsafe_allow_html=True,
        )
    with c:
        st.markdown(
            """
            <div class="k-card"><div class="k-section-title">Экспортировать данные</div>
            <div class="k-muted">CSV и JSON можно скачать и передать в следующий слой сайта или API.</div></div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Ближайшие блокировки перед нормальным продом")
    st.warning(
        "Пока нет настоящего сохранения в PostgreSQL через API. Редактирование работает в текущей Streamlit-сессии. "
        "Следующий правильный шаг — добавить backend endpoints: save catalog, save index, publish snapshot."
    )

elif section == "Каталог камней":
    st.caption("Компактная ручная таблица. Изменения пока сохраняются в сессии и доступны для экспорта.")
    top1, top2, top3, top4 = st.columns([1.2, 1, 1, 1])
    with top1:
        st.session_state.request_only = st.toggle("Все цены по запросу", value=st.session_state.request_only)
    with top2:
        if st.button("Сохранить локально", type="primary", use_container_width=True):
            st.session_state.last_local_save = now_label()
            st.toast("Таблица сохранена в текущей сессии")
    with top3:
        if st.button("Сбросить демо", use_container_width=True):
            st.session_state.catalog_df = sample_catalog()
            st.rerun()
    with top4:
        dataframe_download(st.session_state.catalog_df, "kurgin_catalog_table.csv")

    edited = compact_editor(
        st.session_state.catalog_df,
        key="catalog_editor",
        column_config={
            "status": st.column_config.SelectboxColumn("status", options=["draft", "ready", "active", "published", "sold", "removed"], width="small"),
            "stone_id": st.column_config.TextColumn("stone_id", width="small"),
            "title": st.column_config.TextColumn("title", width="medium"),
            "shape": st.column_config.SelectboxColumn("shape", options=["Round", "Oval", "Emerald", "Pear", "Cushion", "Princess", "Radiant", "Marquise", "Other"], width="small"),
            "carat": st.column_config.NumberColumn("ct", min_value=0.0, step=0.01, format="%.2f", width="small"),
            "color": st.column_config.SelectboxColumn("color", options=list("DEFGHIJ") + ["K", "L", "M"], width="small"),
            "clarity": st.column_config.SelectboxColumn("clarity", options=["FL", "IF", "VVS1", "VVS2", "VS1", "VS2", "SI1", "SI2"], width="small"),
            "lab": st.column_config.SelectboxColumn("lab", options=["IGI", "GIA", "GCAL", "HRD", "Other"], width="small"),
            "report_number": st.column_config.TextColumn("report #", width="small"),
            "kurgin_score": st.column_config.NumberColumn("score", min_value=0, max_value=100, step=1, width="small"),
            "public_price_rub": st.column_config.NumberColumn("price ₽", min_value=0, step=1000, width="small"),
            "show_in_catalog": st.column_config.CheckboxColumn("show", width="small"),
            "checkout_enabled": st.column_config.CheckboxColumn("checkout", width="small"),
            "section": st.column_config.SelectboxColumn("section", options=["main", "reserve", "premium", "hidden"], width="small"),
        },
    )
    st.session_state.catalog_df = edited[CATALOG_COLUMNS]

    st.markdown("### Предпросмотр public catalog")
    payload = build_catalog_snapshot(st.session_state.catalog_df, st.session_state.request_only)
    l, r = st.columns([2, 1])
    with l:
        st.dataframe(pd.DataFrame(payload["stones"]), use_container_width=True, hide_index=True, height=220)
    with r:
        st.metric("Будет опубликовано", payload["count"])
        st.caption("В public snapshot не попадают закупочные, маржинальные и внутренние поля.")
        json_download(payload, "public_catalog_snapshot.json")

elif section == "Индекс ₽/ct":
    st.caption("Редактирование строк публичного индекса. На сайт должны уходить только active/published строки.")
    c1, c2, c3 = st.columns([1.4, 1, 1])
    with c1:
        st.session_state.active_index_version = st.text_input("Версия индекса", value=st.session_state.active_index_version)
    with c2:
        if st.button("Сохранить локально", type="primary", use_container_width=True):
            st.session_state.last_local_save = now_label()
            st.toast("Индекс сохранён в текущей сессии")
    with c3:
        dataframe_download(st.session_state.index_df, "kurgin_index_table.csv")

    edited = compact_editor(
        st.session_state.index_df,
        key="index_editor",
        column_config={
            "status": st.column_config.SelectboxColumn("status", options=["draft", "active", "published", "archived"], width="small"),
            "color": st.column_config.SelectboxColumn("color", options=list("DEFGHIJ") + ["K", "L", "M"], width="small"),
            "clarity": st.column_config.SelectboxColumn("clarity", options=["FL", "IF", "VVS1", "VVS2", "VS1", "VS2", "SI1", "SI2"], width="small"),
            "carat_band_from": st.column_config.NumberColumn("from ct", min_value=0.0, step=0.01, format="%.2f", width="small"),
            "carat_band_to": st.column_config.NumberColumn("to ct", min_value=0.0, step=0.01, format="%.2f", width="small"),
            "score_range": st.column_config.TextColumn("range", width="small"),
            "score_label": st.column_config.TextColumn("label", width="small"),
            "public_index_rub_per_ct": st.column_config.NumberColumn("₽/ct", min_value=0, step=1000, width="small"),
        },
    )
    st.session_state.index_df = edited[INDEX_COLUMNS]

    payload = build_index_snapshot(st.session_state.index_df, st.session_state.active_index_version)
    l, r = st.columns([2, 1])
    with l:
        st.markdown("### Публичные строки")
        st.dataframe(pd.DataFrame(payload["rows"]), use_container_width=True, hide_index=True, height=240)
    with r:
        st.metric("Active rows", len(payload["rows"]))
        json_download(payload, "public_index_snapshot.json")

elif section == "Публикация":
    st.caption("Сравнение локального draft snapshot и текущих API snapshot. Если API выключен, показывается только локальный проект.")
    local_catalog = build_catalog_snapshot(st.session_state.catalog_df, st.session_state.request_only)
    local_index = build_index_snapshot(st.session_state.index_df, st.session_state.active_index_version)
    api_catalog, catalog_error = api_get("/catalog/public-snapshot")
    api_index, index_error = api_get("/index/public-snapshot")
    api_settings, settings_error = api_get("/site-settings/snapshot")

    tabs = st.tabs(["Catalog", "Index", "Site settings"])
    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Local draft")
            st.json(local_catalog, expanded=False)
            json_download(local_catalog, "public_catalog_snapshot.local.json", "Скачать local JSON")
        with c2:
            st.markdown("#### API current")
            if catalog_error:
                st.error(catalog_error)
            else:
                st.json(api_catalog, expanded=False)
    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Local draft")
            st.json(local_index, expanded=False)
            json_download(local_index, "public_index_snapshot.local.json", "Скачать local JSON")
        with c2:
            st.markdown("#### API current")
            if index_error:
                st.error(index_error)
            else:
                st.json(api_index, expanded=False)
    with tabs[2]:
        if settings_error:
            st.error(settings_error)
        else:
            st.json(api_settings, expanded=False)

elif section == "Тексты сайта":
    st.caption("Мини-таблица переводов для сайта и партнёрского кабинета.")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("Сохранить локально", type="primary", use_container_width=True):
            st.session_state.last_local_save = now_label()
            st.toast("Тексты сохранены в текущей сессии")
    with c2:
        if st.button("Сбросить демо", use_container_width=True):
            st.session_state.texts_df = sample_texts()
            st.rerun()
    with c3:
        dataframe_download(st.session_state.texts_df, "kurgin_site_texts.csv")

    edited = compact_editor(
        st.session_state.texts_df,
        key="texts_editor",
        column_config={
            "key": st.column_config.TextColumn("key", width="medium"),
            "ru": st.column_config.TextColumn("ru", width="medium"),
            "en": st.column_config.TextColumn("en", width="medium"),
            "zh-CN": st.column_config.TextColumn("zh-CN", width="medium"),
            "hy": st.column_config.TextColumn("hy", width="medium"),
            "public_visible": st.column_config.CheckboxColumn("public", width="small"),
        },
    )
    st.session_state.texts_df = edited[TEXT_COLUMNS]

elif section == "Risk Center":
    catalog = st.session_state.catalog_df.fillna("")
    index = st.session_state.index_df.fillna("")
    duplicated_ids = catalog[catalog["stone_id"].duplicated(keep=False) & (catalog["stone_id"] != "")]
    missing_reports = catalog[(catalog["show_in_catalog"] == True) & (catalog["report_number"] == "")]  # noqa: E712
    visible_without_ready = catalog[(catalog["show_in_catalog"] == True) & ~catalog["status"].isin(["ready", "active", "published"])]  # noqa: E712
    bad_index = index[index["carat_band_to"].astype(float) <= index["carat_band_from"].astype(float)]

    checks = [
        ("Дубли stone_id", len(duplicated_ids), duplicated_ids),
        ("Публичные камни без report_number", len(missing_reports), missing_reports),
        ("show включён, но статус не готов", len(visible_without_ready), visible_without_ready),
        ("Некорректные диапазоны ct в индексе", len(bad_index), bad_index),
    ]

    for title, count, frame in checks:
        if count:
            st.error(f"{title}: {count}")
            st.dataframe(frame, use_container_width=True, hide_index=True, height=160)
        else:
            st.success(f"{title}: 0")

elif section == "Настройки":
    st.caption("Базовые флаги MVP. Сейчас это UI-слой, без записи в backend.")
    st.text_input("API URL", value=API_URL, disabled=True)
    st.toggle("Public checkout включён", value=False, disabled=True)
    st.toggle("Mock payments", value=True, disabled=True)
    st.toggle("Request-only режим каталога", value=st.session_state.request_only, key="settings_request_only")
    st.info("Для постоянного сохранения надо добавить таблицы PostgreSQL и POST/PUT endpoints в FastAPI.")
