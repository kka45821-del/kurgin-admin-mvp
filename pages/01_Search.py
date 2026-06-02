from __future__ import annotations

import streamlit as st

from kurgin.config import APP_NAME
from kurgin.data_io import filter_catalog, load_sample_catalog, read_catalog, to_csv_bytes, to_excel_bytes
from kurgin.formula import score_catalog
from kurgin.i18n import language_selector, t
from kurgin.storage import add_favorite, init_db
from kurgin.ui import inject_css, metric_cards, page_footer, render_catalog_table, render_logo_header

st.set_page_config(page_title=f"{APP_NAME} · Search", page_icon="🔎", layout="wide")

inject_css()
language_selector()
init_db()

render_logo_header(t("search_title"))

uploaded = st.file_uploader(t("upload_catalog"), type=["csv", "xlsx", "xls"])
use_sample = st.toggle(t("use_sample"), value=uploaded is None)

try:
    if uploaded is not None:
        raw = read_catalog(uploaded)
    elif use_sample:
        raw = load_sample_catalog()
    else:
        raw = load_sample_catalog().head(0)
except Exception:
    st.error(t("invalid_file"))
    st.stop()

scored = score_catalog(raw)
st.session_state["current_catalog"] = scored

st.success(f"{t('catalog_loaded')}: {len(scored):,} {t('rows')}")

with st.sidebar:
    st.subheader(t("filters"))
    query = st.text_input(t("search_text"), "")
    type_options = ["All"] + sorted(scored["type"].dropna().astype(str).unique().tolist())
    availability_options = ["All"] + sorted(scored["availability"].dropna().astype(str).unique().tolist())
    stone_type = st.selectbox(t("type"), type_options)
    availability = st.selectbox(t("availability"), availability_options)
    min_score = st.slider(t("min_score"), 0, 100, 0)

filtered = filter_catalog(scored, query=query, stone_type=stone_type, availability=availability, min_score=min_score)
premium_count = int((filtered["rating"] == "Premium").sum()) if not filtered.empty else 0
metric_cards([
    (t("results"), f"{len(filtered):,}"),
    (t("premium_items"), f"{premium_count:,}"),
    (t("avg_score"), f"{filtered['kurgin_score'].mean():.1f}" if not filtered.empty else "0.0"),
])

st.write("")
render_catalog_table(filtered)

st.write("")
left, middle, right = st.columns([1.3, 1, 1])
with left:
    ids = filtered["stone_id"].astype(str).tolist() if "stone_id" in filtered.columns else []
    selected_id = st.selectbox(t("select_stone"), ids, disabled=not ids)
with middle:
    if st.button(t("add_to_favorites"), type="primary", disabled=not ids):
        record = filtered[filtered["stone_id"].astype(str) == selected_id].iloc[0]
        add_favorite(record)
        st.toast(t("favorite_added"), icon="★")
with right:
    st.download_button(
        t("download_csv"),
        data=to_csv_bytes(filtered),
        file_name="kurgin_filtered_catalog.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.download_button(
        t("download_xlsx"),
        data=to_excel_bytes(filtered),
        file_name="kurgin_filtered_catalog.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

page_footer()
