from __future__ import annotations

import streamlit as st

from kurgin.config import APP_NAME, APP_VERSION, PAYMENTS_ENABLED
from kurgin.i18n import language_selector, t
from kurgin.ui import inject_css, page_footer, render_logo_header

st.set_page_config(page_title=f"{APP_NAME} · Info", page_icon="ℹ️", layout="wide")

inject_css()
language_selector()

render_logo_header(t("info_title"))

st.subheader(t("architecture"))
st.markdown(
    f"""
    **Version:** `{APP_VERSION}`  
    **Payments enabled:** `{PAYMENTS_ENABLED}`

    {t("payments_disabled_text")}

    {t("storage_text")}
    """
)

st.subheader(t("run_command"))
st.code("python -m streamlit run app.py", language="bash")

st.subheader("Repository structure")
st.code(
    """
app.py
pages/
kurgin/
translations_lang/
assets/
data/
tests/
docs/
.streamlit/
requirements.txt
README.md
    """.strip(),
    language="text",
)

st.warning(t("disclaimer"))

page_footer()
