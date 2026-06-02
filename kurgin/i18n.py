from __future__ import annotations

import streamlit as st

from kurgin.config import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from translations_lang.en import TRANSLATIONS as EN
from translations_lang.ru import TRANSLATIONS as RU

_DICTIONARIES = {"ru": RU, "en": EN}


def get_language() -> str:
    language = st.session_state.get("language", DEFAULT_LANGUAGE)
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def t(key: str, **kwargs: object) -> str:
    dictionary = _DICTIONARIES.get(get_language(), RU)
    value = dictionary.get(key, RU.get(key, key))
    return value.format(**kwargs) if kwargs else value


def language_selector() -> str:
    current = get_language()
    labels = list(SUPPORTED_LANGUAGES.values())
    codes = list(SUPPORTED_LANGUAGES.keys())
    current_index = codes.index(current)

    selected_label = st.sidebar.selectbox(t("language"), labels, index=current_index)
    selected_code = codes[labels.index(selected_label)]
    st.session_state["language"] = selected_code
    return selected_code
