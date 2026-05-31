import pandas as pd
import streamlit as st

from admin_io import load_batches, load_stones

from .exports import batch_report_parts, detail_table, excel_bytes
from .helpers import ensure_columns, safe_name


ACTIVE_BATCH_STATUSES = {"", "uploaded", "active", "draft"}
ARCHIVE_BATCH_STATUSES = {"removed_from_sale", "archived"}


def batch_status_label(row: pd.Series) -> str:
    status = str(row.get("batch_status", "") or "").strip().lower()
    if status:
        return status
    upload_confirmed = str(row.get("upload_confirmed", "") or "").strip().lower()
    return "uploaded" if upload_confirmed in ["true", "1", "yes", "да"] else "draft"


def normalize_batches_view(batches: pd.DataFrame, stones: pd.DataFrame) -> pd.DataFrame:
    counts = pd.DataFrame(columns=["batch_number", "количество камней всего"])
    if not stones.empty and "batch_number" in stones.columns:
        counts = stones.groupby("batch_number", dropna=False).size().reset_index(name="количество камней всего")
        counts["batch_number"] = counts["batch_number"].astype(str)

    result = batches.copy()
    result["batch_number"] = result["batch_number"].astype(str)
    result = result.merge(counts, on="batch_number", how="left")
    result["количество камней всего"] = result["количество камней всего"].fillna(result.get("stones_count", 0)).astype(int)
    result["статус"] = result.apply(batch_status_label, axis=1)
    result = result.rename(
        columns={
            "upload_date": "дата",
            "supplier_name": "поставщик",
            "notes": "комментарий",
            "purchase_total_rub": "общая сумма покупки",
            "purchase_advance_rub": "аванс",
            "purchase_debt_rub": "долг",
        }
    )
    return result


def render_batch_actions(result: pd.DataFrame, cols: list[str], key_prefix: str):
    if result.empty:
        return
    for _, row in result.iterrows():
        batch_number = str(row.get("batch_number", ""))
        if not batch_number:
            continue
        with st.expander(f"Партия {batch_number}", expanded=False):
            st.dataframe(pd.DataFrame([row])[cols], use_container_width=True)
            on_site, sold, removed, payments = batch_report_parts(batch_number)
            report = excel_bytes(
                {
                    "Камни на сайте": detail_table(on_site, "дата загрузки на сайт"),
                    "Проданные камни": detail_table(sold, "дата продажи"),
                    "Сняты с продажи": detail_table(removed, "дата снятия с продажи"),
                    "Оплаты поставщику": payments,
                }
            )
            a, b = st.columns(2)
            a.download_button(
                "Скачать Excel",
                data=report,
                file_name=f"KURGIN_batch_{safe_name(batch_number)}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{key_prefix}_batch_download_{batch_number}",
            )
            if b.button("Подробнее", key=f"{key_prefix}_batches_detail_{batch_number}"):
                st.session_state["product_management_view"] = "batch_detail"
                st.session_state["product_detail_batch"] = batch_number
                st.rerun()


def render_product_batches():
    st.markdown("### Загруженные партии")
    batches = load_batches()
    stones = load_stones()
    if batches.empty:
        st.info("Партии пока не загружены.")
        return

    result = normalize_batches_view(batches, stones)
    cols = ["batch_number", "дата", "поставщик", "комментарий", "количество камней всего", "общая сумма покупки", "аванс", "долг", "статус"]
    result = ensure_columns(result, cols)

    status_key = result["статус"].fillna("").astype(str).str.strip().str.lower()
    active = result[status_key.isin(ACTIVE_BATCH_STATUSES)].copy()
    archived = result[status_key.isin(ARCHIVE_BATCH_STATUSES)].copy()

    st.markdown("#### Активные / загруженные партии")
    if active.empty:
        st.info("Активных загруженных партий нет.")
    else:
        st.dataframe(active[cols], use_container_width=True)
        st.markdown("#### Действия по активным партиям")
        render_batch_actions(active, cols, "active")

    st.markdown("#### Снятые с продажи / Архив")
    if archived.empty:
        st.info("Снятых с продажи или архивных партий нет.")
    else:
        st.dataframe(archived[cols], use_container_width=True)
        st.markdown("#### Действия по архивным партиям")
        render_batch_actions(archived, cols, "archive")
