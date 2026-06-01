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
        --kurgin-soft: #fbfaf7;
        --kurgin-gold: #b08a4a;
        --kurgin-gold-soft: #f3eadb;
    }

    .block-container {
        padding-top: 2.4rem;
        padding-bottom: 3rem;
        max-width: 1180px;
    }

    [data-testid="stSidebar"] {
        min-width: 280px;
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
    }

    .kurgin-sidebar-title {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: .03em;
        color: var(--kurgin-ink);
        margin: 0.6rem 0 1.2rem 0;
    }

    .stRadio > label {
        font-size: 0.78rem;
        color: var(--kurgin-muted);
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
        min-height: 54px;
        display: flex;
        align-items: center;
        box-shadow: 0 1px 0 rgba(30, 25, 20, .03);
    }

    div[role="radiogroup"] label:hover {
        border-color: #c6a66c;
        background: #fffaf0;
    }

    div[role="radiogroup"] label p {
        font-size: 1.04rem;
        font-weight: 700;
        color: var(--kurgin-ink);
    }

    .kurgin-note {
        color: var(--kurgin-muted);
        font-size: 0.92rem;
        line-height: 1.45;
    }

    .kurgin-hero {
        border: 1px solid var(--kurgin-line);
        background: linear-gradient(135deg, #ffffff 0%, #fbf7ef 100%);
        border-radius: 18px;
        padding: 22px 24px;
        margin-bottom: 22px;
    }

    .kurgin-hero h1 {
        color: var(--kurgin-ink);
        font-size: 2.1rem;
        margin: 0 0 6px 0;
        letter-spacing: .015em;
    }

    .kurgin-chip-row {
        display: flex;
        gap: 10px;
        margin: 12px 0 2px 0;
        flex-wrap: wrap;
    }

    .kurgin-chip {
        border: 1px solid #d8c6a6;
        background: #fffaf0;
        color: #33291a;
        border-radius: 12px;
        padding: 10px 12px;
        min-width: 126px;
        font-size: .86rem;
        line-height: 1.25;
    }

    .kurgin-chip strong {
        display: block;
        font-size: .95rem;
        margin-bottom: 2px;
    }

    .kurgin-color-title {
        margin: 26px 0 8px 0;
        padding: 12px 14px;
        border: 1px solid var(--kurgin-line);
        border-left: 4px solid var(--kurgin-gold);
        border-radius: 12px;
        background: #ffffff;
        font-weight: 800;
        color: var(--kurgin-ink);
    }

    .stDataFrame, .stDataEditor {
        border-radius: 14px;
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

colors = ["D", "E", "F", "G", "H", "I", "J"]
clarities = ["IF", "VVS1", "VVS2", "VS1", "VS2", "SI1"]
weight_ranges = ["0.30–0.49", "0.50–0.69", "0.70–0.89", "0.90–0.99", "1.00–1.49", "1.50–1.99", "2.00–2.99", "3.00+"]
score_bands = [
    ("Standard", "80–89.99", "Стандартный"),
    ("High", "90–94.99", "Высокое качество"),
    ("Premium", "95–98.49", "Премиальный"),
    ("Top", "98.5+", "Лучший диапазон"),
]

base_by_color = {
    "D": 145000,
    "E": 138000,
    "F": 130000,
    "G": 118000,
    "H": 106000,
    "I": 95000,
    "J": 84000,
}

clarity_factor = {
    "IF": 1.00,
    "VVS1": 0.95,
    "VVS2": 0.90,
    "VS1": 0.84,
    "VS2": 0.79,
    "SI1": 0.68,
}

weight_factor = {
    "0.30–0.49": 0.42,
    "0.50–0.69": 0.55,
    "0.70–0.89": 0.68,
    "0.90–0.99": 0.82,
    "1.00–1.49": 1.00,
    "1.50–1.99": 1.18,
    "2.00–2.99": 1.42,
    "3.00+": 1.74,
}


def make_color_matrix(color: str) -> pd.DataFrame:
    rows = []
    for clarity in clarities:
        row = {"Clarity": clarity}
        for weight in weight_ranges:
            value = base_by_color[color] * clarity_factor[clarity] * weight_factor[weight]
            row[weight] = int(round(value / 1000) * 1000)
        rows.append(row)
    return pd.DataFrame(rows)


if page == "Индекс таблица":
    st.markdown(
        """
        <div class="kurgin-hero">
            <h1>KURGIN Index Table</h1>
            <div class="kurgin-note">Сухой рабочий скелет внутренней индекс-таблицы. Это не публичная цена камня и не публичная витрина.</div>
            <div class="kurgin-chip-row">
                <div class="kurgin-chip"><strong>Standard</strong>80–89.99<br>Стандартный</div>
                <div class="kurgin-chip"><strong>High</strong>90–94.99<br>Высокое качество</div>
                <div class="kurgin-chip"><strong>Premium</strong>95–98.49<br>Премиальный</div>
                <div class="kurgin-chip"><strong>Top</strong>98.5+<br>Лучший диапазон</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top1, top2 = st.columns([1, 1])
    with top1:
        st.selectbox("Версия индекса", ["Draft June 2026", "Active May 2026"], index=0)
    with top2:
        st.selectbox("Категория", ["Main stones", "Small stones", "Pairs", "Side stones", "Exclusive"], index=0)

    st.markdown('<div class="kurgin-note">Все цветовые блоки раскрыты сразу. Внутри каждого блока: Clarity × диапазон веса, значения = внутренний ориентир ₽/ct.</div>', unsafe_allow_html=True)

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
        st.caption("Пока без базы данных и без пароля. Это только сухой UI-скелет таблицы.")

elif page == "Камни":
    st.title("Камни")
    st.info("Раздел пока не подключён. Сейчас меняем только внешний вид индекс-таблицы.")

elif page == "Настройки":
    st.title("Настройки")
    st.info("Раздел пока не подключён. Пароль и доступы добавим позже отдельным шагом.")
