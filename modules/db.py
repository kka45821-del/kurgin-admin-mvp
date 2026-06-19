from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import streamlit as st

KURGIN_SCHEMA_NAME = "kurgin_admin"
KURGIN_CORE_TABLES = ["stones", "shipments", "import_log", "public_exports"]


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


def core_tables_sql_preview() -> str:
    """Preview minimal durable tables for KURGIN Admin.

    These tables intentionally use a compact stable key plus JSONB payload.
    This avoids a large premature relational rewrite while still giving Admin
    persistent storage and a clean migration path.
    """
    return f"""create table if not exists {KURGIN_SCHEMA_NAME}.stones (
    stone_id text primary key,
    status text not null default 'draft',
    availability_status text not null default 'in_stock',
    catalog_section text not null default '',
    shipment_id text not null default '',
    report_number text not null default '',
    stock_number text not null default '',
    payload jsonb not null default '{{}}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists {KURGIN_SCHEMA_NAME}.shipments (
    shipment_id text primary key,
    supplier_name text not null default '',
    shipment_date text not null default '',
    payload jsonb not null default '{{}}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists {KURGIN_SCHEMA_NAME}.import_log (
    import_id text primary key,
    source_file text not null default '',
    status text not null default '',
    payload jsonb not null default '{{}}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists {KURGIN_SCHEMA_NAME}.public_exports (
    export_id bigserial primary key,
    filename text not null default 'public_stones_v1.csv',
    rows_count integer not null default 0,
    payload jsonb not null default '{{}}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_kurgin_stones_status on {KURGIN_SCHEMA_NAME}.stones(status);
create index if not exists idx_kurgin_stones_availability on {KURGIN_SCHEMA_NAME}.stones(availability_status);
create index if not exists idx_kurgin_stones_catalog_section on {KURGIN_SCHEMA_NAME}.stones(catalog_section);
create index if not exists idx_kurgin_stones_shipment on {KURGIN_SCHEMA_NAME}.stones(shipment_id);

insert into {KURGIN_SCHEMA_NAME}.schema_migrations (migration_id, comment)
values ('0002_create_core_tables', 'Create minimal durable KURGIN Admin tables')
on conflict (migration_id) do nothing;
"""


def get_core_tables_status() -> dict[str, Any]:
    """Read-only status for minimal durable KURGIN tables."""
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select table_name
                    from information_schema.tables
                    where table_schema = %s
                    order by table_name
                    """,
                    (KURGIN_SCHEMA_NAME,),
                )
                existing_tables = [row[0] for row in cur.fetchall()]

                counts = {}
                for table_name in ["stones", "shipments", "import_log", "public_exports", "schema_migrations"]:
                    if table_name in existing_tables:
                        cur.execute(f"select count(*) from {KURGIN_SCHEMA_NAME}.{table_name}")
                        counts[table_name] = int(cur.fetchone()[0])

        missing = [table for table in KURGIN_CORE_TABLES if table not in existing_tables]
        return {
            "ok": True,
            "schema": KURGIN_SCHEMA_NAME,
            "existing_tables": existing_tables,
            "missing_core_tables": missing,
            "core_ready": len(missing) == 0,
            "counts": counts,
            "error": "",
        }
    except Exception as exc:
        return {
            "ok": False,
            "schema": KURGIN_SCHEMA_NAME,
            "existing_tables": [],
            "missing_core_tables": KURGIN_CORE_TABLES,
            "core_ready": False,
            "counts": {},
            "error": str(exc),
        }


def create_core_tables() -> dict[str, Any]:
    """Create minimal durable KURGIN Admin tables. Does not migrate CSV data."""
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
                    create table if not exists {KURGIN_SCHEMA_NAME}.stones (
                        stone_id text primary key,
                        status text not null default 'draft',
                        availability_status text not null default 'in_stock',
                        catalog_section text not null default '',
                        shipment_id text not null default '',
                        report_number text not null default '',
                        stock_number text not null default '',
                        payload jsonb not null default '{{}}'::jsonb,
                        created_at timestamptz not null default now(),
                        updated_at timestamptz not null default now()
                    )
                    """
                )
                cur.execute(
                    f"""
                    create table if not exists {KURGIN_SCHEMA_NAME}.shipments (
                        shipment_id text primary key,
                        supplier_name text not null default '',
                        shipment_date text not null default '',
                        payload jsonb not null default '{{}}'::jsonb,
                        created_at timestamptz not null default now(),
                        updated_at timestamptz not null default now()
                    )
                    """
                )
                cur.execute(
                    f"""
                    create table if not exists {KURGIN_SCHEMA_NAME}.import_log (
                        import_id text primary key,
                        source_file text not null default '',
                        status text not null default '',
                        payload jsonb not null default '{{}}'::jsonb,
                        created_at timestamptz not null default now()
                    )
                    """
                )
                cur.execute(
                    f"""
                    create table if not exists {KURGIN_SCHEMA_NAME}.public_exports (
                        export_id bigserial primary key,
                        filename text not null default 'public_stones_v1.csv',
                        rows_count integer not null default 0,
                        payload jsonb not null default '{{}}'::jsonb,
                        created_at timestamptz not null default now()
                    )
                    """
                )
                cur.execute(f"create index if not exists idx_kurgin_stones_status on {KURGIN_SCHEMA_NAME}.stones(status)")
                cur.execute(f"create index if not exists idx_kurgin_stones_availability on {KURGIN_SCHEMA_NAME}.stones(availability_status)")
                cur.execute(f"create index if not exists idx_kurgin_stones_catalog_section on {KURGIN_SCHEMA_NAME}.stones(catalog_section)")
                cur.execute(f"create index if not exists idx_kurgin_stones_shipment on {KURGIN_SCHEMA_NAME}.stones(shipment_id)")
                cur.execute(
                    f"""
                    insert into {KURGIN_SCHEMA_NAME}.schema_migrations (migration_id, comment)
                    values (%s, %s)
                    on conflict (migration_id) do nothing
                    """,
                    ("0002_create_core_tables", "Create minimal durable KURGIN Admin tables"),
                )
            conn.commit()
        return {"ok": True, "schema": KURGIN_SCHEMA_NAME, "error": ""}
    except Exception as exc:
        return {"ok": False, "schema": KURGIN_SCHEMA_NAME, "error": str(exc)}
