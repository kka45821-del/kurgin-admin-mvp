from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from kurgin.config import APP_NAME
from kurgin.data_io import read_catalog, to_csv_bytes, to_excel_bytes
from kurgin.formula import score_catalog, score_single
from kurgin.i18n import language_selector, t
from kurgin.ui import inject_css, page_footer, render_catalog_table, render_logo_header, score_badge

st.set_page_config(page_title=f"{APP_NAME} · Analyzer", page_icon="📊", layout="wide")

inject_css()
language_selector()

render_logo_header(t("analyzer_title"))

tab_manual, tab_batch = st.tabs([t("manual_analysis"), t("batch_analysis")])

with tab_manual:
    left, right = st.columns([1, 1.25], gap="large")

    with left:
        with st.form("manual_score_form"):
            stone_id = st.text_input("Stone ID", "MANUAL-001")
            stone_type = st.selectbox("Type", ["Diamond", "Emerald", "Sapphire", "Ruby", "Spinel", "Tanzanite", "Other"])
            shape = st.text_input("Shape", "Round")
            carat = st.number_input("Carat", min_value=0.01, value=1.0, step=0.05)
            color = st.text_input("Color", "F")
            clarity = st.text_input("Clarity", "VS1")
            cut = st.selectbox("Cut", ["Excellent", "Very Good", "Good", "Fair", "Poor"])
            polish = st.selectbox("Polish", ["Excellent", "Very Good", "Good", "Fair", "Poor"], index=1)
            symmetry = st.selectbox("Symmetry", ["Excellent", "Very Good", "Good", "Fair", "Poor"], index=1)
            fluorescence = st.selectbox("Fluorescence", ["None", "Faint", "Medium", "Strong", "Very Strong"])
            certificate = st.selectbox("Certificate", ["GIA", "SSEF", "Gubelin", "GRS", "IGI", "HRD", "AIGS", "Local", "None"])
            price_usd = st.number_input("Price USD", min_value=0.0, value=10000.0, step=500.0)
            availability = st.selectbox("Availability", ["Available", "Reserved", "On Memo", "Pending", "Sold"])
            submitted = st.form_submit_button(t("score"), type="primary")

    record = {
        "stone_id": stone_id,
        "type": stone_type,
        "shape": shape,
        "carat": carat,
        "color": color,
        "clarity": clarity,
        "cut": cut,
        "polish": polish,
        "symmetry": symmetry,
        "fluorescence": fluorescence,
        "certificate": certificate,
        "price_usd": price_usd,
        "availability": availability,
    }
    result = score_single(record)

    with right:
        score_badge(float(result["kurgin_score"]), str(result["rating"]))
        st.write("")
        c1, c2, c3 = st.columns(3)
        c1.metric(t("quality_score"), f"{result['quality_score']:.1f}")
        c2.metric(t("value_score"), f"{result['value_score']:.1f}")
        c3.metric(t("risk_score"), f"{result['risk_score']:.1f}")

        components = pd.DataFrame(
            {
                "component": [t("quality_score"), t("value_score"), t("risk_score")],
                "score": [result["quality_score"], result["value_score"], result["risk_score"]],
            }
        )
        fig = go.Figure(go.Bar(x=components["component"], y=components["score"]))
        fig.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=20, b=20),
            yaxis=dict(range=[0, 100], title="0-100"),
            xaxis=dict(title=""),
        )
        st.plotly_chart(fig, use_container_width=True)

with tab_batch:
    uploaded = st.file_uploader(t("upload_catalog"), type=["csv", "xlsx", "xls"], key="batch_upload")
    if uploaded is not None:
        try:
            raw = read_catalog(uploaded)
            scored = score_catalog(raw)
            render_catalog_table(scored)
            col1, col2 = st.columns(2)
            col1.download_button(
                t("download_csv"),
                data=to_csv_bytes(scored),
                file_name="kurgin_scored_catalog.csv",
                mime="text/csv",
                use_container_width=True,
            )
            col2.download_button(
                t("download_xlsx"),
                data=to_excel_bytes(scored),
                file_name="kurgin_scored_catalog.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception:
            st.error(t("invalid_file"))
    else:
        st.info(t("upload_catalog"))

page_footer()
