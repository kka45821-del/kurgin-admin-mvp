from pathlib import Path

import pandas as pd

DATA = Path('data')
DATA.mkdir(exist_ok=True)
STONES = DATA / 'stones.csv'
BATCHES = DATA / 'upload_batches.csv'

TAG_COLS = ['tag1', 'tag2', 'tag3', 'tag4', 'tag5', 'tag6']
BASE_COLS = ['stone_id', 'title', 'shape', 'carat', 'color', 'clarity', 'lab', 'report_number', 'price_rub', 'karo_score']
DETAIL_COLS = [
    'section', 'cut', 'polish', 'symmetry', 'fluorescence', 'measurements',
    'diameter', 'diameter_mm', 'size_mm', 'quantity',
    'is_colored', 'color_type', 'color_hue', 'color_intensity',
    'pair_id', 'side_type', 'growth_method', 'supplier_rate', 'supplier_total',
]
STATE_COLS = ['current_status', 'batch_number', 'upload_date', 'supplier_name', 'show_in_catalog', 'is_mvp_eligible', 'has_lab_document', 'physically_received', 'checked_by_kurgin', 'upload_confirmed', 'notes_internal']
STONE_COLS = BASE_COLS + DETAIL_COLS + TAG_COLS + STATE_COLS
BATCH_COLS = ['batch_number', 'upload_date', 'supplier_name', 'stones_count', 'upload_confirmed', 'notes']

TEXT_COLS = [
    'stone_id', 'title', 'shape', 'color', 'clarity', 'lab', 'report_number',
    'section', 'cut', 'polish', 'symmetry', 'fluorescence', 'measurements',
    'is_colored', 'color_type', 'color_hue', 'color_intensity', 'pair_id',
    'side_type', 'growth_method', *TAG_COLS, 'current_status', 'batch_number',
    'upload_date', 'supplier_name', 'show_in_catalog', 'is_mvp_eligible',
    'has_lab_document', 'physically_received', 'checked_by_kurgin',
    'upload_confirmed', 'notes_internal'
]

ALIASES = {
    'stone_id': ['stone_id', 'stone id', 'id', 'sku', 'stock', 'stock #', 'stock id', 'stock_id', 'lot', 'lot no', 'lot number', 'sr no', 'no'],
    'title': ['title', 'name', 'description', 'stone', 'item', 'product', 'название', 'описание'],
    'shape': ['shape', 'shape name', 'diamond shape', 'cut shape', 'form', 'description', 'форма', 'огранка'],
    'carat': ['carat', 'carats', 'ct', 'cts', 'weight', 'carat weight', 'weight ct', 'size', 'вес', 'карат'],
    'color': ['color', 'colour', 'color grade', 'colour grade', 'col', 'цвет', 'цветность'],
    'clarity': ['clarity', 'clarity grade', 'cla', 'cl', 'purity', 'чистота'],
    'lab': ['lab', 'laboratory', 'cert lab', 'certificate lab', 'grading lab', 'issuer', 'лаборатория'],
    'report_number': ['report_number', 'report number', 'report no', 'report #', 'report', 'certificate', 'certificate_number', 'certificate number', 'certificate no', 'cert', 'cert no', 'номер сертификата'],
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
    'tag1': ['tag1', 'teg1', 'тег1'],
    'tag2': ['tag2', 'teg2', 'тег2'],
    'tag3': ['tag3', 'teg3', 'тег3'],
    'tag4': ['tag4', 'teg4', 'тег4'],
    'tag5': ['tag5', 'teg5', 'тег5'],
    'tag6': ['tag6', 'teg6', 'тег6'],
}


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
    return df[columns]


def save_table(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(exist_ok=True)
    columns = STONE_COLS if path == STONES else BATCH_COLS
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
        normalized_alias = key_name(alias)
        if normalized_alias in columns:
            return raw[columns[normalized_alias]].reset_index(drop=True)
    return pd.Series([''] * len(raw), dtype='object')


def clean_number(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(',', '.', regex=False)
    cleaned = cleaned.str.replace(r'[^0-9.\-]', '', regex=True)
    return pd.to_numeric(cleaned, errors='coerce').fillna(0)


def normalize_shape_value(value: str) -> str:
    text = str(value or '').strip()
    key = text.lower()
    if key in ['round brilliant', 'round brilliant cut', 'rbc', 'round']:
        return 'Round'
    return text.title() if text.isupper() else text


def normalize_excel(raw: pd.DataFrame, batch_number: str, upload_date, supplier_name: str, notes: str) -> pd.DataFrame:
    out = pd.DataFrame({col: [''] * len(raw) for col in STONE_COLS})
    for col in BASE_COLS + DETAIL_COLS + TAG_COLS:
        out[col] = pick_column(raw, col)

    for col in TEXT_COLS:
        if col in out.columns:
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

    for col in ['carat', 'price_rub', 'karo_score', 'diameter', 'diameter_mm', 'size_mm', 'quantity', 'supplier_rate', 'supplier_total']:
        out[col] = clean_number(out[col])
    out['shape'] = out['shape'].apply(normalize_shape_value)

    text_cleanup_cols = TAG_COLS + ['cut', 'polish', 'symmetry', 'fluorescence', 'measurements', 'section', 'color_type', 'pair_id', 'side_type', 'stone_id', 'title', 'color', 'clarity', 'lab', 'report_number']
    for col in text_cleanup_cols:
        out[col] = out[col].fillna('').astype(str).replace({'nan': '', 'None': '', 'none': ''})

    empty_id = out['stone_id'].astype(str).str.strip().isin(['', 'nan', 'None', 'none'])
    if empty_id.any():
        generated_ids = [f'{batch_number}-{i + 1:04d}' for i in range(int(empty_id.sum()))]
        out.loc[empty_id, 'stone_id'] = generated_ids

    empty_title = out['title'].astype(str).str.strip().isin(['', 'nan', 'None', 'none'])
    if empty_title.any():
        out.loc[empty_title, 'title'] = (
            out.loc[empty_title, 'shape'].astype(str) + ' ' +
            out.loc[empty_title, 'carat'].astype(str) + ' ' +
            out.loc[empty_title, 'color'].astype(str) + ' ' +
            out.loc[empty_title, 'clarity'].astype(str)
        )
    return out[STONE_COLS]


def public_preview(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    result = df.copy()
    bool_cols = ['show_in_catalog', 'is_mvp_eligible', 'has_lab_document', 'physically_received', 'checked_by_kurgin', 'upload_confirmed']
    for col in bool_cols:
        result[col] = result[col].astype(str).str.lower().isin(['true', '1', 'yes', 'да'])
    return result[
        result['show_in_catalog'] & result['is_mvp_eligible'] & result['has_lab_document'] &
        result['physically_received'] & result['checked_by_kurgin'] & result['upload_confirmed'] &
        result['current_status'].astype(str).str.lower().eq('available')
    ]


def upsert_batch_log(batch_number: str, upload_date, supplier_name: str, stones_count: int, notes: str) -> None:
    log = load_batches()
    log = log[~log['batch_number'].astype(str).eq(str(batch_number))]
    row = pd.DataFrame([{
        'batch_number': str(batch_number),
        'upload_date': str(upload_date),
        'supplier_name': str(supplier_name),
        'stones_count': int(stones_count),
        'upload_confirmed': True,
        'notes': notes,
    }])
    save_batches(pd.concat([log, row], ignore_index=True))


def batch_summary(stones: pd.DataFrame) -> pd.DataFrame:
    if stones.empty:
        return pd.DataFrame(columns=['batch_number', 'stones_count'])
    return stones.groupby('batch_number', dropna=False).size().reset_index(name='stones_count')