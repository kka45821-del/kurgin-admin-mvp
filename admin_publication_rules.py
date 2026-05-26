import pandas as pd

PUBLIC_FLAG_COLUMNS = [
    'show_in_catalog',
    'is_mvp_eligible',
    'has_lab_document',
    'physically_received',
    'checked_by_kurgin',
    'upload_confirmed',
]

PUBLIC_ALLOWED_STATUS = 'available'


def boolean_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin(['true', '1', 'yes', 'y', 'да'])


def publication_mask(df: pd.DataFrame) -> pd.Series:
    """Return the MVP publication mask for stones.

    This is the single admin-side business rule for whether a row may enter
    public preview / catalog.json. Storage code must not own this decision.
    """
    if df.empty:
        return pd.Series([], dtype=bool, index=df.index)

    mask = pd.Series(True, index=df.index)
    for col in PUBLIC_FLAG_COLUMNS:
        if col not in df.columns:
            return pd.Series(False, index=df.index)
        mask = mask & boolean_series(df[col])

    if 'current_status' not in df.columns:
        return pd.Series(False, index=df.index)

    status = df['current_status'].astype(str).str.strip().str.lower()
    return mask & status.eq(PUBLIC_ALLOWED_STATUS)


def public_preview(df: pd.DataFrame) -> pd.DataFrame:
    """Filter stones that are allowed to be included in public catalog.json."""
    if df.empty:
        return df
    return df.copy()[publication_mask(df)]


def publication_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {'total': 0, 'public': 0, 'blocked': 0}
    mask = publication_mask(df)
    return {'total': int(len(df)), 'public': int(mask.sum()), 'blocked': int((~mask).sum())}
