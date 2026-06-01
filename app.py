import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="KURGIN Admin",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --kurgin-ink: #1c1a18;
        --kurgin-muted: #77716a;
        --kurgin-line: #e8e2d8;
        --kurgin-gold: #b08a4a;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1180px;
    }

    [data-testid="stSidebar"] {
        min-width: 300px;
        background: linear-gradient(180deg, #fbfaf7 0%, #f4efe6 100%);
        border-right: 1px solid var(--kurgin-line);
    }

    [data-testid="stSidebarNav"],
    [data-testid="collapsedControl"],
    button[kind="header"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stBaseButton-header"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
    }

    .kurgin-sidebar-title {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: .03em;
        color: var(--kurgin-ink);
        margin: 0.6rem 0 1.2rem 0;
    }

    div[role="radiogroup"] {
        width: 100%;
    }

    div[role="radiogroup"] label {
        width: 100%;
        min-width: 100%;
        box-sizing: border-box;
        background: #ffffff;
        border: 1px solid var(--kurgin-line);
        border-radius: 10px;
        padding: 14px 16px;
        margin: 10px 0;
        min-height: 56px;
        display: flex;
        align-items: center;
    }

    div[role="radiogroup"] label:hover {
        border-color: #c6a66c;
        background: #fffaf0;
    }

    div[role="radiogroup"] label p {
        font-size: 1.06rem;
        font-weight: 700;
        color: var(--kurgin-ink);
    }

    .kurgin-note {
        color: var(--kurgin-muted);
        font-size: 0.88rem;
        line-height: 1.4;
    }

    .kurgin-hero {
        border: 1px solid var(--kurgin-line);
        background: linear-gradient(135deg, #ffffff 0%, #fbf7ef 100%);
        border-radius: 16px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }

    .kurgin-hero h1 {
        color: var(--kurgin-ink);
        font-size: 1.9rem;
        margin: 0 0 4px 0;
        letter-spacing: .015em;
    }

    .kurgin-chip-row {
        display: flex;
        gap: 8px;
        margin: 10px 0 0 0;
        flex-wrap: wrap;
    }

    .kurgin-chip {
        border: 1px solid #d8c6a6;
        background: #fffaf0;
        color: #33291a;
        border-radius: 10px;
        padding: 8px 10px;
        min-width: 112px;
        font-size: .78rem;
        line-height: 1.18;
    }

    .kurgin-chip strong {
        display: block;
        font-size: .86rem;
        margin-bottom: 2px;
    }

    .kurgin-color-title {
        margin: 18px 0 6px 0;
        padding: 10px 12px;
        border: 1px solid var(--kurgin-line);
        border-left: 4px solid var(--kurgin-gold);
        border-radius: 10px;
        background: #ffffff;
        font-weight: 800;
        color: var(--kurgin-ink);
    }

    .stDataFrame, .stDataEditor {
        border-radius: 12px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown('<div class="kurgin-sidebar-title">KURGIN Admin</div>', unsafe_allow_html=True)

page = st.sidebar.radio(
    "Меню",
    [
        "Индекс таблица",
        "Камни",
        "Настройки",
    ],
    index=0,
)

st.sidebar.caption("Режим разработки: вход без пароля.")

colors = ["D", "E", "F", "G"]
clarities = ["IF", "VVS1", "VVS2", "VS1", "VS2", "SI1"]
weight_ranges = [
    "1–1.49",
    "1.5–1.99",
    "2–2.49",
    "2.5–2.99",
    "3–3.49",
    "3.5–3.99",
    "4–4.49",
    "4.5–4.99",
]
score_bands = [
    ("Elite", "98.5–100", "Элитный"),
    ("Premium", "95–98.49", "Премиальный"),
    ("High", "90–94.99", "Высокое качество"),
    ("Standard", "80–89.99", "Стандартный"),
    ("Fair", "70–79.99", "Среднее качество"),
    ("Poor", "50–69.99", "Низкое качество"),
    ("Rejected", "0–49.99", "Не рекомендуется"),
]

public_index_rows = [
    ("D", "IF", "1–1.49", 250), ("D", "IF", "1.5–1.99", 380), ("D", "IF", "2–2.49", 480),
    ("D", "VVS1", "1–1.49", 125), ("D", "VVS1", "1.5–1.99", 150), ("D", "VVS1", "2–2.49", 170), ("D", "VVS1", "2.5–2.99", 210), ("D", "VVS1", "3–3.49", 245), ("D", "VVS1", "4–4.49", 325),
    ("D", "VVS2", "1–1.49", 110), ("D", "VVS2", "1.5–1.99", 115), ("D", "VVS2", "2–2.49", 120), ("D", "VVS2", "2.5–2.99", 125), ("D", "VVS2", "3–3.49", 135), ("D", "VVS2", "3.5–3.99", 145), ("D", "VVS2", "4–4.49", 160), ("D", "VVS2", "4.5–4.99", 170),
    ("D", "VS1", "1–1.49", 100), ("D", "VS1", "1.5–1.99", 100), ("D", "VS1", "2–2.49", 105), ("D", "VS1", "2.5–2.99", 115), ("D", "VS1", "3–3.49", 125), ("D", "VS1", "3.5–3.99", 130),
    ("E", "IF", "1–1.49", 185),
    ("E", "VVS1", "1–1.49", 120), ("E", "VVS1", "1.5–1.99", 145), ("E", "VVS1", "2–2.49", 150), ("E", "VVS1", "2.5–2.99", 160), ("E", "VVS1", "3–3.49", 165),
    ("E", "VVS2", "1–1.49", 105), ("E", "VVS2", "1.5–1.99", 110), ("E", "VVS2", "2–2.49", 105), ("E", "VVS2", "2.5–2.99", 100), ("E", "VVS2", "3–3.49", 100),
    ("E", "VS1", "1–1.49", 95), ("E", "VS1", "1.5–1.99", 98), ("E", "VS1", "2–2.49", 98), ("E", "VS1", "2.5–2.99", 98), ("E", "VS1", "3–3.49", 98), ("E", "VS1", "3.5–3.99", 100), ("E", "VS1", "4–4.49", 100), ("E", "VS1", "4.5–4.99", 105),
    ("F", "IF", "1–1.49", 150), ("F", "IF", "1.5–1.99", 150),
    ("F", "VVS1", "1–1.49", 115), ("F", "VVS1", "1.5–1.99", 135), ("F", "VVS1", "2–2.49", 145), ("F", "VVS1", "2.5–2.99", 155), ("F", "VVS1", "3–3.49", 155), ("F", "VVS1", "4.5–4.99", 175),
    ("F", "VVS2", "1–1.49", 100), ("F", "VVS2", "1.5–1.99", 100), ("F", "VVS2", "2–2.49", 100), ("F", "VVS2", "2.5–2.99", 100), ("F", "VVS2", "3–3.49", 100), ("F", "VVS2", "3.5–3.99", 100), ("F", "VVS2", "4–4.49", 105), ("F", "VVS2", "4.5–4.99", 105),
    ("F", "VS1", "1–1.49", 95), ("F", "VS1", "1.5–1.99", 95), ("F", "VS1", "2–2.49", 95), ("F", "VS1", "2.5–2.99", 95), ("F", "VS1", "3–3.49", 95), ("F", "VS1", "3.5–3.99", 98), ("F", "VS1", "4–4.49", 100), ("F", "VS1", "4.5–4.99", 100),
    ("G", "VVS1", "2–2.49", 110),
    ("G", "VVS2", "3–3.49", 95),
    ("G", "VS1", "1.5–1.99", 95), ("G", "VS1", "2–2.49", 95), ("G", "VS1", "3–3.49", 95),
]


def make_color_matrix(color: str) -> pd.DataFrame:
    by_key = {(c, clarity, band): value for c, clarity, band, value in public_index_rows}
    rows = []
    for clarity in clarities:
        row = {"Clarity": clarity}
        for band in weight_ranges:
            value = by_key.get((color, clarity, band))
            row[band] = "—" if value is None else value
        rows.append(row)
    return pd.DataFrame(rows)


if page == "Индекс таблица":
    st.markdown(
        """
        <div class="kurgin-hero">
            <h1>KURGIN Index Table</h1>
            <div class="kurgin-note">Внутренняя индекс-таблица админки. Сухой скелет: без категории, без формы, без базы данных.</div>
            <div class="kurgin-chip-row">
        """
        + "".join(
            f'<div class="kurgin-chip"><strong>{name}</strong>{range_label}<br>{ru}</div>'
            for name, range_label, ru in score_bands
        )
        + """
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="kurgin-note">Все цветовые блоки раскрыты сразу. Внутри каждого блока: Clarity × реальный диапазон веса, значения = внутренний ориентир.</div>', unsafe_allow_html=True)

    for color in colors:
        st.markdown(f'<div class="kurgin-color-title">Цвет {color}</div>', unsafe_allow_html=True)
        st.data_editor(
            make_color_matrix(color),
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            key=f"index_color_{color}",
        )

    c1, c2, c3 = st.columns([1, 1, 4])
    with c1:
        st.button("Save", use_container_width=True)
    with c2:
        st.button("Reset", use_container_width=True)
    with c3:
        st.caption("Пока без сохранения в базу. Значения редактируются только на экране.")

elif page == "Камни":
    st.title("Камни")
    st.info("Раздел пока не подключён. Сейчас делаем только индекс-таблицу.")

elif page == "Настройки":
    st.title("Настройки")
    st.info("Раздел пока не подключён. Пароль и доступы добавим позже отдельным шагом.")
