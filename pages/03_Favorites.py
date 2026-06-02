from __future__ import annotations

import streamlit as st

from kurgin.config import APP_NAME
from kurgin.data_io import to_csv_bytes, to_excel_bytes
from kurgin.i18n import language_selector, t
from kurgin.storage import init_db, list_favorites, remove_favorite
from kurgin.ui import inject_css, page_footer, render_catalog_table, render_logo_header

st.set_page_config(page_title=f"{APP_NAME} · Favorites", page_icon="★", layout="wide")

inject_css()
language_selector()
init_db()

render_logo_header(t("favorites_title"))

favorites = list_favorites()
if favorites.empty:
    st.info(t("empty_favorites"))
    page_footer()
    st.stop()

render_catalog_table(favorites)

st.write("")
col1, col2, col3 = st.columns([1.3, 1, 1])
with col1:
    selected_id = st.selectbox(t("select_stone"), favorites["stone_id"].astype(str).tolist())
with col2:
    if st.button(t("remove"), type="secondary"):
        remove_favorite(selected_id)
        st.toast(t("removed"), icon="✓")
        st.rerun()
with col3:
    st.download_button(
        t("download_csv"),
        data=to_csv_bytes(favorites),
        file_name="kurgin_favorites.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.download_button(
        t("download_xlsx"),
        data=to_excel_bytes(favorites),
        file_name="kurgin_favorites.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

page_footer()
