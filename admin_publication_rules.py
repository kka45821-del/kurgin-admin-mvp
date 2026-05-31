import pandas as pd

from admin_price_display_settings import public_prices_request_only

PUBLIC_FLAG_COLUMNS = [
    'show_in_catalog',
    'is_mvp_eligible',
    'has_lab_document',
    'physically_received',
    'checked_by_kurgin',
    'upload_confirmed',
]

PUBLIC_ALLOWED_STATUS = 'available'
VISIBLE_WITHOUT_PRICE_STATUSES = {'missing', 'index_pending', 'index_suggested', 'needs_review', 'request_price'}
SELLABLE_PRICE_STATUSES = {'confirmed', 'final', 'manual_confirmed', 'approved', 'index_confirmed'}
PUBLIC_PRICE_COLUMNS = [
    'price_rub', 'site_price_rub', 'client_mode_price_rub', 'jeweler_price_rub',
    'index_price_hint', 'admin_final_price_rub', 'confirmed_public_price_rub',
    'calculated_price_rub', 'raw_calculated_price_rub', 'supplier_rate', 'supplier_total',
]
CHECKOUT_FEATURE_ENABLED = False


def boolean_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin(['true', '1', 'yes', 'y', 'да'])


def number_series(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(',', '.', regex=False)
    cleaned = cleaned.str.replace(r'[^0-9.\-]', '', regex=True)
    return pd.to_numeric(cleaned, errors='coerce').fillna(0)


def price_status_series(df: pd.DataFrame) -> pd.Series:
    if 'price_status' not in df.columns:
        return pd.Series('', index=df.index)
    return df['price_status'].astype(str).str.strip().str.lower()


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
    required = {'price_rub', 'price_confirmed', 'availability_confirmed', 'price_status'}
    if not required.issubset(df.columns):
        return pd.Series(False, index=df.index)
    price = number_series(df['price_rub'])
    price_status = price_status_series(df)
    return (
        base
        & price.gt(0)
        & boolean_series(df['price_confirmed'])
        & boolean_series(df['availability_confirmed'])
        & price_status.isin(SELLABLE_PRICE_STATUSES)
    )


def public_visible_mask(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series([], dtype=bool, index=df.index)
    base = base_public_mask(df)
    sellable = public_sellable_mask(df)
    price = number_series(df['price_rub']) if 'price_rub' in df.columns else pd.Series(0, index=df.index)
    show_without_price = boolean_series(df['show_without_price']) if 'show_without_price' in df.columns else pd.Series(False, index=df.index)
    price_status = price_status_series(df)
    request_only = show_without_price | price.le(0) | price_status.isin(VISIBLE_WITHOUT_PRICE_STATUSES) | price_status.eq('')
    return base & (sellable | request_only)


def publication_mask(df: pd.DataFrame) -> pd.Series:
    return public_visible_mask(df)


def public_reason_series(df: pd.DataFrame, sellable: pd.Series, checkout_enabled: pd.Series, request_only_mode: bool = False) -> pd.Series:
    price = number_series(df['price_rub']) if 'price_rub' in df.columns else pd.Series(0, index=df.index)
    price_status = price_status_series(df)
    price_confirmed = boolean_series(df['price_confirmed']) if 'price_confirmed' in df.columns else pd.Series(False, index=df.index)
    availability_confirmed = boolean_series(df['availability_confirmed']) if 'availability_confirmed' in df.columns else pd.Series(False, index=df.index)

    reason = pd.Series('request_price', index=df.index, dtype=object)
    reason = reason.mask(~availability_confirmed, 'availability_not_confirmed')
    reason = reason.mask(~price_confirmed & price.gt(0), 'price_not_confirmed')
    reason = reason.mask(price_status.eq(''), 'price_status_missing')
    reason = reason.mask(price_status.isin({'needs_review', 'index_pending', 'index_suggested'}), 'price_needs_review')
    reason = reason.mask(price.le(0), 'price_missing')
    reason = reason.mask(sellable & ~checkout_enabled, 'checkout_not_enabled')
    reason = reason.mask(request_only_mode & price.gt(0), 'public_price_request_only')
    reason = reason.mask(checkout_enabled, 'checkout_enabled')
    return reason


def mask_public_prices_for_request(df: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    result = df.copy()
    for col in PUBLIC_PRICE_COLUMNS:
        if col in result.columns:
            result.loc[mask, col] = 0
    return result


def public_preview(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    result = df.copy()[public_visible_mask(df)].copy()
    if result.empty:
        return result
    sellable = public_sellable_mask(result)
    request_only_mode = public_prices_request_only()
    checkout_enabled = sellable & CHECKOUT_FEATURE_ENABLED & ~request_only_mode
    is_request_price = request_only_mode | ~sellable

    result['public_visible'] = True
    result['public_sellable'] = sellable
    result['checkout_enabled'] = checkout_enabled
    result['public_action'] = checkout_enabled.map({True: 'checkout', False: 'request_price'})
    result['is_request_price'] = is_request_price
    result['public_state'] = 'request_price'
    result.loc[sellable & ~checkout_enabled & ~request_only_mode, 'public_state'] = 'sellable_contact'
    result.loc[checkout_enabled, 'public_state'] = 'checkout'
    result['public_reason'] = public_reason_series(result, sellable, checkout_enabled, request_only_mode)
    result = mask_public_prices_for_request(result, is_request_price)
    return result


def publication_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {'total': 0, 'visible': 0, 'sellable': 0, 'checkout': 0, 'request_price': 0, 'blocked': 0}
    visible = public_visible_mask(df)
    sellable = public_sellable_mask(df)
    preview = public_preview(df)
    checkout = boolean_series(preview['checkout_enabled']) if not preview.empty and 'checkout_enabled' in preview.columns else pd.Series(False, index=preview.index)
    request_price = boolean_series(preview['is_request_price']) if not preview.empty and 'is_request_price' in preview.columns else pd.Series(False, index=preview.index)
    return {
        'total': int(len(df)),
        'visible': int(visible.sum()),
        'sellable': int(sellable.sum()),
        'checkout': int(checkout.sum()),
        'request_price': int(request_price.sum()),
        'blocked': int((~visible).sum()),
    }
