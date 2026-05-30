import pandas as pd
import streamlit as st

from admin_io import load_batches, load_stones

from .exports import batch_report_parts, detail_table, excel_bytes
from .helpers import ensure_columns, safe_name


def render_product_batches():
    st.markdown("### Загруженные партии")
    batches = load_batches()
    stones = load_stones()
    if batches.empty:
        st.info("Партии пока не загружены.")
        return

    counts = pd.DataFrame(columns=["batch_number", "количество камней всего"])
    if not stones.empty and "batch_number" in stones.columns:
        counts = stones.groupby("batch_number", dropna=False).size().reset_index(name="количество камней всего")
        counts["batch_number"] = counts["batch_number"].astype(str)

    result = batches.copy()
    result["batch_number"] = result["batch_number"].astype(str)
    result = result.merge(counts, on="batch_number", how="left")
    result["количество камней всего"] = result["количество камней всего"].fillna(result.get("stones_count", 0)).astype(int)
    if "upload_confirmed" in result.columns:
        result["статус"] = result["upload_confirmed"].astype(str).map(lambda value: "uploaded" if value.lower() in ["true", "1", "yes", "да"] else "draft")
    else:
        result["статус"] = "not available"
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

    cols = ["batch_number", "дата", "поставщик", "комментарий", "количество камней всего", "общая сумма покупки", "аванс", "долг", "статус"]
    result = ensure_columns(result, cols)
    st.dataframe(result[cols], use_container_width=True)

    st.markdown("#### Действия по партиям")
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
                key=f"batch_download_{batch_number}",
            )
            if b.button("Подробнее", key=f"batches_detail_{batch_number}"):
                st.session_state["product_management_view"] = "batch_detail"
                st.session_state["product_detail_batch"] = batch_number
                st.rerun()
