from pathlib import Path

import pandas as pd
import streamlit as st

from admin_log import write_admin_action

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MATRIX_FILE = DATA / "price_index_matrix_usd.csv"
KS_FILE = DATA / "ks_price_coefficients.csv"

COLORS = ["D", "E", "F", "G"]
CLARITIES = ["IF", "VVS1", "VVS2", "VS1", "VS2"]
CARAT_BANDS = ["0.30-0.39", "0.40-0.49", "0.50-0.69", "0.70-0.89", "0.90-0.99", "1.00-1.49", "1.50-1.99", "2.00-2.99", "3.00-3.99", "4.00-4.99", "5.00+"]
BAND_LIMITS = {
    "0.30-0.39": (0.30, 0.39),
    "0.40-0.49": (0.40, 0.49),
    "0.50-0.69": (0.50, 0.69),
    "0.70-0.89": (0.70, 0.89),
    "0.90-0.99": (0.90, 0.99),
    "1.00-1.49": (1.00, 1.49),
    "1.50-1.99": (1.50, 1.99),
    "2.00-2.99": (2.00, 2.99),
    "3.00-3.99": (3.00, 3.99),
    "4.00-4.99": (4.00, 4.99),
    "5.00+": (5.00, 99.99),
}
KS_ROWS = [
    {"ks_range": "KS < 70", "coefficient": 0.60},
    {"ks_range": "KS 70-80", "coefficient": 0.80},
    {"ks_range": "KS 80-90", "coefficient": 1.00},
    {"ks_range": "KS 90-95", "coefficient": 1.20},
    {"ks_range": "KS 95-99", "coefficient": 1.40},
    {"ks_range": "KS 99+", "coefficient": 1.70},
]


def empty_matrix() -> pd.DataFrame:
    return pd.DataFrame([{**{"clarity": clarity}, **{band: 0 for band in CARAT_BANDS}} for clarity in CLARITIES])


def default_long_index() -> pd.DataFrame:
    rows = []
    for color in COLORS:
        for clarity in CLARITIES:
            for band in CARAT_BANDS:
                carat_min, carat_max = BAND_LIMITS[band]
                rows.append({
                    "color": color,
                    "clarity": clarity,
                    "carat_band": band,
                    "carat_min": carat_min,
                    "carat_max": carat_max,
                    "section": "large" if carat_min >= 3 else "main",
                    "price_usd_per_ct": 0,
                })
    return pd.DataFrame(rows)


def load_long_index() -> pd.DataFrame:
    if MATRIX_FILE.exists():
        df = pd.read_csv(MATRIX_FILE)
    else:
        df = default_long_index()
    for col in ["color", "clarity", "carat_band", "carat_min", "carat_max", "section", "price_usd_per_ct"]:
        if col not in df.columns:
            df[col] = "" if col not in {"carat_min", "carat_max", "price_usd_per_ct"} else 0
    df["price_usd_per_ct"] = pd.to_numeric(df["price_usd_per_ct"], errors="coerce").fillna(0)
    df["carat_min"] = pd.to_numeric(df["carat_min"], errors="coerce").fillna(0)
    df["carat_max"] = pd.to_numeric(df["carat_max"], errors="coerce").fillna(0)
    return df


def save_long_index(df: pd.DataFrame) -> None:
    df.to_csv(MATRIX_FILE, index=False)


def matrix_for_color(df: pd.DataFrame, color: str) -> pd.DataFrame:
    rows = []
    part = df[df["color"].astype(str).str.upper().eq(color)]
    for clarity in CLARITIES:
        row = {"clarity": clarity}
        for band in CARAT_BANDS:
            match = part[(part["clarity"].astype(str).str.upper() == clarity) & (part["carat_band"].astype(str) == band)]
            row[band] = float(match.iloc[0]["price_usd_per_ct"]) if not match.empty else 0
        rows.append(row)
    return pd.DataFrame(rows)


def long_from_matrices(matrices: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for color, matrix in matrices.items():
        for _, row in matrix.iterrows():
            clarity = str(row.get("clarity", "")).strip().upper()
            for band in CARAT_BANDS:
                carat_min, carat_max = BAND_LIMITS[band]
                price = pd.to_numeric(pd.Series([row.get(band, 0)]), errors="coerce").fillna(0).iloc[0]
                rows.append({
                    "color": color,
                    "clarity": clarity,
                    "carat_band": band,
                    "carat_min": carat_min,
                    "carat_max": carat_max,
                    "section": "large" if carat_min >= 3 else "main",
                    "price_usd_per_ct": float(price),
                })
    return pd.DataFrame(rows)


def load_ks() -> pd.DataFrame:
    if KS_FILE.exists():
        df = pd.read_csv(KS_FILE)
    else:
        df = pd.DataFrame(KS_ROWS)
    if "ks_range" not in df.columns:
        df["ks_range"] = ""
    if "coefficient" not in df.columns:
        df["coefficient"] = 1.0
    df["coefficient"] = pd.to_numeric(df["coefficient"], errors="coerce").fillna(1.0)
    return df[["ks_range", "coefficient"]]


def save_ks(df: pd.DataFrame) -> None:
    df[["ks_range", "coefficient"]].to_csv(KS_FILE, index=False)


def validate_long(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if df.empty:
        return pd.DataFrame([{"type": "error", "message": "Index matrix empty"}])
    if (pd.to_numeric(df["price_usd_per_ct"], errors="coerce").fillna(0) < 0).any():
        rows.append({"type": "error", "message": "USD/ct не может быть отрицательным"})
    duplicates = df.duplicated(subset=["color", "clarity", "carat_band"], keep=False)
    if duplicates.any():
        rows.append({"type": "error", "message": "Есть дубли color/clarity/carat_band"})
    return pd.DataFrame(rows)


def render_price_index_matrix() -> None:
    st.markdown("### Index table — USD / ct")
    st.caption("Значения в ячейках — доллары за карат. Рубли считаются позже через курс USD/RUB и подтверждение цены.")

    st.markdown("#### KURGIN Score coefficients")
    ks = st.data_editor(load_ks(), use_container_width=True, hide_index=True, key="ks_matrix_coefficients")
    if st.button("Сохранить коэффициенты KS"):
        save_ks(ks)
        write_admin_action("ks_coefficients_save", "data/ks_price_coefficients.csv", len(ks), "price_management", "success", "KS coefficients saved.")
        st.success("Коэффициенты KS сохранены.")
        st.rerun()

    st.divider()
    st.markdown("#### Базовая матрица USD / ct")
    source = load_long_index()
    matrices = {}
    for color in COLORS:
        st.markdown(f"##### Color {color}")
        matrices[color] = st.data_editor(
            matrix_for_color(source, color),
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            key=f"price_index_usd_matrix_{color}",
            disabled=["clarity"],
            column_config={band: st.column_config.NumberColumn(band, min_value=0.0, step=10.0) for band in CARAT_BANDS},
        )

    normalized = long_from_matrices(matrices)
    validation = validate_long(normalized)
    if validation.empty:
        st.success("USD index matrix валидна.")
    else:
        st.error("В USD index matrix есть ошибки. Сохранение заблокировано.")
        st.dataframe(validation, use_container_width=True)

    if st.button("Сохранить USD index matrix", type="primary", disabled=not validation.empty):
        save_long_index(normalized)
        write_admin_action("price_index_usd_matrix_save", "data/price_index_matrix_usd.csv", len(normalized), "price_management", "success", "USD/ct matrix saved. Public prices are not recalculated automatically.")
        st.success("USD index matrix сохранена. Публичные цены не изменены автоматически.")
        st.rerun()

    with st.expander("Технический normalized view", expanded=False):
        st.dataframe(normalized, use_container_width=True)
