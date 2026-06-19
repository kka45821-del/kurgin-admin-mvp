from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import streamlit as st

KURGIN_SCHEMA_NAME = "kurgin_admin"


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


def _connect():
    config = get_database_config()
    if config is None:
        raise RuntimeError("DATABASE_URL не найден.")
    import psycopg
    return psycopg.connect(config.url, connect_timeout=10)


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


def get_kurgin_schema_status() -> dict[str, Any]:
    """Read-only status for the dedicated KURGIN schema."""
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select exists(select 1 from information_schema.schemata where schema_name = %s)",
                    (KURGIN_SCHEMA_NAME,),
                )
                exists = bool(cur.fetchone()[0])

                table_rows = []
                if exists:
                    cur.execute(
                        """
                        select table_name
                        from information_schema.tables
                        where table_schema = %s
                        order by table_name
                        """,
                        (KURGIN_SCHEMA_NAME,),
                    )
                    table_rows = [row[0] for row in cur.fetchall()]

        return {"ok": True, "exists": exists, "schema": KURGIN_SCHEMA_NAME, "tables": table_rows, "error": ""}
    except Exception as exc:
        return {"ok": False, "exists": False, "schema": KURGIN_SCHEMA_NAME, "tables": [], "error": str(exc)}


def schema_sql_preview() -> str:
    return f"""create schema if not exists {KURGIN_SCHEMA_NAME};

create table if not exists {KURGIN_SCHEMA_NAME}.schema_migrations (
    migration_id text primary key,
    applied_at timestamptz not null default now(),
    comment text not null default ''
);

insert into {KURGIN_SCHEMA_NAME}.schema_migrations (migration_id, comment)
values ('0001_create_schema', 'Initial KURGIN Admin schema marker')
on conflict (migration_id) do nothing;
"""


def create_kurgin_schema() -> dict[str, Any]:
    """Create only the dedicated schema and a migration marker table."""
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(f"create schema if not exists {KURGIN_SCHEMA_NAME}")
                cur.execute(
                    f"""
                    create table if not exists {KURGIN_SCHEMA_NAME}.schema_migrations (
                        migration_id text primary key,
                        applied_at timestamptz not null default now(),
                        comment text not null default ''
                    )
                    """
                )
                cur.execute(
                    f"""
                    insert into {KURGIN_SCHEMA_NAME}.schema_migrations (migration_id, comment)
                    values (%s, %s)
                    on conflict (migration_id) do nothing
                    """,
                    ("0001_create_schema", "Initial KURGIN Admin schema marker"),
                )
            conn.commit()
        return {"ok": True, "schema": KURGIN_SCHEMA_NAME, "error": ""}
    except Exception as exc:
        return {"ok": False, "schema": KURGIN_SCHEMA_NAME, "error": str(exc)}
