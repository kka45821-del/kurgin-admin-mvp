import base64
import json
import os
import urllib.error
import urllib.request

import pandas as pd
import streamlit as st

from admin_io import BATCH_COLS, STONE_COLS, load_batches, load_stones, public_preview

DATA_REPO = 'kka45821-del/kurgin-data'
BRANCH = 'main'

PUBLIC_ALIAS_FIELDS = {
    'id': 'stone_id',
    'score': 'karo_score',
    'kurgin_score': 'karo_score',
    'price': 'price_rub',
    'public_price_rub': 'price_rub',
    'report': 'report_number',
    'availability': 'current_status',
}

IMPORTANT_CATALOG_FIELDS = [
    'stone_id', 'shape', 'carat', 'color', 'clarity', 'lab', 'report_number',
    'karo_score', 'price_rub', 'section', 'cut', 'polish', 'symmetry',
    'fluorescence', 'measurements', 'diameter', 'diameter_mm', 'quantity',
]


def _token() -> str:
    try:
        value = st.secrets.get('GITHUB_TOKEN', '')
    except Exception:
        value = ''
    return value or os.getenv('GITHUB_TOKEN', '')


def _request(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('X-GitHub-Api-Version', '2022-11-28')
    if data is not None:
        req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read().decode('utf-8')
        return json.loads(raw) if raw else {}


def _get_sha(repo: str, path: str, token: str) -> str | None:
    url = f'https://api.github.com/repos/{repo}/contents/{path}?ref={BRANCH}'
    try:
        result = _request('GET', url, token)
        return result.get('sha')
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def _publish_file(repo: str, path: str, content: str, message: str, token: str) -> None:
    url = f'https://api.github.com/repos/{repo}/contents/{path}'
    payload = {
        'message': message,
        'content': base64.b64encode(content.encode('utf-8')).decode('ascii'),
        'branch': BRANCH,
    }
    sha = _get_sha(repo, path, token)
    if sha:
        payload['sha'] = sha
    _request('PUT', url, token, payload)


def _df_to_csv(df: pd.DataFrame, columns: list[str]) -> str:
    result = df.copy()
    for col in columns:
        if col not in result.columns:
            result[col] = ''
    return result[columns].to_csv(index=False)


def _clean_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, 'item'):
        try:
            value = value.item()
        except Exception:
            pass
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return round(value, 6)
    text = str(value).strip()
    if text == '' or text.lower() in ['nan', 'none', 'null']:
        return None
    return text


def _stone_from_row(row: pd.Series) -> dict:
    stone = {}
    for col in STONE_COLS:
        stone[col] = _clean_value(row.get(col))

    for public_key, source_key in PUBLIC_ALIAS_FIELDS.items():
        stone[public_key] = _clean_value(row.get(source_key))

    # Compatibility aliases for the public Streamlit catalog and future analytics.
    stone['karo_score'] = stone.get('karo_score')
    stone['KURGIN Score'] = stone.get('kurgin_score')
    stone['priceText'] = '' if stone.get('price') in [None, 0, '0'] else str(stone.get('price'))

    return stone


def _catalog_payload(df: pd.DataFrame) -> str:
    public = public_preview(df).copy()
    stones = [_stone_from_row(row) for _, row in public.iterrows()]
    payload = {
        'source': 'KURGIN Admin',
        'updated_at': pd.Timestamp.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'count': len(stones),
        'schema': {
            'version': 'catalog_mvp_v2',
            'score_public_name': 'KURGIN Score',
            'score_field': 'karo_score',
            'includes_full_catalog_fields': True,
        },
        'stones': stones,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _field_coverage(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if df.empty:
        return pd.DataFrame(columns=['field', 'filled', 'empty'])
    for field in IMPORTANT_CATALOG_FIELDS:
        if field not in df.columns:
            rows.append({'field': field, 'filled': 0, 'empty': len(df)})
            continue
        series = df[field]
        empty = series.isna() | series.astype(str).str.strip().isin(['', 'nan', 'None', 'none', '0'])
        rows.append({'field': field, 'filled': int((~empty).sum()), 'empty': int(empty.sum())})
    return pd.DataFrame(rows)


def render_publish_tab() -> None:
    st.subheader('Опубликовать catalog.json в kurgin-data')
    st.caption('Публикуем только данные. Публичный сайт и его дизайн не меняем.')

    stones = load_stones()
    batches = load_batches()
    public = public_preview(stones)
    catalog_json = _catalog_payload(stones)

    st.metric('Всего камней в админке', len(stones))
    st.metric('Публичных камней для catalog.json', len(public))
    st.metric('Партий', len(batches))

    st.write('Preview публичных камней')
    st.dataframe(public.head(20), use_container_width=True)

    with st.expander('Покрытие важных полей перед публикацией', expanded=False):
        st.dataframe(_field_coverage(public), use_container_width=True)

    st.download_button('Скачать catalog.json', catalog_json, file_name='catalog.json')
    st.download_button('Скачать stones.csv', _df_to_csv(stones, STONE_COLS), file_name='stones.csv')
    st.download_button('Скачать upload_batches.csv', _df_to_csv(batches, BATCH_COLS), file_name='upload_batches.csv')

    token = _token()
    if not token:
        st.warning('Автопубликация требует Streamlit secret GITHUB_TOKEN. Пока можно скачать catalog.json и загрузить его в kurgin-data вручную.')
        return

    confirm = st.checkbox('Подтверждаю публикацию catalog.json в kurgin-data')
    if st.button('Опубликовать catalog.json', type='primary', disabled=not confirm):
        try:
            _publish_file(DATA_REPO, 'catalog.json', catalog_json, 'Publish catalog.json from admin', token)
            _publish_file(DATA_REPO, 'data/catalog.json', catalog_json, 'Publish data/catalog.json from admin', token)
            _publish_file(DATA_REPO, 'stones.csv', _df_to_csv(stones, STONE_COLS), 'Publish stones.csv from admin', token)
            _publish_file(DATA_REPO, 'upload_batches.csv', _df_to_csv(batches, BATCH_COLS), 'Publish upload_batches.csv from admin', token)
            st.success('catalog.json опубликован в kurgin-data')
        except Exception as exc:
            st.error(f'Ошибка публикации: {exc}')