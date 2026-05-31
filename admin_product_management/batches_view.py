import pandas as pd
import streamlit as st

from admin_io import load_batches, load_stones
from admin_log import write_admin_action

from .actions import ACTIVE_BATCH_STATUSES, active_batch_mask, archive_all_active_batches, normalized_batch_status
from .exports import batch_report_parts, detail_table, excel_bytes
from .helpers import ensure_columns, safe_name


def normalize_batches_view(batches: pd.DataFrame, stones: pd.DataFrame) -> pd.DataFrame:
    counts = pd.DataFrame(columns=["batch_number", "количество камней всего"])
    if not stones.empty and "batch_number" in stones.columns:
        counts = stones.groupby("batch_number", dropna=False).size().reset_index(name="количество камней всего")
        counts["batch_number"] = counts["batch_number"].astype(str)

    result = batches.copy()
    result["batch_number"] = result["batch_number"].astype(str)
    result = result.merge(counts, on="batch_number", how="left")
    result["количество камней всего"] = result["количество камней всего"].fillna(result.get("stones_count", 0)).astype(int)
    result["статус"] = result.apply(normalized_batch_status, axis=1)
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
                st.session_state["product_batch_detail_return_menu"] = "Загруженные партии"
                st.rerun()


def render_archive_all_button(active_count: int):
    with st.expander("Dev-сброс активных партий", expanded=False):
        st.warning("Действие переместит все активные партии в Архив. Public site не меняется без отдельной публикации.")
        confirm = st.checkbox("Я понимаю, что все активные партии будут перемещены в Архив.", key="archive_all_confirm")
        if st.button("Переместить все партии в Архив", disabled=not confirm or active_count == 0, key="archive_all_batches"):
            affected_stones, affected_batches = archive_all_active_batches(note="dev cleanup archive all")
            write_admin_action(
                action="batch_archive_all",
                entity="all_active_batches",
                rows_count=affected_stones,
                source="product_management_batches",
                details=f"archived_batches={affected_batches}; non_sold_stones_removed_from_sale={affected_stones}; public site requires separate publish",
            )
            st.success("Все активные партии перемещены в Архив. Публичный сайт изменится только после отдельной публикации.")
            st.rerun()


def render_product_batches():
    st.markdown("### Загруженные партии")
    st.caption("Здесь показываются только активные партии: пустой batch_status, uploaded, active или draft.")
    batches = load_batches()
    stones = load_stones()
    if batches.empty:
        st.info("Партии пока не загружены.")
        return

    result = normalize_batches_view(batches, stones)
    cols = ["batch_number", "дата", "поставщик", "комментарий", "количество камней всего", "общая сумма покупки", "аванс", "долг", "статус"]
    result = ensure_columns(result, cols)

    active = result[result["статус"].fillna("").astype(str).str.strip().str.lower().isin(ACTIVE_BATCH_STATUSES)].copy()

    if active.empty:
        st.info("Активных загруженных партий нет.")
    else:
        st.dataframe(active[cols], use_container_width=True)
        st.markdown("#### Действия по активным партиям")
        render_batch_actions(active, cols, "active")

    render_archive_all_button(len(active))
