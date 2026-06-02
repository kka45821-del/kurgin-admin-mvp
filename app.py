from __future__ import annotations

import pandas as pd
import streamlit as st

from kurgin.config import APP_NAME
from kurgin.data_io import load_sample_catalog
from kurgin.formula import score_catalog, score_summary
from kurgin.i18n import language_selector, t
from kurgin.ui import inject_css, metric_cards, page_footer, render_catalog_table, render_logo_header

st.set_page_config(page_title=APP_NAME, page_icon="💎", layout="wide")

inject_css()
language_selector()

render_logo_header(t("home_title"), t("home_subtitle"))

st.markdown(
    f"""
    <span class="status-pill">✓ {t("status_no_payments")}</span>
    <span class="status-pill">✓ {t("status_local_storage")}</span>
    <span class="status-pill">✓ {t("status_ready_repo")}</span>
    """,
    unsafe_allow_html=True,
)

st.write("")

sample = score_catalog(load_sample_catalog())
summary = score_summary(sample)

metric_cards([
    (t("stones"), f"{summary['count']:,}"),
    (t("avg_score"), f"{summary['avg_score']:.1f}"),
    (t("premium_items"), f"{summary['premium']:,}"),
    (t("median_ppc"), f"${summary['median_ppc']:,.0f}"),
])

st.write("")
left, right = st.columns([1, 1], gap="large")
with left:
    st.subheader(t("sample_overview"))
    top = sample.sort_values("kurgin_score", ascending=False).head(8)
    render_catalog_table(top, height=330)

with right:
    st.subheader(t("architecture"))
    st.markdown(
        """
        - **Streamlit UI** for fast deployment.
        - **Pandas scoring engine** isolated in `kurgin/formula.py`.
        - **SQLite favorites** in local app storage.
        - **CSV/XLSX import/export** without payment services.
        - **RU/EN interface** using lightweight translation dictionaries.
        """
    )
    st.code("python -m streamlit run app.py", language="bash")

st.write("")
col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/01_Search.py", label=t("open_search"), icon="🔎")
with col2:
    st.page_link("pages/02_Analyzer.py", label=t("open_analyzer"), icon="📊")
with col3:
    st.page_link("pages/03_Favorites.py", label=t("open_favorites"), icon="★")

st.info(t("disclaimer"))
page_footer()
