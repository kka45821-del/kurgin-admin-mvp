from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pandas as pd
import streamlit as st

from admin_io import BATCH_COLS, STONE_COLS, load_batches, load_stones
from admin_log import write_admin_action
from admin_publication_rules import public_preview
from admin_publish import DATA_REPO, _df_to_csv, _publish_file, _token, publish_catalog_snapshot

REMOTE_CATALOG_SOURCES = [
    {
        "name": "catalog.json",
        "path": "catalog.json",
        "url": "https://raw.githubusercontent.com/kka45821-del/kurgin-data/main/catalog.json",
        "site_order": 1,
    },
    {
        "name": "stones.json",
        "path": "stones.json",
        "url": "https://raw.githubusercontent.com/kka45821-del/kurgin-data/main/stones.json",
        "site_order": 2,
    },
    {
        "name": "catalog_published.json",
        "path": "catalog_published.json",
        "url": "https://raw.githubusercontent.com/kka45821-del/kurgin-data/main/catalog_published.json",
        "site_order": 3,
    },
    {
        "name": "data/catalog.json",
        "path": "data/catalog.json",
        "url": "https://raw.githubusercontent.com/kka45821-del/kurgin-data/main/data/catalog.json",
        "site_order": 4,
    },
]


def _load_json_url(url: str) -> dict | list:
    with urlopen(url, timeout=8) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw)


def _extract_stones(payload) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    stones = payload.get("stones")
    if isinstance(stones, list):
        return [row for row in stones if isinstance(row, dict)]
    data = payload.get("data")
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict) and isinstance(data.get("stones"), list):
        return [row for row in data["stones"] if isinstance(row, dict)]
    return []


def _stone_id(row: dict) -> str:
    for key in ("stone_id", "id", "stock", "stock_id", "sku"):
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _ids_from_stones(stones: list[dict]) -> set[str]:
    return {stone_id for stone_id in (_stone_id(row) for row in stones) if stone_id}


def _empty_catalog_payload() -> str:
    payload = {
        "source": "KURGIN Admin",
        "updated_at": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": 0,
        "schema": {
            "version": "catalog_mvp_v2",
            "score_public_name": "KURGIN Score",
            "score_field": "karo_score",
            "includes_full_catalog_fields": True,
            "section_autofill": True,
        },
        "stones": [],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def local_public_state() -> dict:
    stones = load_stones()
    public = public_preview(stones)
    local_ids = set()
    if not public.empty and "stone_id" in public.columns:
        local_ids = {str(value).strip() for value in public["stone_id"].tolist() if str(value).strip()}
    return {
        "stones_total": int(len(stones)),
        "public_total": int(len(public)),
        "public_ids": local_ids,
        "public_df": public,
    }


def remote_catalog_states() -> list[dict]:
    result = []
    for source in REMOTE_CATALOG_SOURCES:
        state = {
            "name": source["name"],
            "path": source["path"],
            "url": source["url"],
            "site_order": source["site_order"],
            "status": "unknown",
            "count": 0,
            "ids": set(),
            "updated_at": "",
            "error": "",
        }
        try:
            payload = _load_json_url(source["url"])
            stones = _extract_stones(payload)
            state["status"] = "loaded"
            state["count"] = len(stones)
            state["ids"] = _ids_from_stones(stones)
            if isinstance(payload, dict):
                state["updated_at"] = str(payload.get("updated_at") or "")
        except HTTPError as exc:
            if exc.code == 404:
                state["status"] = "missing"
                state["error"] = "404 not found"
            else:
                state["status"] = "error"
                state["error"] = f"HTTP {exc.code}: {exc.reason}"
        except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            state["status"] = "error"
            state["error"] = str(exc)
        result.append(state)
    return result


def active_site_state(remote_states: list[dict]) -> dict:
    for state in sorted(remote_states, key=lambda row: row["site_order"]):
        if state["status"] == "loaded" and state["count"] > 0:
            return state
    for state in sorted(remote_states, key=lambda row: row["site_order"]):
        if state["status"] == "loaded":
            return state
    return {
        "name": "none",
        "path": "",
        "url": "",
        "site_order": 0,
        "status": "none",
        "count": 0,
        "ids": set(),
        "updated_at": "",
        "error": "",
    }


def compare_sync(local: dict, remote_states: list[dict]) -> dict:
    active = active_site_state(remote_states)
    local_ids = local["public_ids"]
    remote_ids = active.get("ids", set())
    non_primary_non_empty = [
        state["name"]
        for state in remote_states
        if state["name"] not in {"catalog.json", "data/catalog.json"}
        and state["status"] == "loaded"
        and state["count"] > 0
    ]
    return {
        "active": active,
        "local_only": sorted(local_ids - remote_ids),
        "remote_only": sorted(remote_ids - local_ids),
        "same_ids": local_ids == remote_ids,
        "non_primary_non_empty": non_primary_non_empty,
        "is_synced": local_ids == remote_ids and not non_primary_non_empty,
    }


def clear_public_site_snapshot(source: str = "admin_site_sync", details: str = "clear public site") -> dict:
    token = _token()
    if not token:
        raise RuntimeError("GITHUB_TOKEN не задан. Нельзя автоматически очистить сайт.")

    empty_catalog = _empty_catalog_payload()
    empty_stones_csv = _df_to_csv(pd.DataFrame(columns=STONE_COLS), STONE_COLS)
    empty_batches_csv = _df_to_csv(pd.DataFrame(columns=BATCH_COLS), BATCH_COLS)
    steps = [
        ("catalog.json", lambda: _publish_file(DATA_REPO, "catalog.json", empty_catalog, f"Clear catalog.json from {source}", token)),
        ("data/catalog.json", lambda: _publish_file(DATA_REPO, "data/catalog.json", empty_catalog, f"Clear data/catalog.json from {source}", token)),
        ("stones.csv", lambda: _publish_file(DATA_REPO, "stones.csv", empty_stones_csv, f"Clear stones.csv from {source}", token)),
        ("upload_batches.csv", lambda: _publish_file(DATA_REPO, "upload_batches.csv", empty_batches_csv, f"Clear upload_batches.csv from {source}", token)),
    ]
    failed_step = ""
    try:
        for step_name, action in steps:
            failed_step = step_name
            action()
    except Exception as exc:
        write_admin_action(
            action="clear_public_site_catalog",
            entity="kurgin-data/catalog.json",
            rows_count=0,
            source=source,
            result="error",
            details=f"failed_step={failed_step}; {details}; error={exc}",
        )
        raise

    write_admin_action(
        action="clear_public_site_catalog",
        entity="kurgin-data/catalog.json",
        rows_count=0,
        source=source,
        result="success",
        details=details,
    )
    return {"count": 0, "updated_at": json.loads(empty_catalog)["updated_at"]}


def _remote_table(remote_states: list[dict]) -> pd.DataFrame:
    rows = []
    for state in remote_states:
        rows.append(
            {
                "источник сайта": state["name"],
                "порядок чтения": state["site_order"],
                "статус": state["status"],
                "камней": state["count"],
                "updated_at": state["updated_at"],
                "ошибка": state["error"],
            }
        )
    return pd.DataFrame(rows)


def render_site_sync_page() -> None:
    st.subheader("Синхронизация сайта")
    st.caption(
        "Контрольный экран между Admin data и публичным каталогом. "
        "Здесь видно, что именно увидит сайт и совпадает ли это с текущей админкой."
    )

    local = local_public_state()
    remote_states = remote_catalog_states()
    sync = compare_sync(local, remote_states)
    active = sync["active"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Камней в админке", local["stones_total"])
    c2.metric("К публикации из админки", local["public_total"])
    c3.metric("Камней на сайте", active.get("count", 0))
    c4.metric("Источник сайта", active.get("name", "none"))

    if sync["is_synced"]:
        st.success("Админка и сайт синхронизированы по публичным stone_id.")
    else:
        st.error("Есть расхождение между админкой и сайтом.")

    st.markdown("#### Источники, которые проверяет сайт")
    st.dataframe(_remote_table(remote_states), use_container_width=True)

    if sync["non_primary_non_empty"]:
        st.warning(
            "Найдены непустые запасные источники сайта: " + ", ".join(sync["non_primary_non_empty"]) + ". "
            "Их нужно очистить или удалить, иначе сайт может показать старые камни."
        )

    with st.expander("Расхождения по stone_id", expanded=not sync["is_synced"]):
        left, right = st.columns(2)
        left.markdown("**Есть в админке, нет на сайте**")
        left.dataframe(pd.DataFrame({"stone_id": sync["local_only"]}), use_container_width=True)
        right.markdown("**Есть на сайте, нет в админке**")
        right.dataframe(pd.DataFrame({"stone_id": sync["remote_only"]}), use_container_width=True)

    st.divider()
    st.markdown("#### Действия синхронизации")

    publish_confirm = st.checkbox(
        "Подтверждаю: опубликовать текущее состояние админки на сайт",
        key="site_sync_publish_confirm",
    )
    if st.button("Опубликовать текущую админку на сайт", type="primary", disabled=not publish_confirm):
        try:
            result = publish_catalog_snapshot(source="admin_site_sync", details="manual sync from site sync page")
            st.success(f"Сайт обновлён. В публичном каталоге: {result.get('count', 0)} камней.")
            st.rerun()
        except Exception as exc:
            st.error(f"Не удалось опубликовать сайт: {exc}")

    clear_confirm = st.checkbox(
        "Подтверждаю: очистить публичный каталог сайта, не трогая локальные данные админки",
        key="site_sync_clear_confirm",
    )
    if st.button("Очистить сайт", type="secondary", disabled=not clear_confirm):
        try:
            result = clear_public_site_snapshot(details="manual clear from site sync page")
            st.success(f"Публичный каталог очищен. На сайте должно быть: {result.get('count', 0)} камней.")
            st.rerun()
        except Exception as exc:
            st.error(f"Не удалось очистить сайт: {exc}")

    if st.button("Перепроверить синхронизацию"):
        st.rerun()
