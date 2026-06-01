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
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1280px;
    }
    [data-testid="stSidebar"] {
        min-width: 260px;
    }
    .kurgin-note {
        color: #666;
        font-size: 0.92rem;
        line-height: 1.45;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("KURGIN Admin")

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

default_values = {
    "IF": [145000, 138000, 130000, 118000, 106000, 95000, 84000],
    "VVS1": [138000, 132000, 124000, 112000, 101000, 91000, 80000],
    "VVS2": [130000, 124000, 117000, 106000, 96000, 86000, 76000],
    "VS1": [122000, 116000, 110000, 100000, 90000, 81000, 72000],
    "VS2": [114000, 109000, 103000, 94000, 85000, 76000, 68000],
    "SI1": [98000, 94000, 89000, 81000, 73000, 66000, 59000],
}


def make_default_matrix() -> pd.DataFrame:
    df = pd.DataFrame(default_values, index=colors)
    df.index.name = "Color"
    return df


if "index_matrix" not in st.session_state:
    st.session_state.index_matrix = make_default_matrix()

if page == "Индекс таблица":
    st.title("KURGIN Index Table")
    st.caption("Внутренняя индекс-таблица админки. Это не публичная цена камня и не публичная витрина.")

    top1, top2, top3 = st.columns([1.1, 1.1, 1])

    with top1:
        st.selectbox("Версия индекса", ["Draft June 2026", "Active May 2026"], index=0)

    with top2:
        st.selectbox(
            "Диапазон веса",
            [
                "0.30–0.49 ct",
                "0.50–0.69 ct",
                "0.70–0.89 ct",
                "0.90–0.99 ct",
                "1.00–1.49 ct",
                "1.50–1.99 ct",
                "2.00–2.99 ct",
                "3.00+ ct",
            ],
            index=4,
        )

    with top3:
        st.selectbox(
            "Категория",
            ["Main stones", "Small stones", "Pairs", "Side stones", "Exclusive"],
            index=0,
        )

    st.divider()
    st.subheader("Матрица Color × Clarity")
    st.markdown(
        '<div class="kurgin-note">В ячейках указывается внутренний ориентир ₽/ct для выбранного диапазона веса и категории. Форма камня здесь специально не используется.</div>',
        unsafe_allow_html=True,
    )

    edited_matrix = st.data_editor(
        st.session_state.index_matrix,
        use_container_width=True,
        num_rows="fixed",
        key="index_table_editor",
    )

    c1, c2, c3 = st.columns([1, 1, 4])

    with c1:
        if st.button("Save", use_container_width=True):
            st.session_state.index_matrix = edited_matrix.copy()
            st.success("Индекс-таблица сохранена в текущей сессии.")

    with c2:
        if st.button("Reset", use_container_width=True):
            st.session_state.index_matrix = make_default_matrix()
            st.rerun()

    with c3:
        st.caption("Пока без базы данных и без пароля. Это рабочий каркас таблицы для разработки.")

elif page == "Камни":
    st.title("Камни")
    st.info("Раздел пока не подключён. На этом этапе делаем только индекс-таблицу.")

elif page == "Настройки":
    st.title("Настройки")
    st.info("Раздел пока не подключён. Пароль и доступы добавим ближе к стабильной версии.")
