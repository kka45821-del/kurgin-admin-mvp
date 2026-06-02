from __future__ import annotations

import streamlit as st

from kurgin.config import APP_NAME, CANONICAL_COLUMNS
from kurgin.data_io import empty_template, load_sample_catalog, read_catalog, to_csv_bytes
from kurgin.i18n import language_selector, t
from kurgin.ui import inject_css, page_footer, render_catalog_table, render_logo_header
from kurgin.validators import issues_to_frame, validate_catalog

st.set_page_config(page_title=f"{APP_NAME} · Data Quality", page_icon="✅", layout="wide")

inject_css()
language_selector()

render_logo_header(t("quality_title"))

uploaded = st.file_uploader(t("upload_catalog"), type=["csv", "xlsx", "xls"], key="quality_upload")
use_sample = st.toggle(t("use_sample"), value=uploaded is None)

try:
    raw = read_catalog(uploaded) if uploaded is not None else load_sample_catalog()
except Exception:
    st.error(t("invalid_file"))
    st.stop()

issues = validate_catalog(raw)
issue_frame = issues_to_frame(issues)

if issue_frame.empty:
    st.success(t("no_data_issues"))
else:
    st.subheader(t("data_issues"))
    st.dataframe(issue_frame, use_container_width=True, hide_index=True)

st.subheader(t("template_columns"))
template = empty_template()
st.dataframe(template, use_container_width=True, hide_index=True)
st.download_button(
    "Download template CSV",
    data=to_csv_bytes(template),
    file_name="kurgin_import_template.csv",
    mime="text/csv",
)

st.subheader("Preview")
render_catalog_table(raw, height=360)

page_footer()
