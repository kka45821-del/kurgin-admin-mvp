from datetime import date, datetime

import pandas as pd
import streamlit as st

from admin_io import add_batch_payment, load_batches, load_stones, save_batches, save_stones
from admin_log import write_admin_action

from .exports import batch_report_parts, detail_table, excel_bytes, render_table_download
from .helpers import batch_metadata, rub, safe_name
from .payments import batch_payment_rows


def render_batch_finance(batch_number: str, meta: dict):
    payments = batch_payment_rows(batch_number)
    paid_extra = float(pd.to_numeric(payments["amount_rub"], errors="coerce").fillna(0).sum()) if not payments.empty else 0.0
    total = float(meta.get("purchase_total_rub", 0) or 0)
    advance = float(meta.get("purchase_advance_rub", 0) or 0)
    remaining = total - advance - paid_extra

    st.markdown("#### Финансы партии")
    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Общая сумма покупки", rub(total))
    f2.metric("Аванс", rub(advance))
    f3.metric("Дополнительные оплаты", rub(paid_extra))
    f4.metric("Остаток", rub(remaining))

    st.markdown("#### Оплаты")
    if payments.empty:
        st.info("Дополнительных оплат пока нет.")
    else:
        st.dataframe(payments, use_container_width=True)

    with st.expander("Добавить оплату", expanded=False):
        st.caption("Внутренняя оплата поставщику. Это не клиентская оплата, не checkout и не payment session.")
        payment_date = st.date_input("Дата оплаты", value=date.today(), key=f"payment_date_{batch_number}")
        amount = st.number_input("Сумма оплаты", min_value=0.0, value=0.0, step=1000.0, key=f"payment_amount_{batch_number}")
        note = st.text_input("Комментарий / заметка", key=f"payment_note_{batch_number}")
        if st.button("Сохранить оплату", key=f"payment_save_{batch_number}", disabled=amount <= 0):
            add_batch_payment(batch_number, payment_date, amount, note, datetime.now().isoformat(timespec="seconds"))
            write_admin_action(
                action="batch_supplier_payment_add",
                entity=str(batch_number),
                rows_count=1,
                source="product_management_batch_detail",
                details=f"Internal supplier payment amount_rub={amount}; note={note}",
            )
            st.success("Оплата добавлена. Остаток будет пересчитан.")
            st.rerun()


def _ensure_soft_remove_columns(stones: pd.DataFrame) -> pd.DataFrame:
    result = stones.copy()
    defaults = {
        "show_in_catalog": True,
        "is_mvp_eligible": True,
        "current_status": "available",
        "removed_from_sale_at": "",
    }
    for column, default in defaults.items():
        if column not in result.columns:
            result[column] = default
    return result


def _mark_batch_removed_from_sale(batch_number: str, today: str) -> bool:
    batches = load_batches()
    if batches.empty or "batch_number" not in batches.columns:
        return False

    for column in ["batch_status", "removed_from_sale_at", "removed_from_sale_note"]:
        if column not in batches.columns:
            batches[column] = ""

    batch_mask = batches["batch_number"].astype(str).eq(str(batch_number))
    if not bool(batch_mask.any()):
        return False

    batches.loc[batch_mask, "batch_status"] = "removed_from_sale"
    batches.loc[batch_mask, "removed_from_sale_at"] = today
    batches.loc[batch_mask, "removed_from_sale_note"] = "removed from sale in admin"
    save_batches(batches)
    return True


def render_soft_remove(batch_number: str):
    st.markdown("#### Снять партию с продажи")
    st.warning("Партия будет снята с продажи в админке. Публичный сайт изменится только после отдельной публикации.")
    confirm = st.checkbox("Подтверждаю снятие партии с продажи", key=f"remove_confirm_{batch_number}")
    if st.button("Снять партию с продажи", key=f"remove_batch_{batch_number}", disabled=not confirm):
        stones = load_stones()
        if stones.empty or "batch_number" not in stones.columns:
            st.error("Камни партии не найдены.")
            return

        stones = _ensure_soft_remove_columns(stones)
        batch_mask = stones["batch_number"].astype(str).eq(str(batch_number))
        status = stones["current_status"].fillna("").astype(str).str.strip().str.lower()
        sold_mask = status.eq("sold")
        active_mask = (batch_mask & ~sold_mask).reindex(stones.index, fill_value=False).fillna(False).astype(bool)
        active_indexes = stones.index[active_mask]
        affected = int(len(active_indexes))

        if affected == 0:
            st.warning("Нет активных камней для снятия с продажи.")
            return

        today = date.today().isoformat()
        stones.loc[active_indexes, "show_in_catalog"] = False
        stones.loc[active_indexes, "is_mvp_eligible"] = False
        stones.loc[active_indexes, "current_status"] = "removed_from_sale"
        stones.loc[active_indexes, "removed_from_sale_at"] = today
        save_stones(stones)

        batch_marked = _mark_batch_removed_from_sale(batch_number, today)
        if not batch_marked:
            st.warning("Камни сняты с продажи, но строка партии в upload_batches.csv не найдена.")

        write_admin_action(
            action="batch_soft_remove_from_sale",
            entity=str(batch_number),
            rows_count=affected,
            source="product_management_batch_detail",
            details="show_in_catalog=false; is_mvp_eligible=false; current_status=removed_from_sale; removed_from_sale_at=today; batch_status=removed_from_sale if batch row exists. Sold stones untouched. Public site requires separate publish.",
        )
        st.success("Партия снята с продажи в админке и перемещена в архив. Публичный сайт изменится только после отдельной публикации.")
        st.rerun()


def render_product_batch_detail(batch_number: str):
    batches = load_batches()
    meta = batch_metadata(batch_number, batches)

    if st.button("← Назад к состоянию"):
        st.session_state["product_management_view"] = "state"
        st.session_state["product_management_next_menu"] = "Состояние"
        st.rerun()

    st.markdown(f"### Партия {batch_number}")
    st.caption(
        f"Дата: {meta.get('upload_date', 'not available')} · "
        f"Поставщик: {meta.get('supplier_name', 'not available')} · "
        f"Комментарий: {meta.get('notes', 'not available')}"
    )

    render_batch_finance(batch_number, meta)

    on_site, sold, removed, payments = batch_report_parts(batch_number)
    full_report = excel_bytes(
        {
            "Камни на сайте": detail_table(on_site, "дата загрузки на сайт"),
            "Проданные камни": detail_table(sold, "дата продажи"),
            "Сняты с продажи": detail_table(removed, "дата снятия с продажи"),
            "Оплаты поставщику": payments,
        }
    )
    st.download_button(
        "Скачать полный Excel-отчёт партии",
        data=full_report,
        file_name=f"KURGIN_batch_report_{safe_name(batch_number)}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"full_report_{batch_number}",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### Камни на сайте / продаются ещё")
        table = detail_table(on_site, "дата загрузки на сайт")
        st.dataframe(table, use_container_width=True)
        render_table_download("Скачать Excel", table, batch_number, "Камни_на_сайте")
    with col2:
        st.markdown("#### Проданные камни")
        table = detail_table(sold, "дата продажи")
        st.dataframe(table, use_container_width=True)
        render_table_download("Скачать Excel", table, batch_number, "Проданные")
    with col3:
        st.markdown("#### Сняты с продажи")
        table = detail_table(removed, "дата снятия с продажи")
        st.dataframe(table, use_container_width=True)
        render_table_download("Скачать Excel", table, batch_number, "Сняты_с_продажи")

    render_soft_remove(batch_number)
