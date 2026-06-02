from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st

from kurgin.config import ASSETS_DIR, DISPLAY_COLUMNS


def inject_css() -> None:
    css_path = ASSETS_DIR / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_logo_header(title: str, subtitle: str | None = None) -> None:
    logo_path = ASSETS_DIR / "logo.svg"
    if logo_path.exists():
        logo = logo_path.read_text(encoding="utf-8")
        st.markdown(
            f"""
            <div class="kurgin-header">
                <div class="kurgin-logo">{logo}</div>
                <div>
                    <h1>{title}</h1>
                    {f'<p>{subtitle}</p>' if subtitle else ''}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.title(title)
        if subtitle:
            st.caption(subtitle)


def metric_cards(items: Iterable[tuple[str, str]]) -> None:
    materialized = list(items)
    columns = st.columns(max(len(materialized), 1))
    for column, (label, value) in zip(columns, materialized):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def safe_display_columns(df: pd.DataFrame) -> list[str]:
    ordered = [column for column in DISPLAY_COLUMNS if column in df.columns]
    rest = [column for column in df.columns if column not in ordered and not column.startswith("_")]
    return ordered + rest


def render_catalog_table(df: pd.DataFrame, height: int = 520) -> None:
    display = df[safe_display_columns(df)].copy()
    column_config = {}
    if "kurgin_score" in display.columns:
        column_config["kurgin_score"] = st.column_config.ProgressColumn(
            "KURGIN Score", min_value=0, max_value=100, format="%.1f"
        )
    if "quality_score" in display.columns:
        column_config["quality_score"] = st.column_config.NumberColumn("Quality", format="%.1f")
    if "value_score" in display.columns:
        column_config["value_score"] = st.column_config.NumberColumn("Value", format="%.1f")
    if "risk_score" in display.columns:
        column_config["risk_score"] = st.column_config.NumberColumn("Reliability", format="%.1f")
    if "price_usd" in display.columns:
        column_config["price_usd"] = st.column_config.NumberColumn("Price USD", format="$%d")
    if "price_per_carat" in display.columns:
        column_config["price_per_carat"] = st.column_config.NumberColumn("$/ct", format="$%.2f")
    st.dataframe(display, use_container_width=True, height=height, column_config=column_config)


def score_badge(score: float, rating: str) -> None:
    st.markdown(
        f"""
        <div class="score-badge">
            <span>{rating}</span>
            <strong>{score:.1f}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_footer() -> None:
    st.markdown(
        '<div class="footer">KURGIN Platform MVP · No payments · Local-first</div>',
        unsafe_allow_html=True,
    )
