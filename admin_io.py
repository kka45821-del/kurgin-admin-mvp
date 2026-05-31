from pathlib import Path
import re

import pandas as pd

DATA = Path('data')
DATA.mkdir(exist_ok=True)
STONES = DATA / 'stones.csv'
BATCHES = DATA / 'upload_batches.csv'
BATCH_PAYMENTS = DATA / 'batch_payments.csv'

TAG_COLS = ['tag1', 'tag2', 'tag3', 'tag4', 'tag5', 'tag6']
BASE_COLS = ['stone_id', 'title', 'shape', 'carat', 'color', 'clarity', 'lab', 'report_number', 'price_rub', 'karo_score']
DETAIL_COLS = ['section', 'cut', 'polish', 'symmetry', 'fluorescence', 'measurements', 'diameter', 'diameter_mm', 'size_mm', 'quantity', 'is_colored', 'color_type', 'color_hue', 'color_intensity', 'pair_id', 'side_type', 'growth_method', 'supplier_rate', 'supplier_total']
PRICE_COLS = [
    'site_price_rub', 'client_mode_price_rub', 'jeweler_price_rub',
    'price_confirmed', 'availability_confirmed', 'price_source', 'price_status',
    'index_price_hint', 'admin_final_price_rub', 'admin_price_note', 'show_without_price',
    'confirmed_public_price_rub', 'calculated_price_rub', 'raw_calculated_price_rub',
    'manual_usd_rub_rate', 'global_price_adjustment_percent', 'pricing_run_timestamp',
]
STATE_COLS = [
    'current_status', 'batch_number', 'upload_date', 'supplier_name', 'show_in_catalog',
    'is_mvp_eligible', 'has_lab_document', 'physically_received', 'checked_by_kurgin',
    'upload_confirmed', 'notes_internal', 'removed_from_sale_at',
]
STONE_COLS = BASE_COLS + DETAIL_COLS + PRICE_COLS + TAG_COLS + STATE_COLS
BATCH_COLS = [
    'batch_number', 'upload_date', 'supplier_name', 'stones_count', 'upload_confirmed', 'notes',
    'purchase_total_rub', 'purchase_advance_rub', 'purchase_debt_rub',
    'batch_status', 'archived_at', 'archived_note', 'permanently_deleted_at',
    'removed_from_sale_at', 'removed_from_sale_note',
]
PAYMENT_COLS = ['batch_number', 'payment_date', 'amount_rub', 'note', 'created_at']

ALIASES = {
    'stone_id': ['stone_id', 'stone id', 'id', 'sku', 'stock', 'stock #', 'stock id', 'lot', 'lot no', 'lot number', 'sr no', 'no'],
    'title': ['title', 'name', 'description', 'stone', 'item', 'product', 'название', 'описание'],
    'shape': ['shape', 'shape name', 'diamond shape', 'cut shape', 'form', 'description', 'форма', 'огранка'],
    'carat': ['carat', 'carats', 'ct', 'cts', 'weight', 'carat weight', 'weight ct', 'size', 'вес', 'карат'],
    'color': ['color', 'colour', 'color grade', 'colour grade', 'col', 'цвет', 'цветность'],
    'clarity': ['clarity', 'clarity grade', 'cla', 'cl', 'purity', 'чистота'],
    'lab': ['lab', 'laboratory', 'cert lab', 'certificate lab', 'grading lab', 'issuer', 'лаборатория'],
    'report_number': ['report_number', 'report number', 'report no', 'report #', 'report', 'certificate', 'certificate number', 'certificate no', 'cert', 'cert no', 'номер сертификата'],
    'price_rub': ['price_rub', 'price rub', 'price_rur', 'price rur', 'public price rub', 'price', 'rub', 'rur', 'цена', 'стоимость'],
    'karo_score': ['karo_score', 'karo score', 'kurgin_score', 'kurgin score', 'score', 'karo', 'оценка'],
    'section': ['section', 'catalog section', 'category', 'раздел'],
    'cut': ['cut', 'cut grade'],
    'polish': ['polish'],
    'symmetry': ['symmetry', 'sym'],
    'fluorescence': ['fluorescence', 'fluor', 'fluo', 'fluorescence intensity'],
    'measurements': ['measurements', 'measurement', 'measure', 'размеры'],
    'diameter': ['diameter', 'diameter mm'],
    'diameter_mm': ['diameter_mm', 'diameter mm', 'diametermm'],
    'size_mm': ['size_mm', 'size mm', 'mm', 'размер мм'],
    'quantity': ['quantity', 'qty', 'pcs', 'pieces', 'pcs/cts', 'count', 'количество', 'шт'],
    'is_colored': ['is_colored', 'is colored', 'colored', 'цветной'],
    'color_type': ['color_type', 'color type', 'fancy color', 'color description', 'описание цвета'],
    'color_hue': ['color_hue', 'color hue', 'hue'],
    'color_intensity': ['color_intensity', 'color intensity', 'intensity'],
    'pair_id': ['pair_id', 'pair id', 'pair number', 'pair'],
    'side_type': ['side_type', 'side type', 'side shape'],
    'growth_method': ['type', 'growth_method', 'growth method', 'method', 'cvd hpht'],
    'supplier_rate': ['rate', 'supplier rate'],
    'supplier_total': ['total amt', 'total amount', 'supplier total'],
    'site_price_rub': ['site_price_rub', 'site price rub', 'public site price rub', 'website price rub', 'цена на сайте'],
    'client_mode_price_rub': ['client_mode_price_rub', 'client mode price rub', 'client price rub', 'цена в режиме клиента'],
    'jeweler_price_rub': ['jeweler_price_rub', 'jeweler price rub', 'jeweller price rub', 'цена для ювелира'],
    'price_confirmed': ['price_confirmed', 'price confirmed', 'confirmed price', 'цена подтверждена'],
    'availability_confirmed': ['availability_confirmed', 'availability confirmed', 'confirmed availability', 'наличие подтверждено'],
    'price_source': ['price_source', 'price source', 'источник цены'],
    'price_status': ['price_status', 'price status', 'статус цены'],
    'index_price_hint': ['index_price_hint', 'index price hint', 'index hint', 'ориентир цены'],
    'admin_final_price_rub': ['admin_final_price_rub', 'admin final price rub', 'final price rub', 'финальная цена'],
    'admin_price_note': ['admin_price_note', 'admin price note', 'price note', 'комментарий по цене'],
    'show_without_price': ['show_without_price', 'show without price', 'показывать без цены'],
    'confirmed_public_price_rub': ['confirmed_public_price_rub', 'confirmed public price rub'],
    'calculated_price_rub': ['calculated_price_rub', 'calculated price rub'],
    'raw_calculated_price_rub': ['raw_calculated_price_rub', 'raw calculated price rub'],
    'manual_usd_rub_rate': ['manual_usd_rub_rate', 'manual usd rub rate'],
    'global_price_adjustment_percent': ['global_price_adjustment_percent', 'global price adjustment percent'],
    'pricing_run_timestamp': ['pricing_run_timestamp', 'pricing run timestamp'],
    **{col: [col, col.replace('tag', 'teg'), col.replace('tag', 'тег')] for col in TAG_COLS},
}

TEXT_COLS = [
    'stone_id', 'title', 'shape', 'color', 'clarity', 'lab', 'report_number', 'section',
    'cut', 'polish', 'symmetry', 'fluorescence', 'measurements', 'is_colored', 'color_type',
    'color_hue', 'color_intensity', 'pair_id', 'side_type', 'growth_method', 'price_confirmed',
    'availability_confirmed', 'price_source', 'price_status', 'admin_price_note', 'show_without_price',
    'pricing_run_timestamp', *TAG_COLS, 'current_status', 'batch_number', 'upload_date',
    'supplier_name', 'show_in_catalog', 'is_mvp_eligible', 'has_lab_document', 'physically_received',
    'checked_by_kurgin', 'upload_confirmed', 'notes_internal', 'removed_from_sale_at',
]
NUMBER_COLS = [
    'carat', 'price_rub', 'site_price_rub', 'client_mode_price_rub', 'jeweler_price_rub', 'karo_score',
    'diameter', 'diameter_mm', 'size_mm', 'quantity', 'supplier_rate', 'supplier_total',
    'index_price_hint', 'admin_final_price_rub', 'confirmed_public_price_rub', 'calculated_price_rub',
    'raw_calculated_price_rub', 'manual_usd_rub_rate', 'global_price_adjustment_percent'
]
BATCH_NUMBER_COLS = ['stones_count', 'purchase_total_rub', 'purchase_advance_rub', 'purchase_debt_rub']
PAYMENT_NUMBER_COLS = ['amount_rub']


def key_name(value) -> str:
    return ''.join(ch for ch in str(value).strip().lower() if ch.isalnum())


def load_table(path: Path, columns: list[str]) -> pd.DataFrame:
    df = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=columns)
    if 'tags' in df.columns:
        parts = df['tags'].fillna('').astype(str).str.replace(',', ';', regex=False).str.split(';')
        for index, col in enumerate(TAG_COLS):
            if col not in df.columns:
                df[col] = parts.apply(lambda values: values[index].strip() if len(values) > index else '')
    for col in columns:
        if col not in df.columns:
            df[col] = ''
    result = df[columns].copy()
    if path == BATCHES:
        for col in BATCH_NUMBER_COLS:
            result[col] = pd.to_numeric(result[col], errors='coerce').fillna(0)
    if path == BATCH_PAYMENTS:
        for col in PAYMENT_NUMBER_COLS:
            result[col] = pd.to_numeric(result[col], errors='coerce').fillna(0)
    return result


def save_table(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(exist_ok=True)
    if path == STONES:
        columns = STONE_COLS
    elif path == BATCH_PAYMENTS:
        columns = PAYMENT_COLS
    else:
        columns = BATCH_COLS
    for col in columns:
        if col not in df.columns:
            df[col] = ''
    df[columns].to_csv(path, index=False)


def load_stones() -> pd.DataFrame:
    return load_table(STONES, STONE_COLS)


def save_stones(df: pd.DataFrame) -> None:
    save_table(df, STONES)


def load_batches() -> pd.DataFrame:
    return load_table(BATCHES, BATCH_COLS)


def save_batches(df: pd.DataFrame) -> None:
    save_table(df, BATCHES)


def load_batch_payments() -> pd.DataFrame:
    return load_table(BATCH_PAYMENTS, PAYMENT_COLS)


def save_batch_payments(df: pd.DataFrame) -> None:
    save_table(df, BATCH_PAYMENTS)


def add_batch_payment(batch_number: str, payment_date, amount_rub: float, note: str, created_at: str) -> None:
    payments = load_batch_payments()
    row = pd.DataFrame([{
        'batch_number': str(batch_number),
        'payment_date': str(payment_date),
        'amount_rub': float(amount_rub or 0),
        'note': note or '',
        'created_at': str(created_at),
    }])
    save_batch_payments(pd.concat([payments, row], ignore_index=True))


def next_batch_number() -> str:
    log = load_batches()
    nums = []
    for value in log['batch_number'].astype(str):
        if value.startswith('P-'):
            try:
                nums.append(int(value.split('-')[-1]))
            except Exception:
                pass
    return f"P-{(max(nums) + 1 if nums else 1):04d}"


def pick_column(raw: pd.DataFrame, key: str) -> pd.Series:
    columns = {key_name(col): col for col in raw.columns}
    for alias in ALIASES.get(key, [key]):
        if key_name(alias) in columns:
            return raw[columns[key_name(alias)]].reset_index(drop=True)
    return pd.Series([''] * len(raw), dtype='object')


def clean_number(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(',', '.', regex=False)
    cleaned = cleaned.str.replace(r'[^0-9.\-]', '', regex=True)
    return pd.to_numeric(cleaned, errors='coerce').fillna(0)


def bool_value(value) -> bool:
    return str(value).strip().lower() in ['true', '1', 'yes', 'y', 'да']


def derive_diameter_from_measurements(value) -> float:
    numbers = re.findall(r'\d+(?:[\.,]\d+)?', str(value or ''))
    if len(numbers) < 2:
        return 0.0
    try:
        first = float(numbers[0].replace(',', '.'))
        second = float(numbers[1].replace(',', '.'))
        return round((first + second) / 2, 3) if first > 0 and second > 0 else 0.0
    except ValueError:
        return 0.0


def normalize_shape_value(value: str) -> str:
    text = str(value or '').strip()
    key = text.lower()
    if key in ['round brilliant', 'round brilliant cut', 'rbc', 'round']:
        return 'Round'
    return text.title() if text.isupper() else text


def normalize_excel(raw: pd.DataFrame, batch_number: str, upload_date, supplier_name: str, notes: str) -> pd.DataFrame:
    out = pd.DataFrame({col: [''] * len(raw) for col in STONE_COLS})
    for col in BASE_COLS + DETAIL_COLS + PRICE_COLS + TAG_COLS:
        out[col] = pick_column(raw, col)

    for col in TEXT_COLS:
        out[col] = out[col].astype('object')

    out['current_status'] = 'available'
    out['batch_number'] = str(batch_number)
    out['upload_date'] = str(upload_date)
    out['supplier_name'] = str(supplier_name)
    out['show_in_catalog'] = True
    out['is_mvp_eligible'] = True
    out['has_lab_document'] = True
    out['physically_received'] = True
    out['checked_by_kurgin'] = True
    out['upload_confirmed'] = True
    out['notes_internal'] = notes or 'uploaded_xlsx'
    out['removed_from_sale_at'] = ''

    for col in NUMBER_COLS:
        out[col] = clean_number(out[col])
    out['shape'] = out['shape'].apply(normalize_shape_value)

    # Backward-compatible price model:
    # - site_price_rub is the public site price.
    # - price_rub remains the legacy/public compatibility field.
    # - If either field is provided, mirror it into the other when missing.
    out.loc[out['site_price_rub'].le(0) & out['price_rub'].gt(0), 'site_price_rub'] = out['price_rub']
    out.loc[out['price_rub'].le(0) & out['site_price_rub'].gt(0), 'price_rub'] = out['site_price_rub']

    price_missing = out['price_rub'].le(0)
    existing_price_confirmed = out['price_confirmed'].apply(bool_value)
    existing_availability_confirmed = out['availability_confirmed'].apply(bool_value)
    out['price_confirmed'] = existing_price_confirmed & out['price_rub'].gt(0)
    out['availability_confirmed'] = existing_availability_confirmed | True
    out['price_source'] = out['price_source'].replace('', pd.NA).fillna(price_missing.map({True: 'not_set', False: 'excel'}))
    out['price_status'] = out['price_status'].replace('', pd.NA).fillna(price_missing.map({True: 'missing', False: 'needs_review'}))
    out['show_without_price'] = out['show_without_price'].apply(bool_value) | price_missing

    text_cleanup_cols = TAG_COLS + ['cut', 'polish', 'symmetry', 'fluorescence', 'measurements', 'section', 'color_type', 'pair_id', 'side_type', 'stone_id', 'title', 'color', 'clarity', 'lab', 'report_number', 'price_source', 'price_status', 'admin_price_note', 'pricing_run_timestamp']
    for col in text_cleanup_cols:
        out[col] = out[col].fillna('').astype(str).replace({'nan': '', 'None': '', 'none': ''})

    derived_diameter = out['measurements'].apply(derive_diameter_from_measurements)
    for col in ['diameter', 'diameter_mm']:
        missing = out[col].le(0) & derived_diameter.gt(0)
        out.loc[missing, col] = derived_diameter[missing]

    empty_id = out['stone_id'].astype(str).str.strip().isin(['', 'nan', 'None', 'none'])
    if empty_id.any():
        out.loc[empty_id, 'stone_id'] = [f'{batch_number}-{i + 1:04d}' for i in range(int(empty_id.sum()))]

    empty_title = out['title'].astype(str).str.strip().isin(['', 'nan', 'None', 'none'])
    if empty_title.any():
        out.loc[empty_title, 'title'] = out.loc[empty_title, 'shape'].astype(str) + ' ' + out.loc[empty_title, 'carat'].astype(str) + ' ' + out.loc[empty_title, 'color'].astype(str) + '/' + out.loc[empty_title, 'clarity'].astype(str)

    return out[STONE_COLS]


def upsert_batch_log(
    batch_number: str,
    upload_date,
    supplier_name: str,
    stones_count: int,
    notes: str,
    purchase_total_rub: float = 0,
    purchase_advance_rub: float = 0,
) -> None:
    log = load_batches()
    log = log[~log['batch_number'].astype(str).eq(str(batch_number))]
    total = float(purchase_total_rub or 0)
    advance = float(purchase_advance_rub or 0)
    debt = total - advance
    row = pd.DataFrame([{
        'batch_number': str(batch_number),
        'upload_date': str(upload_date),
        'supplier_name': str(supplier_name),
        'stones_count': int(stones_count),
        'upload_confirmed': True,
        'notes': notes,
        'purchase_total_rub': total,
        'purchase_advance_rub': advance,
        'purchase_debt_rub': debt,
        'batch_status': 'uploaded',
        'archived_at': '',
        'archived_note': '',
        'permanently_deleted_at': '',
        'removed_from_sale_at': '',
        'removed_from_sale_note': '',
    }])
    save_batches(pd.concat([log, row], ignore_index=True))
