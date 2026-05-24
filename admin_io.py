from datetime import date
from pathlib import Path

import pandas as pd

DATA = Path('data')
DATA.mkdir(exist_ok=True)
STONES = DATA / 'stones.csv'
BATCHES = DATA / 'upload_batches.csv'

TAG_COLS = ['tag1', 'tag2', 'tag3', 'tag4', 'tag5', 'tag6']
BASE_COLS = ['stone_id', 'title', 'shape', 'carat', 'color', 'clarity', 'lab', 'report_number', 'price_rub', 'karo_score']
STATE_COLS = ['current_status', 'batch_number', 'upload_date', 'supplier_name', 'show_in_catalog', 'is_mvp_eligible', 'has_lab_document', 'physically_received', 'checked_by_kurgin', 'upload_confirmed', 'notes_internal']
STONE_COLS = BASE_COLS + TAG_COLS + STATE_COLS
BATCH_COLS = ['batch_number', 'upload_date', 'supplier_name', 'stones_count', 'upload_confirmed', 'notes']

ALIASES = {
    'stone_id': ['stone_id', 'id', 'sku', 'report_number', 'report #'],
    'title': ['title', 'name', 'description'],
    'shape': ['shape', 'форма', 'огранка'],
    'carat': ['carat', 'ct', 'weight', 'вес', 'карат'],
    'color': ['color', 'colour', 'цвет'],
    'clarity': ['clarity', 'чистота'],
    'lab': ['lab', 'laboratory', 'issuer', 'лаборатория'],
    'report_number': ['report_number', 'report', 'report #', 'certificate_number'],
    'price_rub': ['price_rub', 'price', 'цена', 'rub'],
    'karo_score': ['karo_score', 'score', 'kurgin_score', 'karo'],
    'tag1': ['tag1', 'teg1', 'тег1'],
    'tag2': ['tag2', 'teg2', 'тег2'],
    'tag3': ['tag3', 'teg3', 'тег3'],
    'tag4': ['tag4', 'teg4', 'тег4'],
    'tag5': ['tag5', 'teg5', 'тег5'],
    'tag6': ['tag6', 'teg6', 'тег6'],
}


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
    df.to_csv(path, index=False)


def load_stones() -> pd.DataFrame:
    return load_table(STONES, STONE_COLS)


def save_stones(df: pd.DataFrame) -> None:
    save_table(df[STONE_COLS], STONES)


def load_batches() -> pd.DataFrame:
    return load_table(BATCHES, BATCH_COLS)


def save_batches(df: pd.DataFrame) -> None:
    save_table(df[BATCH_COLS], BATCHES)


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
    columns = {str(col).strip().lower(): col for col in raw.columns}
    for alias in ALIASES.get(key, [key]):
        if alias.lower() in columns:
            return raw[columns[alias.lower()]].reset_index(drop=True)
    return pd.Series([''] * len(raw))


def normalize_excel(raw: pd.DataFrame, batch_number: str, upload_date, supplier_name: str, notes: str) -> pd.DataFrame:
    out = pd.DataFrame({col: [''] * len(raw) for col in STONE_COLS})

    for col in BASE_COLS + TAG_COLS:
        out[col] = pick_column(raw, col)

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

    for col in ['carat', 'price_rub', 'karo_score']:
        out[col] = pd.to_numeric(out[col], errors='coerce').fillna(0)

    for col in TAG_COLS:
        out[col] = out[col].fillna('').astype(str).replace({'nan': '', 'None': ''})

    empty_id = out['stone_id'].astype(str).str.strip().isin(['', 'nan', 'None'])
    out.loc[empty_id, 'stone_id'] = [f'{batch_number}-{i + 1:04d}' for i in range(empty_id.sum())]

    empty_title = out['title'].astype(str).str.strip().isin(['', 'nan', 'None'])
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
        result['show_in_catalog'] &
        result['is_mvp_eligible'] &
        result['has_lab_document'] &
        result['physically_received'] &
        result['checked_by_kurgin'] &
        result['upload_confirmed'] &
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
