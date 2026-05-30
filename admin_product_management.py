from datetime import date, datetime
from io import BytesIO

import pandas as pd
import streamlit as st

from admin_io import add_batch_payment, load_batch_payments, load_batches, load_stones, save_stones
from admin_log import write_admin_action
from admin_publication_rules import number_series, public_preview, public_visible_mask, publication_summary
from admin_publish import render_publish_tab
from admin_upload import render_upload_tab


PRODUCT_MENU = [
    "Загрузка",
    "Установить цену",
    "Опубликовать",
    "Загруженные партии",
    "Редактирование",
    "Состояние",
    "Все камни",
]


def bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y", "да"])


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = df.copy()
    for col in columns:
        if col not in result.columns:
            result[col] = ""
    return result


def rub(value) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0
    return f"{amount:,.0f} ₽".replace(",", " ")


def excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            safe_sheet_name = str(sheet_name)[:31] or "Sheet"
            df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
    return out.getvalue()


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(value))[:80]


def batch_metadata(batch_number: str, batches: pd.DataFrame) -> dict:
    if batches.empty or "batch_number" not in batches.columns:
        return {}
    rows = batches[batches["batch_number"].astype(str).eq(str(batch_number))]
    if rows.empty:
        return {}
    return rows.iloc[0].to_dict()


def batch_payment_rows(batch_number: str) -> pd.DataFrame:
    payments = load_batch_payments()
    if payments.empty or "batch_number" not in payments.columns:
        return pd.DataFrame(columns=["batch_number", "payment_date", "amount_rub", "note", "created_at"])
    return payments[payments["batch_number"].astype(str).eq(str(batch_number))].copy()


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


def render_product_upload():
    st.markdown("### Загрузка")
    st.caption("Excel содержит параметры камня, не финальную цену. Финальная цена задаётся отдельно после проверки.")
    render_upload_tab(allow_replace=False, show_next_to_pricing=True)


def render_product_pricing_placeholder():
    st.markdown("### Установить цену")
    st.caption("Отдельный экран после загрузки. Pricing engine в этой задаче не реализуется.")
    st.info("Excel содержит параметры камней, цена устанавливается отдельно на основе Index table в админке.")

    last_batch = st.session_state.get("product_management_last_batch")
    if not last_batch:
        st.info("Сначала загрузите и сохраните партию в разделе Загрузка.")
        return

    st.markdown("#### Последняя загруженная партия")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Номер партии", last_batch.get("batch_number", ""))
    c2.metric("Дата загрузки", last_batch.get("upload_date", ""))
    c3.metric("Поставщик", last_batch.get("supplier_name", ""))
    c4.metric("Камней всего", last_batch.get("stones_count", 0))
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Общая сумма покупки", rub(last_batch.get("purchase_total_rub", 0)))
    c6.metric("Аванс", rub(last_batch.get("purchase_advance_rub", 0)))
    c7.metric("Долг", rub(last_batch.get("purchase_debt_rub", 0)))
    c8.caption(f"Комментарий: {last_batch.get('notes', '') or 'not available'}")

    stones = load_stones()
    if stones.empty:
        st.info("Камни последней партии пока не найдены в Admin catalog.")
        return

    batch_number = str(last_batch.get("batch_number", ""))
    if "batch_number" in stones.columns:
        df = stones[stones["batch_number"].astype(str).eq(batch_number)].copy()
    else:
        df = pd.DataFrame()

    if df.empty:
        st.warning("Партия сохранена в session state, но строки этой партии не найдены в текущем Admin catalog.")
        return

    price = number_series(df["price_rub"]) if "price_rub" in df.columns else pd.Series(0, index=df.index)
    price_status = df["price_status"].astype(str).str.strip().str.lower() if "price_status" in df.columns else pd.Series("", index=df.index)
    price_confirmed = bool_series(df["price_confirmed"]) if "price_confirmed" in df.columns else pd.Series(False, index=df.index)
    availability_confirmed = bool_series(df["availability_confirmed"]) if "availability_confirmed" in df.columns else pd.Series(False, index=df.index)

    df["price_missing"] = price.le(0)
    df["needs_review"] = df["price_missing"] | price_status.isin(["", "missing", "needs_review", "index_pending", "index_suggested"])
    df["ready_for_publish"] = price.gt(0) & price_confirmed & availability_confirmed
    df["цена на сайте"] = price
    df["цена в режиме клиента"] = "not available"
    df["цена для ювелира"] = "not available"

    view_cols = [
        "stone_id",
        "title",
        "shape",
        "carat",
        "color",
        "clarity",
        "lab",
        "report_number",
        "price_rub",
        "цена на сайте",
        "цена в режиме клиента",
        "цена для ювелира",
        "price_status",
        "price_missing",
        "needs_review",
        "ready_for_publish",
    ]
    df = ensure_columns(df, view_cols)
    st.dataframe(df[view_cols], use_container_width=True)

    if st.button("Далее", key="product_pricing_next_to_publish"):
        st.session_state["product_management_menu"] = "Опубликовать"
        st.session_state["product_management_view"] = "main"
        st.rerun()


def render_product_publish():
    st.markdown("### Опубликовать")
    stones = load_stones()
    summary = publication_summary(stones)
    public = public_preview(stones)

    c1, c2, c3 = st.columns(3)
    c1.metric("К публикации", summary.get("visible", 0))
    c2.metric("Sellable", summary.get("sellable", 0))
    c3.metric("Blocked", summary.get("blocked", 0))

    if not public.empty and "section" in public.columns:
        st.markdown("#### Distribution by section")
        dist = public["section"].fillna("не задано").value_counts().rename_axis("section").reset_index(name="count")
        st.dataframe(dist, use_container_width=True)
    else:
        st.info("Нет публичных камней для распределения по section.")

    render_publish_tab()
    st.caption("Кнопка Далее переводит к списку партий. Она не утверждает, что публикация уже выполнена.")
    if st.button("Далее", key="product_publish_next_to_batches"):
        st.session_state["product_management_menu"] = "Загруженные партии"
        st.session_state["product_management_view"] = "main"
        st.rerun()


def batch_stones(batch_number: str) -> pd.DataFrame:
    stones = load_stones()
    if stones.empty or "batch_number" not in stones.columns:
        return pd.DataFrame()
    return stones[stones["batch_number"].astype(str).eq(str(batch_number))].copy()


def detail_table(df: pd.DataFrame, date_column_name: str) -> pd.DataFrame:
    columns = {
        "batch_number": "номер партии",
        "upload_date": date_column_name,
        "report_number": "номер сертификата",
        "shape": "огранка",
        "carat": "карат",
        "color": "цвет",
        "clarity": "чистота",
    }
    if df.empty:
        return pd.DataFrame(columns=list(columns.values()))
    result = ensure_columns(df, list(columns.keys()))
    return result[list(columns.keys())].rename(columns=columns)


def batch_report_parts(batch_number: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    batch_df = batch_stones(batch_number)
    payments = batch_payment_rows(batch_number)
    if not batch_df.empty and "current_status" in batch_df.columns:
        status = batch_df["current_status"].astype(str).str.lower()
        on_site = batch_df[~status.isin(["sold", "removed", "removed_from_sale", "unavailable", "hidden"])]
        sold = batch_df[status.eq("sold")]
        removed = batch_df[status.isin(["removed", "removed_from_sale", "unavailable", "hidden"])]
    else:
        on_site = batch_df
        sold = pd.DataFrame()
        removed = pd.DataFrame()
    return on_site, sold, removed, payments


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


def render_product_edit_placeholder():
    st.markdown("### Редактирование")
    st.info("Здесь позже будет безопасное редактирование камней, партий и статусов.")
    st.write("- массовое опасное редактирование не включено;")
    st.write("- удаление, rollback и автоматическое изменение данных не добавлены;")
    st.write("- любые изменения данных требуют отдельного задания и проверки.")


def render_table_download(label: str, df: pd.DataFrame, batch_number: str, suffix: str):
    st.download_button(
        label,
        data=excel_bytes({suffix: df}),
        file_name=f"KURGIN_{safe_name(batch_number)}_{safe_name(suffix)}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"download_{suffix}_{batch_number}",
    )


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


def render_soft_remove(batch_number: str):
    st.markdown("#### Снять партию с продажи")
    st.warning("Партия будет снята с продажи в админке. Публичный сайт изменится только после отдельной публикации.")
    confirm = st.checkbox("Подтверждаю снятие партии с продажи", key=f"remove_confirm_{batch_number}")
    if st.button("Снять партию с продажи", key=f"remove_batch_{batch_number}", disabled=not confirm):
        stones = load_stones()
        if stones.empty or "batch_number" not in stones.columns:
            st.error("Камни партии не найдены.")
            return
        batch_mask = stones["batch_number"].astype(str).eq(str(batch_number))
        status = stones.get("current_status", pd.Series("", index=stones.index)).astype(str).str.lower()
        active_mask = batch_mask & ~status.eq("sold")
        affected = int(active_mask.sum())
        stones.loc[active_mask, "show_in_catalog"] = False
        stones.loc[active_mask, "is_mvp_eligible"] = False
        stones.loc[active_mask, "current_status"] = "removed_from_sale"
        stones.loc[active_mask, "removed_from_sale_at"] = date.today().isoformat()
        save_stones(stones)
        write_admin_action(
            action="batch_soft_remove_from_sale",
            entity=str(batch_number),
            rows_count=affected,
            source="product_management_batch_detail",
            details="show_in_catalog=false; is_mvp_eligible=false; current_status=removed_from_sale; removed_from_sale_at=today. Sold stones untouched. Public site requires separate publish.",
        )
        st.success(f"Партия {batch_number} снята с продажи в Admin. Затронуто строк: {affected}. Для сайта нужен отдельный publish.")
        st.rerun()


def render_product_batch_detail(batch_number: str):
    batches = load_batches()
    meta = batch_metadata(batch_number, batches)

    if st.button("← Назад к состоянию"):
        st.session_state["product_management_view"] = "state"
        st.session_state["product_management_menu"] = "Состояние"
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


def product_state_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    stones = load_stones()
    batches = load_batches()
    if stones.empty:
        return pd.DataFrame(), pd.DataFrame()

    work = stones.copy()
    if "batch_number" not in work.columns:
        work["batch_number"] = "не задано"
    work["batch_number"] = work["batch_number"].astype(str)
    visible_mask = public_visible_mask(work)

    grouped = work.groupby("batch_number", dropna=False).size().reset_index(name="количество камней всего")
    on_site = work[visible_mask].groupby("batch_number", dropna=False).size().reset_index(name="количество на сайте")
    result = grouped.merge(on_site, on="batch_number", how="left")
    result["количество на сайте"] = result["количество на сайте"].fillna(0).astype(int)

    if "current_status" in work.columns:
        sold = work[work["current_status"].astype(str).str.lower().eq("sold")].groupby("batch_number").size().reset_index(name="количество проданных")
        reserved = work[work["current_status"].astype(str).str.lower().eq("reserved")].groupby("batch_number").size().reset_index(name="количество забронированных")
        result = result.merge(sold, on="batch_number", how="left").merge(reserved, on="batch_number", how="left")
    else:
        result["количество проданных"] = 0
        result["количество забронированных"] = 0

    for col in ["количество проданных", "количество забронированных"]:
        if col not in result.columns:
            result[col] = 0
        result[col] = result[col].fillna(0).astype(int)

    result["количество в избранных"] = 0
    result["количество в корзине"] = 0

    if not batches.empty:
        meta = batches.copy()
        meta["batch_number"] = meta["batch_number"].astype(str)
        meta = meta.rename(columns={"upload_date": "дата", "supplier_name": "имя поставщика", "notes": "комментарий"})
        result = result.merge(meta[[c for c in ["batch_number", "дата", "имя поставщика", "комментарий"] if c in meta.columns]], on="batch_number", how="left")
    else:
        result["дата"] = ""
        result["имя поставщика"] = ""
        result["комментарий"] = ""

    cols = [
        "дата",
        "имя поставщика",
        "комментарий",
        "количество камней всего",
        "количество на сайте",
        "количество проданных",
        "количество в избранных",
        "количество забронированных",
        "количество в корзине",
        "batch_number",
    ]
    result = ensure_columns(result, cols)
    return result[cols], work


def render_product_state():
    st.markdown("### Состояние")
    st.caption("sold / reserve / cart / favorites пока future-safe placeholders и не являются активной коммерческой логикой.")

    result, _ = product_state_rows()
    if result.empty:
        st.info("Камней пока нет.")
        return

    header = st.columns([1, 1, 2, 1, 1, 1, 1, 1, 1, 1])
    labels = [
        "дата",
        "имя поставщика",
        "комментарий",
        "всего",
        "на сайте",
        "продано",
        "избранное",
        "бронь",
        "корзина",
        "",
    ]
    for col, label in zip(header, labels):
        col.markdown(f"**{label}**")

    for _, row in result.iterrows():
        cols = st.columns([1, 1, 2, 1, 1, 1, 1, 1, 1, 1])
        cols[0].write(row.get("дата", ""))
        cols[1].write(row.get("имя поставщика", ""))
        cols[2].write(row.get("комментарий", ""))
        cols[3].write(row.get("количество камней всего", 0))
        cols[4].write(row.get("количество на сайте", 0))
        cols[5].write(row.get("количество проданных", 0))
        cols[6].write(row.get("количество в избранных", 0))
        cols[7].write(row.get("количество забронированных", 0))
        cols[8].write(row.get("количество в корзине", 0))
        batch_number = str(row.get("batch_number", ""))
        if cols[9].button("Подробнее", key=f"batch_detail_{batch_number}"):
            st.session_state["product_management_view"] = "batch_detail"
            st.session_state["product_detail_batch"] = batch_number
            st.rerun()


def render_product_management_page():
    left_title, right_title = st.columns([1, 4])
    with left_title:
        if st.button("← Назад", use_container_width=True):
            st.session_state["admin_return_dashboard"] = True
            st.session_state["product_management_view"] = "main"
            st.rerun()
    with right_title:
        st.subheader("Управление товаром")
        st.caption("Отдельная рабочая зона: камни, загрузка, цена, публикация, партии и состояние.")

    st.divider()

    if st.session_state.get("product_management_view") == "batch_detail":
        render_product_batch_detail(st.session_state.get("product_detail_batch", ""))
        return

    menu_col, content_col = st.columns([1, 4])
    with menu_col:
        selected = st.radio("Меню", PRODUCT_MENU, key="product_management_menu", label_visibility="collapsed")
    with content_col:
        if selected == "Загрузка":
            render_product_upload()
        elif selected == "Установить цену":
            render_product_pricing_placeholder()
        elif selected == "Опубликовать":
            render_product_publish()
        elif selected == "Загруженные партии":
            render_product_batches()
        elif selected == "Редактирование":
            render_product_edit_placeholder()
        elif selected == "Состояние":
            render_product_state()
        elif selected == "Все камни":
            render_product_all_stones()
