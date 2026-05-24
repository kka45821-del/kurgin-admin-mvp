import base64
import json
import os
import urllib.error
import urllib.request

import pandas as pd
import streamlit as st

from admin_io import BATCHES, BATCH_COLS, STONES, STONE_COLS, load_batches, load_stones

DATA_REPO = 'kka45821-del/kurgin-data'
BRANCH = 'main'


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
    for col in columns:
        if col not in df.columns:
            df[col] = ''
    return df[columns].to_csv(index=False)


def render_publish_tab() -> None:
    st.subheader('Опубликовать каталог в kurgin-data')
    st.caption('Публичный сайт не меняем. Эта кнопка только копирует проверенные CSV из админки в общий репозиторий данных.')

    stones = load_stones()
    batches = load_batches()

    st.metric('Камней в локальном каталоге админки', len(stones))
    st.metric('Партий в локальном журнале', len(batches))

    st.write('Preview stones.csv')
    st.dataframe(stones.head(20), use_container_width=True)

    token = _token()
    if not token:
        st.warning('Для прямой публикации нужен Streamlit secret GITHUB_TOKEN с доступом к kurgin-data.')
        st.download_button('Скачать stones.csv', _df_to_csv(stones, STONE_COLS), file_name='stones.csv')
        st.download_button('Скачать upload_batches.csv', _df_to_csv(batches, BATCH_COLS), file_name='upload_batches.csv')
        return

    confirm = st.checkbox('Подтверждаю публикацию текущего каталога в kurgin-data')
    if st.button('Опубликовать каталог в kurgin-data', type='primary', disabled=not confirm):
        try:
            _publish_file(DATA_REPO, 'stones.csv', _df_to_csv(stones, STONE_COLS), 'Publish stones from admin', token)
            _publish_file(DATA_REPO, 'upload_batches.csv', _df_to_csv(batches, BATCH_COLS), 'Publish batches from admin', token)
            st.success('Каталог опубликован в kurgin-data')
        except Exception as exc:
            st.error(f'Ошибка публикации: {exc}')
