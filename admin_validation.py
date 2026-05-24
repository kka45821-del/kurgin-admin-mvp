import pandas as pd

CRITICAL_FIELDS = {
    'stone_id': 'ID / Stock # не распознан',
    'shape': 'Форма / огранка не распознана',
    'carat': 'Вес / carat не распознан или равен 0',
    'color': 'Цвет не распознан',
    'clarity': 'Чистота не распознана',
    'lab': 'Лаборатория не распознана',
    'report_number': 'Report # / сертификат не распознан',
}

OPTIONAL_FIELDS = {
    'price_rub': 'Цена пока необязательна: можно оставить 0 / пусто',
    'karo_score': 'Karo Score пока необязателен: можно оставить 0 / пусто',
}


def _empty(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().isin(['', 'nan', 'None', 'none', 'NONE'])


def validate_catalog(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    critical_rows = []
    warning_rows = []

    if df.empty:
        critical_rows.append({'type': 'critical', 'field': 'file', 'rows': 'all', 'count': 0, 'message': 'Файл пустой или лист выбран неверно'})
        return pd.DataFrame(critical_rows), pd.DataFrame(warning_rows)

    for field, message in CRITICAL_FIELDS.items():
        if field not in df.columns:
            critical_rows.append({'type': 'critical', 'field': field, 'rows': 'all', 'count': len(df), 'message': message})
            continue
        if field == 'carat':
            mask = pd.to_numeric(df[field], errors='coerce').fillna(0).le(0)
        else:
            mask = _empty(df[field])
        if mask.any():
            rows = ', '.join([str(i + 2) for i in df.index[mask].tolist()[:20]])
            critical_rows.append({'type': 'critical', 'field': field, 'rows': rows, 'count': int(mask.sum()), 'message': message})

    if 'stone_id' in df.columns:
        dup = df['stone_id'].astype(str).str.strip().duplicated(keep=False) & ~_empty(df['stone_id'])
        if dup.any():
            rows = ', '.join([str(i + 2) for i in df.index[dup].tolist()[:20]])
            critical_rows.append({'type': 'critical', 'field': 'stone_id', 'rows': rows, 'count': int(dup.sum()), 'message': 'Дублирующиеся stone_id / Stock #'})

    for field, message in OPTIONAL_FIELDS.items():
        if field not in df.columns:
            warning_rows.append({'type': 'warning', 'field': field, 'rows': 'all', 'count': len(df), 'message': message})
            continue
        mask = pd.to_numeric(df[field], errors='coerce').fillna(0).le(0)
        if mask.any():
            rows = ', '.join([str(i + 2) for i in df.index[mask].tolist()[:20]])
            warning_rows.append({'type': 'warning', 'field': field, 'rows': rows, 'count': int(mask.sum()), 'message': message})

    return pd.DataFrame(critical_rows), pd.DataFrame(warning_rows)
