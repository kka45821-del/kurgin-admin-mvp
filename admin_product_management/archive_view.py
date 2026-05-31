import pandas as pd
import streamlit as st

from admin_io import load_batches, load_stones
from admin_log import write_admin_action

from .actions import archive_batch_mask, permanently_delete_batch
from .exports import batch_report_parts, detail_table, excel_bytes
from .helpers import ensure_columns, safe_name


PERMANENT_DELETE_CONFIRMATION = "Я понимаю, что партия и связанные с ней камни будут удалены из Admin data навсегда."


def normalize_archive_view(batches: pd.DataFrame, stones: pd.DataFrame) -> pd.DataFrame:
    counts = pd.DataFrame(columns=["batch_number", "количество камней всего"])
    if not stones.empty and "batch_number" in stones.columns:
        counts = stones.groupby("batch_number", dropna=False).size().reset_index(name="количество камней всего")
        counts["batch_number"] = counts["batch_number"].astype(str)

    result = batches.copy()
    result["batch_number"] = result["batch_number"].astype(str)
    result = result.merge(counts, on="batch_number", how="left")
    result["количество камней всего"] = result["количество камней всего"].fillna(result.get("stones_count", 0)).astype(int)
    result = result.rename(
        columns={
            "upload_date": "дата загрузки",
            "supplier_name": "поставщик",
            "notes": "комментарий",
            "purchase_total_rub": "общая сумма покупки",
            "purchase_advance_rub": "аванс",
            "purchase_debt_rub": "долг",
        }
    )
    return result


def archive_excel(batch_number: str) -> bytes:
    on_site, sold, removed, payments = batch_report_parts(batch_number)
    return excel_bytes(
        {
            "Камни на сайте": detail_table(on_site, "дата загрузки на сайт"),
            "Проданные камни": detail_table(sold, "дата продажи"),
            "Сняты с продажи": detail_table(removed, "дата снятия с продажи"),
            "Оплаты поставщику": payments,
        }
    )


def render_archive_actions(result: pd.DataFrame, cols: list[str]):
    if result.empty:
        return

    for _, row in result.iterrows():
        batch_number = str(row.get("batch_number", ""))
        if not batch_number:
            continue

        with st.expander(f"Партия {batch_number}", expanded=False):
            st.dataframe(pd.DataFrame([row])[cols], use_container_width=True)

            a, b, c = st.columns(3)
            if a.button("Подробнее", key=f"archive_detail_{batch_number}"):
                st.session_state["product_management_view"] = "batch_detail"
                st.session_state["product_detail_batch"] = batch_number
                st.session_state["product_batch_detail_return_menu"] = "Архив"
                st.rerun()

            b.download_button(
                "Скачать Excel",
                data=archive_excel(batch_number),
                file_name=f"KURGIN_archive_batch_{safe_name(batch_number)}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"archive_download_{batch_number}",
            )

            with c:
                confirmation = st.checkbox(
                    PERMANENT_DELETE_CONFIRMATION,
                    key=f"permanent_delete_confirm_{batch_number}",
                )
                if st.button(
                    "Удалить навсегда",
                    type="secondary",
                    disabled=not confirmation,
                    key=f"permanent_delete_{batch_number}",
                ):
                    deleted_stones, deleted_batch_rows, deleted_payments = permanently_delete_batch(batch_number)
                    write_admin_action(
                        action="batch_permanent_delete",
                        entity=batch_number,
                        rows_count=deleted_stones,
                        source="product_management_archive",
                        details=(
                            f"deleted stones={deleted_stones}, batch row={deleted_batch_rows}, "
                            f"batch payments={deleted_payments}; admin_actions preserved"
                        ),
                    )
                    st.success("Партия удалена навсегда из Admin data. История действий сохранена.")
                    st.rerun()


def render_product_archive():
    st.markdown("### Архив")
    st.caption("Архивные партии не публикуются автоматически. Public site изменится только после отдельного Publish.")
    batches = load_batches()
    stones = load_stones()

    if batches.empty:
        st.info("Архив пуст.")
        return

    archived_batches = batches[archive_batch_mask(batches)].copy()
    if archived_batches.empty:
        st.info("Архив пуст.")
        return

    result = normalize_archive_view(archived_batches, stones)
    cols = [
        "batch_number",
        "дата загрузки",
        "поставщик",
        "комментарий",
        "количество камней всего",
        "archived_at",
        "archived_note",
        "общая сумма покупки",
        "аванс",
        "долг",
    ]
    result = ensure_columns(result, cols)

    st.dataframe(result[cols], use_container_width=True)
    st.markdown("#### Действия")
    render_archive_actions(result, cols)
