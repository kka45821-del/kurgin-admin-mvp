from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Iterable

FORMULA_VERSION = 'pricing_formula_v1'
FORMULA_DISPLAY = 'base_price_usd_per_carat × carat × manual_usd_rub_rate × score_coefficient'
ROUNDING_RULE = 'ceil_to_1000_rub'

ROUND_SHAPES = {'round', 'круг', 'round brilliant', 'round brilliant cut', 'rbc'}
SCORE_REQUIRED_SECTIONS = {'main', 'large'}
INDEX_V1_SECTIONS = {'main', 'large'}

PRICE_STATUS_MISSING = 'missing'
PRICE_STATUS_REQUEST_PRICE = 'request_price'
PRICE_STATUS_SCORE_REQUIRED = 'score_required'
PRICE_STATUS_CALCULATED = 'calculated'
PRICE_STATUS_NEEDS_REVIEW = 'needs_review'
PRICE_STATUS_CONFIRMED = 'confirmed'
PRICE_STATUS_BLOCKED = 'blocked'

SCORE_BANDS = [
    {'from': 0.0, 'to': 50.0, 'coefficient': 0.5, 'display': '0–49.99', 'include_to': False},
    {'from': 50.0, 'to': 70.0, 'coefficient': 0.7, 'display': '50–69.99', 'include_to': False},
    {'from': 70.0, 'to': 80.0, 'coefficient': 0.8, 'display': '70–79.99', 'include_to': False},
    {'from': 80.0, 'to': 90.0, 'coefficient': 1.0, 'display': '80–89.99', 'include_to': False},
    {'from': 90.0, 'to': 95.0, 'coefficient': 1.2, 'display': '90–94.99', 'include_to': False},
    {'from': 95.0, 'to': 98.5, 'coefficient': 1.4, 'display': '95–98.49', 'include_to': False},
    {'from': 98.5, 'to': 100.0, 'coefficient': 1.7, 'display': '98.5–100', 'include_to': True},
]

DEFAULT_CARAT_BANDS = [
    {'from': 0.00, 'to': 0.30, 'display': '0.00–0.29'},
    {'from': 0.30, 'to': 0.50, 'display': '0.30–0.49'},
    {'from': 0.50, 'to': 0.70, 'display': '0.50–0.69'},
    {'from': 0.70, 'to': 1.00, 'display': '0.70–0.99'},
    {'from': 1.00, 'to': 1.50, 'display': '1.00–1.49'},
    {'from': 1.50, 'to': 2.00, 'display': '1.50–1.99'},
    {'from': 2.00, 'to': 2.50, 'display': '2.00–2.49'},
    {'from': 2.50, 'to': 3.00, 'display': '2.50–2.99'},
    {'from': 3.00, 'to': 4.00, 'display': '3.00–3.99'},
    {'from': 4.00, 'to': 5.00, 'display': '4.00–4.99'},
    {'from': 5.00, 'to': None, 'display': '5.00+'},
]


def _clean_text(value: Any) -> str:
    if value is None:
        return ''
    text = str(value).strip()
    if text.lower() in {'', 'nan', 'none', 'null'}:
        return ''
    return text


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    if value is None or value == '':
        return default
    try:
        if isinstance(value, str):
            value = value.strip().replace(' ', '').replace(',', '.')
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_key(value: Any) -> str:
    return _clean_text(value).strip().lower()


def _is_round(shape: Any) -> bool:
    return _normalize_key(shape) in ROUND_SHAPES


def _normalized_section(section: Any) -> str:
    return _normalize_key(section)


def _row_value(row: dict, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ''):
            return row[key]
    return default


def _stone_score(stone: dict) -> Any:
    return stone.get('karo_score') or stone.get('kurgin_score') or stone.get('score')


def score_coefficient(score: Any) -> float | None:
    """Return KURGIN Score coefficient by controlled V1 bands.

    Returns None when score is missing or outside 0..100.
    """
    score_value = _safe_float(score, None)
    if score_value is None or score_value < 0 or score_value > 100:
        return None
    for band in SCORE_BANDS:
        left = band['from']
        right = band['to']
        include_to = bool(band.get('include_to'))
        if score_value >= left and (score_value < right or (include_to and score_value <= right)):
            return float(band['coefficient'])
    return None


def carat_band(carat: Any, bands: Iterable[dict] | None = None) -> dict:
    """Return carat band where left border is inclusive and right border is exclusive."""
    carat_value = _safe_float(carat, None)
    if carat_value is None or carat_value < 0:
        return {'status': PRICE_STATUS_BLOCKED, 'reason': 'invalid_carat', 'carat': carat_value}
    for band in (list(bands) if bands is not None else DEFAULT_CARAT_BANDS):
        left = _safe_float(band.get('from'), 0.0)
        right = _safe_float(band.get('to'), None)
        if carat_value >= left and (right is None or carat_value < right):
            return {'status': 'found', 'from': left, 'to': right, 'display': band.get('display', ''), 'carat': carat_value}
    return {'status': PRICE_STATUS_MISSING, 'reason': 'carat_band_not_found', 'carat': carat_value}


def ceil_to_1000_rub(value: Any) -> int:
    """Round upward to 1,000 RUB."""
    number = _safe_float(value, 0.0) or 0.0
    if number <= 0:
        return 0
    return int(math.ceil(number / 1000.0) * 1000)


def rate_warning(
    manual_rate: Any,
    reference_rate: Any | None = None,
    threshold: Any = 0,
) -> dict:
    """Compare manual USD/RUB rate against a reference CBR rate.

    Reference rate never changes the calculation automatically. It only returns
    rate_warning=True when absolute difference is greater than threshold.
    """
    manual = _safe_float(manual_rate, None)
    reference = _safe_float(reference_rate, None)
    threshold_value = _safe_float(threshold, 0.0) or 0.0

    if manual is None or manual <= 0:
        return {
            'status': PRICE_STATUS_BLOCKED,
            'rate_warning': True,
            'manual_usd_rub_rate': manual,
            'reference_cbr_usd_rub_rate': reference,
            'rate_warning_threshold_rub': threshold_value,
            'rate_difference_rub': None,
            'reason': 'manual_usd_rub_rate_required',
        }

    if reference is None or reference <= 0:
        return {
            'status': 'ok',
            'rate_warning': False,
            'manual_usd_rub_rate': manual,
            'reference_cbr_usd_rub_rate': reference,
            'rate_warning_threshold_rub': threshold_value,
            'rate_difference_rub': None,
            'reason': 'reference_rate_not_set',
        }

    difference = abs(manual - reference)
    warning = difference > threshold_value
    return {
        'status': PRICE_STATUS_NEEDS_REVIEW if warning else 'ok',
        'rate_warning': warning,
        'manual_usd_rub_rate': manual,
        'reference_cbr_usd_rub_rate': reference,
        'rate_warning_threshold_rub': threshold_value,
        'rate_difference_rub': difference,
        'reason': 'manual_rate_differs_from_reference' if warning else '',
    }


def select_base_price(
    price_table: Iterable[dict],
    shape: Any,
    section: Any,
    carat: Any,
    color: Any = '',
    clarity: Any = '',
) -> dict:
    """Select base USD/ct row from a controlled table."""
    carat_value = _safe_float(carat, None)
    if carat_value is None or carat_value <= 0:
        return {'status': PRICE_STATUS_MISSING, 'price_status': PRICE_STATUS_MISSING, 'reason': 'invalid_or_missing_carat'}

    shape_key = _normalize_key(shape)
    section_key = _normalized_section(section)
    color_key = _normalize_key(color)
    clarity_key = _normalize_key(clarity)

    for row in price_table or []:
        if _normalize_key(_row_value(row, 'shape')) not in {'', shape_key}:
            continue
        if _normalize_key(_row_value(row, 'section')) not in {'', section_key}:
            continue
        if _normalize_key(_row_value(row, 'color')) not in {'', color_key}:
            continue
        if _normalize_key(_row_value(row, 'clarity')) not in {'', clarity_key}:
            continue

        left = _safe_float(_row_value(row, 'carat_band_from', 'from'), 0.0)
        right = _safe_float(_row_value(row, 'carat_band_to', 'to'), None)
        if not (carat_value >= left and (right is None or carat_value < right)):
            continue

        base_price = _safe_float(_row_value(row, 'base_price_usd_per_carat', 'base_price'), None)
        if base_price is None or base_price <= 0:
            return apply_empty_cell_rule(reason='empty_base_price_cell', row=row)

        return {
            'status': 'found',
            'base_price_usd_per_carat': base_price,
            'price_table_version': _row_value(row, 'price_table_version', default=''),
            'row': row,
        }

    return apply_empty_cell_rule(reason='base_price_row_not_found')


def apply_empty_cell_rule(reason: str = 'empty_base_price_cell', row: dict | None = None) -> dict:
    return {
        'status': PRICE_STATUS_REQUEST_PRICE,
        'price_status': PRICE_STATUS_REQUEST_PRICE,
        'reason': reason,
        'row': row,
        'public_visible': True,
        'public_sellable': False,
        'checkout_enabled': False,
        'public_action': 'request_price',
        'calculated_price_rub': None,
        'confirmed_public_price_rub': None,
    }


def apply_score_required_rule(stone: dict) -> dict:
    return {
        'status': PRICE_STATUS_SCORE_REQUIRED,
        'import_status': PRICE_STATUS_BLOCKED,
        'price_status': PRICE_STATUS_SCORE_REQUIRED,
        'error': 'KURGIN Score required',
        'reason': 'round_main_large_requires_kurgin_score',
        'stone_id': stone.get('stone_id') or stone.get('id'),
        'public_visible': True,
        'public_sellable': False,
        'checkout_enabled': False,
        'public_action': 'request_price',
        'calculated_price_rub': None,
        'confirmed_public_price_rub': None,
    }


def _score_required_for_stone(stone: dict) -> bool:
    return _is_round(stone.get('shape')) and _normalized_section(stone.get('section')) in SCORE_REQUIRED_SECTIONS


def validate_round_main_large_score(stone: dict) -> dict:
    if _score_required_for_stone(stone) and score_coefficient(_stone_score(stone)) is None:
        result = apply_score_required_rule(stone)
        result['ok'] = False
        return result
    return {'ok': True, 'status': 'ready', 'reason': ''}


def can_calculate_price(stone: dict, base_price_result: dict | None = None) -> dict:
    """Validate whether a stone can receive a calculated admin price.

    This does not confirm the public price.
    """
    score_validation = validate_round_main_large_score(stone)
    if not score_validation.get('ok'):
        return score_validation

    if _safe_float(stone.get('carat'), 0.0) <= 0:
        return {'ok': False, 'status': PRICE_STATUS_BLOCKED, 'price_status': PRICE_STATUS_BLOCKED, 'reason': 'carat_required'}

    if base_price_result and base_price_result.get('status') in {PRICE_STATUS_REQUEST_PRICE, PRICE_STATUS_MISSING}:
        result = dict(base_price_result)
        result['ok'] = False
        return result

    return {'ok': True, 'status': 'ready', 'reason': ''}


def calculate_price(
    stone: dict,
    price_table: Iterable[dict],
    manual_usd_rub_rate: Any,
    reference_cbr_usd_rub_rate: Any | None = None,
    rate_warning_threshold_rub: Any = 0,
    usd_rub_rate_version: str = '',
    score_band_version: str = 'score_bands_v1',
) -> dict:
    """Calculate V1 admin price without confirming it.

    The result is calculated_price_rub / index_price_hint only. It must not be
    treated as confirmed_public_price_rub until a separate admin confirmation.
    Reference CBR rate never changes the manual rate used in the calculation.
    """
    rate_check = rate_warning(manual_usd_rub_rate, reference_cbr_usd_rub_rate, rate_warning_threshold_rub)
    if rate_check.get('status') == PRICE_STATUS_BLOCKED:
        return rate_check

    base = select_base_price(
        price_table=price_table,
        shape=stone.get('shape'),
        section=stone.get('section'),
        carat=stone.get('carat'),
        color=stone.get('color'),
        clarity=stone.get('clarity'),
    )
    check = can_calculate_price(stone, base)
    if not check.get('ok'):
        return check

    shape = stone.get('shape')
    section = _normalized_section(stone.get('section'))
    if _is_round(shape) and section in INDEX_V1_SECTIONS:
        coefficient = score_coefficient(_stone_score(stone))
    else:
        coefficient = 1.0

    if coefficient is None:
        return apply_score_required_rule(stone)

    carat = _safe_float(stone.get('carat'), 0.0) or 0.0
    manual_rate = rate_check['manual_usd_rub_rate']
    raw_price = float(base['base_price_usd_per_carat']) * carat * manual_rate * coefficient
    rounded_price = ceil_to_1000_rub(raw_price)
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    return {
        'status': PRICE_STATUS_CALCULATED,
        'price_status': PRICE_STATUS_CALCULATED,
        'raw_calculated_price_rub': raw_price,
        'calculated_price_rub': rounded_price,
        'index_price_hint': rounded_price,
        'confirmed_public_price_rub': None,
        'price_confirmed': False,
        'availability_confirmed': False,
        'public_visible': True,
        'public_sellable': False,
        'checkout_enabled': False,
        'public_action': 'request_price',
        'base_price_usd_per_carat': base['base_price_usd_per_carat'],
        'score_coefficient': coefficient,
        'carat': carat,
        'manual_usd_rub_rate': manual_rate,
        'reference_cbr_usd_rub_rate': rate_check.get('reference_cbr_usd_rub_rate'),
        'rate_warning_threshold_rub': rate_check.get('rate_warning_threshold_rub'),
        'rate_difference_rub': rate_check.get('rate_difference_rub'),
        'rate_warning': bool(rate_check.get('rate_warning')),
        'price_table_version': base.get('price_table_version', ''),
        'usd_rub_rate_version': usd_rub_rate_version,
        'score_band_version': score_band_version,
        'formula_version': FORMULA_VERSION,
        'formula_display': FORMULA_DISPLAY,
        'rounding_rule': ROUNDING_RULE,
        'pricing_run_timestamp': timestamp,
        'needs_admin_confirmation': True,
    }
