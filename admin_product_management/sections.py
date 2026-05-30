import pandas as pd
import streamlit as st

from admin_io import load_stones
from admin_publication_rules import public_preview

from .helpers import ensure_columns


def product_public_table() -> pd.DataFrame:
    stones = load_stones()
    if stones.empty:
        return pd.DataFrame()
    public = public_preview(stones)
    if public.empty:
        return pd.DataFrame()

    result = public.copy()
    result["KURGIN Score"] = result.get("karo_score", "")
    if "public_action" in result.columns:
        result["public_status"] = result["public_action"].astype(str)
    elif "public_sellable" in result.columns:
        result["public_status"] = result["public_sellable"].map({True: "ready_for_checkout", False: "request_price"})
    else:
        result["public_status"] = "ready_for_publish"

    columns = [
        "stone_id",
        "title",
        "shape",
        "carat",
        "color",
        "clarity",
        "lab",
        "report_number",
        "KURGIN Score",
        "section",
        "price_status",
        "price_rub",
        "show_in_catalog",
        "current_status",
        "public_status",
    ]
    result = ensure_columns(result, columns)
    return result[columns]


def render_product_all_stones():
    st.markdown("### Все камни")
    st.caption("Общий Excel-like view всех камней. Массовое опасное редактирование на этом этапе не включено.")
    stones = load_stones()
    if stones.empty:
        st.info("Камней пока нет.")
        return

    result = stones.copy()
    result["KURGIN Score"] = result.get("karo_score", "")
    public = public_preview(stones)
    public_ids = set(public["stone_id"].astype(str)) if not public.empty and "stone_id" in public.columns else set()
    result["public_status"] = result.get("stone_id", pd.Series("", index=result.index)).astype(str).map(
        lambda value: "public_preview" if value in public_ids else "not_public"
    )
    result["site_price_rub"] = result.get("price_rub", "")
    result["client_mode_price_rub"] = "not available"
    result["jeweler_price_rub"] = "not available"

    tag_cols = [col for col in result.columns if str(col).lower().startswith("tag")]
    columns = [
        "stone_id",
        "batch_number",
        "supplier_name",
        "upload_date",
        "title",
        "shape",
        "carat",
        "color",
        "clarity",
        "lab",
        "report_number",
        "section",
        "KURGIN Score",
        "site_price_rub",
        "client_mode_price_rub",
        "jeweler_price_rub",
        "price_status",
        "current_status",
        "public_status",
    ] + tag_cols
    result = ensure_columns(result, columns)
    st.dataframe(result[columns], use_container_width=True)


def render_product_edit_placeholder():
    st.markdown("### Редактирование")
    st.info("Здесь позже будет безопасное редактирование камней, партий и статусов.")
    st.write("- массовое опасное редактирование не включено;")
    st.write("- удаление, rollback и автоматическое изменение данных не добавлены;")
    st.write("- любые изменения данных требуют отдельного задания и проверки.")
