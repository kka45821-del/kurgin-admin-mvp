from __future__ import annotations

import pandas as pd
import streamlit as st

from admin_pricing_shared import (
    PRICED_BATCH_SECTIONS,
    REQUEST_PRICE_STATUSES,
    bool_series,
    effective_section,
    is_colored_mask,
    is_round_mask,
    number_series,
    text_series,
)


PRICED_BATCH_CANDIDATE_COLUMNS = [
    "stone_id",
    "shape",
    "carat",
    "color",
    "clarity",
    "section",
    "karo_score",
    "current_status",
    "availability_confirmed",
    "price_rub",
    "price_status",
    "price_confirmed",
]


def priced_batch_candidate_preview(stones: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    if stones.empty:
        return pd.DataFrame(columns=PRICED_BATCH_CANDIDATE_COLUMNS), {
            "eligible_candidates": 0,
            "round_candidates": 0,
            "non_round_candidates": 0,
            "missing_score": 0,
            "already_priced": 0,
            "request_price": 0,
        }

    carat = number_series(stones, "carat")
    score = number_series(stones, "karo_score")
    section = effective_section(stones)
    current_status = text_series(stones, "current_status").str.lower()
    price = number_series(stones, "price_rub")
    price_status = text_series(stones, "price_status").str.lower()
    price_confirmed = bool_series(stones, "price_confirmed")
    availability_confirmed = bool_series(stones, "availability_confirmed")
    physically_received = bool_series(stones, "physically_received")
    checked_by_kurgin = bool_series(stones, "checked_by_kurgin")
    show_in_catalog = bool_series(stones, "show_in_catalog")
    round_mask = is_round_mask(stones)

    base_scope = (
        section.isin(PRICED_BATCH_SECTIONS)
        & (~is_colored_mask(stones))
        & carat.ge(1)
        & carat.le(5)
        & current_status.eq("available")
        & availability_confirmed
        & physically_received
        & checked_by_kurgin
        & show_in_catalog
    )
    missing_score_mask = base_scope & round_mask & score.le(0)
    eligible_mask = base_scope & ((~round_mask) | score.gt(0))
    already_priced_mask = eligible_mask & (price.gt(0) | price_confirmed)
    request_price_mask = eligible_mask & (~already_priced_mask) & (price.le(0) | price_status.isin(REQUEST_PRICE_STATUSES))

    candidates = stones.loc[eligible_mask].copy()
    if candidates.empty:
        table = pd.DataFrame(columns=PRICED_BATCH_CANDIDATE_COLUMNS)
    else:
        table = pd.DataFrame(index=candidates.index)
        for column in PRICED_BATCH_CANDIDATE_COLUMNS:
            if column in candidates.columns:
                table[column] = candidates[column]
            else:
                table[column] = ""
        table["section"] = section.loc[candidates.index]
        table["price_status"] = text_series(candidates, "price_status")
        table.loc[table["price_status"].eq("") & pd.to_numeric(table["price_rub"], errors="coerce").fillna(0).le(0), "price_status"] = "request_price"
        table = table[PRICED_BATCH_CANDIDATE_COLUMNS].sort_values(["section", "carat", "shape"], ascending=[True, False, True])

    summary = {
        "eligible_candidates": int(eligible_mask.sum()),
        "round_candidates": int((eligible_mask & round_mask).sum()),
        "non_round_candidates": int((eligible_mask & ~round_mask).sum()),
        "missing_score": int(missing_score_mask.sum()),
        "already_priced": int(already_priced_mask.sum()),
        "request_price": int(request_price_mask.sum()),
    }
    return table, summary


def render_priced_batch_candidates(stones: pd.DataFrame) -> None:
    st.markdown("#### First priced batch candidates")
    st.info("Это только подготовка первого priced batch. Данные не меняются, цены не подтверждаются, catalog.json не публикуется.")

    candidates, summary = priced_batch_candidate_preview(stones)
    m1, m2, m3 = st.columns(3)
    m1.metric("Eligible candidates", summary["eligible_candidates"])
    m2.metric("Round candidates", summary["round_candidates"])
    m3.metric("Non-Round candidates", summary["non_round_candidates"])

    m4, m5, m6 = st.columns(3)
    m4.metric("Missing score", summary["missing_score"])
    m5.metric("Already priced", summary["already_priced"])
    m6.metric("Request price", summary["request_price"])

    if candidates.empty:
        st.warning("Нет eligible candidates по строгим критериям. Проверь section, availability_confirmed, current_status и KURGIN Score для Round.")
    else:
        st.dataframe(candidates, use_container_width=True)
