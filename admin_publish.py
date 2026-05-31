import base64
import json
import os
import time
import urllib.error
import urllib.request

import pandas as pd
import streamlit as st

from admin_io import BATCH_COLS, STONE_COLS, load_batches, load_stones
from admin_log import write_admin_action
from admin_publication_rules import public_preview

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

PUBLIC_COMPUTED_FIELDS = [
    'public_visible',
    'public_sellable',
    'checkout_enabled',
    'public_action',
    'is_request_price',
    'public_state',
    'public_reason',
]

IMPORTANT_CATALOG_FIELDS = [
    'stone_id', 'shape', 'carat', 'color', 'clarity', 'lab', 'report_number',
    'karo_score', 'price_rub', 'section', 'cut', 'polish', 'symmetry',
    'fluorescence', 'measurements', 'diameter', 'diameter_mm', 'quantity',
]

SECTION_ALIASES = {
    'main': 'main', 'основной': 'main', 'основной каталог': 'main',
    'large': 'large', 'крупные': 'large',
    'medium': 'medium', 'средние': 'medium',
    'small': 'small', 'мелкие': 'small',
    'colored': 'colored', 'цветные': 'colored',
    'side': 'side', 'боковые': 'side',
    'pairs': 'pairs', 'парные': 'pairs',
    'exclusive': 'exclusive', 'эксклюзив': 'exclusive',
}

MANUAL_SECTIONS = {'colored', 'side', 'pairs', 'exclusive'}


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


def _publish_file(repo: str, path: str, content: str, message: str, token: str, max_attempts: int = 4) -> None:
    url = f'https://api.github.com/repos/{repo}/contents/{path}'
    encoded = base64.b64encode(content.encode('utf-8')).decode('ascii')
    last_error = None

    for attempt in range(1, max_attempts + 1):
        payload = {
            'message': message,
            'content': encoded,
            'branch': BRANCH,
        }
        sha = _get_sha(repo, path, token)
        if sha:
            payload['sha'] = sha
        try:
            _request('PUT', url, token, payload)
            return
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 409 and attempt < max_attempts:
                time.sleep(0.8 * attempt)
                continue
            raise

    if last_error:
        raise last_error


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


def _safe_float(value, default=0.0) -> float:
    cleaned = _clean_value(value)
    if cleaned is None:
        return default
    try:
        return float(str(cleaned).replace(' ', '').replace(',', '.'))
    except (TypeError, ValueError):
        return default


def _bool_value(value) -> bool:
    cleaned = _clean_value(value)
    if isinstance(cleaned, bool):
        return cleaned
    return str(cleaned or '').strip().lower() in ['1', 'true', 'yes', 'y', 'да']


def _normalize_section(value) -> str:
    cleaned = _clean_value(value)
    if cleaned is None:
        return ''
    return SECTION_ALIASES.get(str(cleaned).strip().lower(), '')


def _section_for_row(row: pd.Series) -> str:
    explicit = _normalize_section(row.get('section'))
    if explicit in MANUAL_SECTIONS:
        return explicit

    if _bool_value(row.get('is_colored')):
        return 'colored'

    carat = _safe_float(row.get('carat'))
    if carat < 0.30:
        return 'small'
    if carat < 1.00:
        return 'medium'
    if carat < 3.00:
        return 'main'
    return 'large'


def _display_price_text(stone: dict) -> str:
    if _bool_value(stone.get('is_request_price')) or stone.get('public_action') == 'request_price':
        return 'по запросу'
    price = stone.get('price') or stone.get('price_rub') or stone.get('public_price_rub')
    if price in [None, 0, '0', '']:
        return 'по запросу'
    return str(price)


def _stone_from_row(row: pd.Series) -> dict:
    stone = {}
    for col in STONE_COLS:
        stone[col] = _clean_value(row.get(col))

    for col in PUBLIC_COMPUTED_FIELDS:
        stone[col] = _clean_value(row.get(col))

    section = _section_for_row(row)
    stone['section'] = section

    for public_key, source_key in PUBLIC_ALIAS_FIELDS.items():
        stone[public_key] = _clean_value(row.get(source_key))

    stone['karo_score'] = stone.get('karo_score')
    stone['KURGIN Score'] = stone.get('kurgin_score')
    stone['priceText'] = _display_price_text(stone)

    return stone


def _catalog_payload(df: pd.DataFrame) -> str:
    public = public_preview(df).copy()
    stones = [_stone_from_row(row) for _, row in public.iterrows()]
    payload = {
        'source': 'KURGIN Admin',
        'updated_at': pd.Timestamp.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'count': len(stones),
        'schema': {
            'version': 'catalog_mvp_v3',
            'score_public_name': 'KURGIN Score',
            'score_field': 'karo_score',
            'includes_full_catalog_fields': True,
            'section_autofill': True,
            'public_state_fields': PUBLIC_COMPUTED_FIELDS,
            'internal_csv_published': False,
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
        if field == 'section':
            calculated = df.apply(_section_for_row, axis=1)
            empty = calculated.astype(str).str.strip().isin(['', 'nan', 'None', 'none'])
        else:
            series = df[field]
            empty = series.isna() | series.astype(str).str.strip().isin(['', 'nan', 'None', 'none', '0'])
        rows.append({'field': field, 'filled': int((~empty).sum()), 'empty': int(empty.sum())})
    return pd.DataFrame(rows)


def _section_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=['section', 'count'])
    calculated = df.apply(_section_for_row, axis=1)
    return calculated.value_counts().rename_axis('section').reset_index(name='count')


def publish_catalog_snapshot(source: str, details: str = '') -> dict:
    """Publish the current public catalog snapshot to kurgin-data.

    Used after admin-side removal/deletion so the public site receives the
    updated catalog without a separate manual publish step.
    Internal CSV files are intentionally not published to the public data repo.
    """
    token = _token()
    if not token:
        raise RuntimeError('GITHUB_TOKEN не задан. Нельзя автоматически обновить сайт.')

    stones = load_stones()
    public = public_preview(stones)
    catalog_json = _catalog_payload(stones)
    catalog_payload = json.loads(catalog_json)

    publish_steps = [
        ('catalog.json', lambda: _publish_file(DATA_REPO, 'catalog.json', catalog_json, f'Publish catalog.json from {source}', token)),
        ('data/catalog.json', lambda: _publish_file(DATA_REPO, 'data/catalog.json', catalog_json, f'Publish data/catalog.json from {source}', token)),
    ]

    failed_step = ''
    try:
        for step_label, publish_action in publish_steps:
            failed_step = step_label
            publish_action()
    except Exception as exc:
        write_admin_action(
            action='publish_catalog_json',
            entity='kurgin-data/catalog.json',
            rows_count=len(public),
            source=source,
            result='error',
            details=f'auto publish failed_step={failed_step}; {details}; error={exc}',
        )
        raise

    updated_at = catalog_payload.get('updated_at', '')
    count = catalog_payload.get('count', 0)
    write_admin_action(
        action='publish_catalog_json',
        entity='kurgin-data/catalog.json',
        rows_count=len(public),
        source=source,
        result='success',
        details=f'auto publish public JSON only; updated_at={updated_at}; count={count}; {details}',
    )
    return {'updated_at': updated_at, 'count': count}


def render_publish_tab() -> None:
    st.subheader('Опубликовать публичный catalog.json в kurgin-data')
    st.caption('Публикуем только публичные JSON-данные. Внутренние CSV не публикуются наружу.')

    stones = load_stones()
    batches = load_batches()
    public = public_preview(stones)
    catalog_json = _catalog_payload(stones)
    catalog_payload = json.loads(catalog_json)

    st.metric('Всего камней в админке', len(stones))
    st.metric('Публичных камней для catalog.json', len(public))
    st.metric('Партий', len(batches))

    if 'public_state' in public.columns:
        with st.expander('Состояния перед публикацией', expanded=True):
            state_summary = public['public_state'].fillna('unknown').astype(str).value_counts().rename_axis('public_state').reset_index(name='count')
            st.dataframe(state_summary, use_container_width=True)

    st.write('Preview публичных камней')
    st.dataframe(public.head(20), use_container_width=True)

    with st.expander('Распределение по разделам перед публикацией', expanded=True):
        st.dataframe(_section_summary(public), use_container_width=True)

    with st.expander('Покрытие важных полей перед публикацией', expanded=False):
        st.dataframe(_field_coverage(public), use_container_width=True)

    st.download_button('Скачать catalog.json', catalog_json, file_name='catalog.json')
    st.download_button('Скачать stones.csv для внутренней проверки', _df_to_csv(stones, STONE_COLS), file_name='stones.csv')
    st.download_button('Скачать upload_batches.csv для внутренней проверки', _df_to_csv(batches, BATCH_COLS), file_name='upload_batches.csv')

    token = _token()
    if not token:
        st.warning('Автопубликация требует Streamlit secret GITHUB_TOKEN. Пока можно скачать catalog.json и загрузить его в kurgin-data вручную.')
        return

    confirm = st.checkbox('Подтверждаю публикацию публичного catalog.json в kurgin-data')
    if st.button('Опубликовать публичный catalog.json', type='primary', disabled=not confirm):
        status_box = st.empty()
        status_box.info('Публикация началась')
        try:
            result = publish_catalog_snapshot(source='admin_publish', details='manual publish button')
            status_box.success('Публикация завершена')
            st.success('catalog.json опубликован')
            st.info(f"updated_at: {result.get('updated_at', '')}\n\ncount: {result.get('count', 0)}")
        except urllib.error.HTTPError as exc:
            status_box.error('Публикация остановлена')
            st.error(f'Ошибка публикации: HTTP Error {exc.code}: {exc.reason}')
            if exc.code == 409:
                st.warning('GitHub вернул 409 Conflict. Нажми кнопку публикации ещё раз через 10 секунд. Код повторно запрашивает свежий SHA файла, поэтому повтор обычно проходит.')
        except Exception as exc:
            status_box.error('Публикация остановлена')
            st.error(f'Ошибка публикации: {exc}')
