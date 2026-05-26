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
VISIBLE_WITHOUT_PRICE_STATUSES = {'missing', 'index_pending', 'index_suggested', 'needs_review'}


def boolean_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin(['true', '1', 'yes', 'y', 'да'])


def number_series(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(',', '.', regex=False)
    cleaned = cleaned.str.replace(r'[^0-9.\-]', '', regex=True)
    return pd.to_numeric(cleaned, errors='coerce').fillna(0)


def base_public_mask(df: pd.DataFrame) -> pd.Series:
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


def public_sellable_mask(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series([], dtype=bool, index=df.index)
    base = base_public_mask(df)
    if not {'price_rub', 'price_confirmed', 'availability_confirmed'}.issubset(df.columns):
        return pd.Series(False, index=df.index)
    price = number_series(df['price_rub'])
    return base & price.gt(0) & boolean_series(df['price_confirmed']) & boolean_series(df['availability_confirmed'])


def public_visible_mask(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series([], dtype=bool, index=df.index)
    base = base_public_mask(df)
    sellable = public_sellable_mask(df)
    price = number_series(df['price_rub']) if 'price_rub' in df.columns else pd.Series(0, index=df.index)
    show_without_price = boolean_series(df['show_without_price']) if 'show_without_price' in df.columns else pd.Series(False, index=df.index)
    price_status = df['price_status'].astype(str).str.strip().str.lower() if 'price_status' in df.columns else pd.Series('', index=df.index)
    request_only = price.le(0) & (show_without_price | price_status.isin(VISIBLE_WITHOUT_PRICE_STATUSES) | price_status.eq(''))
    return base & (sellable | request_only)


def publication_mask(df: pd.DataFrame) -> pd.Series:
    """Backward-compatible alias: public visibility, not sellability."""
    return public_visible_mask(df)


def public_preview(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    result = df.copy()[public_visible_mask(df)].copy()
    if result.empty:
        return result
    sellable = public_sellable_mask(result)
    result['public_visible'] = True
    result['public_sellable'] = sellable
    result['checkout_enabled'] = sellable
    result['public_action'] = sellable.map({True: 'checkout', False: 'request_price'})
    return result


def publication_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {'total': 0, 'visible': 0, 'sellable': 0, 'blocked': 0}
    visible = public_visible_mask(df)
    sellable = public_sellable_mask(df)
    return {'total': int(len(df)), 'visible': int(visible.sum()), 'sellable': int(sellable.sum()), 'blocked': int((~visible).sum())}
