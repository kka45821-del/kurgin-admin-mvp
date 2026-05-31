import json

import streamlit as st

from admin_page_settings import load_settings, save_settings
from admin_price_index_matrix import render_price_index_matrix


def render_price_management_page() -> None:
    st.markdown("### Управление ценами")
    st.caption("Публичное отображение цен, матричный индекс USD/ct и будущий пересчёт цен по индексу.")

    settings = load_settings()
    commerce = settings.setdefault("commerce", {"public_prices_request_only": False})

    current = bool(commerce.get("public_prices_request_only", False))
    st.markdown("#### Публичный режим цен")
    st.info(
        "Если включено, на сайте все публичные цены будут показаны как «по запросу». "
        "Внутри админки цены и расчёты сохраняются."
    )

    commerce["public_prices_request_only"] = st.checkbox(
        "Показывать все публичные цены как «по запросу»",
        value=current,
        key="price_management_public_prices_request_only",
    )

    if commerce["public_prices_request_only"]:
        st.warning("Публичный сайт будет показывать цены как «по запросу». Публичные price-поля будут замаскированы при публикации catalog.json.")
    else:
        st.success("Публичный сайт будет показывать подтверждённые публичные цены, если они больше 0 и разрешены правилами публикации.")

    if st.button("Сохранить режим цен", type="primary"):
        save_settings(settings)
        st.success("Режим публичных цен сохранён.")

    with st.expander("Текущий JSON-фрагмент commerce", expanded=False):
        st.code(json.dumps(settings.get("commerce", {}), ensure_ascii=False, indent=2), language="json")

    st.divider()
    render_price_index_matrix()
