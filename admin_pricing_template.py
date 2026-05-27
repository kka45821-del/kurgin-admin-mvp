from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st


PRICE_TABLE_TEMPLATE_COLUMNS = [
    "section",
    "carat_band_from",
    "carat_band_to",
    "color",
    "clarity",
    "base_price_usd_per_carat",
    "is_active",
]

PRICE_TEMPLATE_BANDS = [
    (1.0, 1.5, True),
    (1.5, 2.0, True),
    (2.0, 2.5, True),
    (2.5, 3.0, True),
    (3.0, 3.5, True),
    (3.5, 4.0, True),
    (4.0, 4.5, True),
    (4.5, 5.0, True),
    (5.0, 5.01, False),
]

# Source: PRICE FOR KARO от рави.xlsx, pasted by user.
# Values are USD per carat. 0 means no price is set and Pricing Engine returns request_price.
PRICE_TEMPLATE_VALUES: dict[tuple[str, str], list[int]] = {
    ("D", "IF"): [250, 380, 480, 0, 0, 0, 0, 0, 0],
    ("D", "VVS1"): [125, 150, 170, 210, 245, 0, 325, 0, 0],
    ("D", "VVS2"): [110, 115, 120, 125, 135, 145, 160, 170, 230],
    ("D", "VS1"): [100, 100, 105, 115, 125, 130, 0, 0, 0],
    ("D", "VS2"): [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ("E", "IF"): [185, 0, 0, 0, 0, 0, 0, 0, 0],
    ("E", "VVS1"): [120, 145, 150, 160, 165, 0, 0, 0, 0],
    ("E", "VVS2"): [105, 110, 105, 100, 100, 0, 0, 0, 0],
    ("E", "VS1"): [95, 98, 98, 98, 98, 100, 100, 105, 105],
    ("E", "VS2"): [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ("F", "IF"): [150, 150, 0, 0, 0, 0, 0, 0, 0],
    ("F", "VVS1"): [115, 135, 145, 155, 155, 0, 0, 175, 170],
    ("F", "VVS2"): [100, 100, 100, 100, 100, 100, 105, 105, 102],
    ("F", "VS1"): [95, 95, 95, 95, 95, 98, 100, 100, 100],
    ("F", "VS2"): [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ("G", "IF"): [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ("G", "VVS1"): [0, 0, 110, 0, 0, 0, 0, 0, 0],
    ("G", "VVS2"): [0, 0, 0, 0, 95, 0, 0, 0, 100],
    ("G", "VS1"): [0, 95, 95, 0, 95, 0, 0, 0, 98],
    ("G", "VS2"): [0, 0, 0, 0, 0, 0, 0, 0, 0],
}


def _price_table_template_frame() -> pd.DataFrame:
    rows: list[dict] = []
    for (color, clarity), values in PRICE_TEMPLATE_VALUES.items():
        for index, value in enumerate(values):
            band_from, band_to, active_band = PRICE_TEMPLATE_BANDS[index]
            rows.append(
                {
                    "section": "",
                    "carat_band_from": band_from,
                    "carat_band_to": band_to,
                    "color": color,
                    "clarity": clarity,
                    "base_price_usd_per_carat": int(value or 0),
                    "is_active": bool(active_band),
                }
            )
    return pd.DataFrame(rows, columns=PRICE_TABLE_TEMPLATE_COLUMNS)


def price_table_template_bytes() -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        _price_table_template_frame().to_excel(writer, index=False, sheet_name="KURGIN_Price_Table")
    output.seek(0)
    return output.getvalue()


def render_price_table_template_download() -> None:
    st.markdown("#### Price table template")
    st.warning(
        "Значения в price table — USD за карат. Пустые значения заменены на 0. "
        "0 означает, что цена не задана и камень уйдёт в request_price. "
        "Итоговая цена считается Pricing Engine."
    )
    st.download_button(
        label="Скачать price table template",
        data=price_table_template_bytes(),
        file_name="kurgin_price_table_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
