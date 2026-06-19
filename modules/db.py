from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import streamlit as st


@dataclass(frozen=True)
class DatabaseConfig:
    url: str
    source: str


def _secret_get(key: str, default: str = "") -> str:
    try:
        value = st.secrets.get(key, default)
    except Exception:
        value = default
    return str(value) if value is not None else default


def get_database_config() -> DatabaseConfig | None:
    """Read PostgreSQL connection config from Streamlit Secrets or environment."""
    secret_url = _secret_get("DATABASE_URL", "").strip()
    if secret_url:
        return DatabaseConfig(url=secret_url, source="Streamlit Secrets")

    env_url = os.environ.get("DATABASE_URL", "").strip()
    if env_url:
        return DatabaseConfig(url=env_url, source="Environment")

    return None


def mask_database_url(url: str) -> str:
    if not url:
        return ""
    try:
        from urllib.parse import urlsplit, urlunsplit

        parts = urlsplit(url)
        netloc = parts.netloc
        if "@" in netloc:
            auth, host = netloc.rsplit("@", 1)
            if ":" in auth:
                user, _secret = auth.split(":", 1)
                netloc = f"{user}:***@{host}"
            else:
                netloc = f"***@{host}"
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        return "***masked***"


def test_database_connection() -> dict[str, Any]:
    config = get_database_config()
    if config is None:
        return {
            "ok": False,
            "configured": False,
            "source": "",
            "masked_url": "",
            "error": "DATABASE_URL не найден.",
            "server_version": "",
            "database": "",
            "user": "",
            "current_schema": "",
        }

    try:
        import psycopg
    except Exception as exc:
        return {
            "ok": False,
            "configured": True,
            "source": config.source,
            "masked_url": mask_database_url(config.url),
            "error": f"psycopg не импортируется: {exc}",
            "server_version": "",
            "database": "",
            "user": "",
            "current_schema": "",
        }

    try:
        with psycopg.connect(config.url, connect_timeout=10) as conn:
            with conn.cursor() as cur:
                cur.execute("select version(), current_database(), current_user, current_schema()")
                version, database, user, schema = cur.fetchone()
        return {
            "ok": True,
            "configured": True,
            "source": config.source,
            "masked_url": mask_database_url(config.url),
            "error": "",
            "server_version": str(version),
            "database": str(database),
            "user": str(user),
            "current_schema": str(schema),
        }
    except Exception as exc:
        return {
            "ok": False,
            "configured": True,
            "source": config.source,
            "masked_url": mask_database_url(config.url),
            "error": str(exc),
            "server_version": "",
            "database": "",
            "user": "",
            "current_schema": "",
        }
