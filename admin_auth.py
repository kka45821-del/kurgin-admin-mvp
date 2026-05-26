import os

import streamlit as st

from admin_log import write_admin_action


def get_admin_password() -> str:
    try:
        secret_password = st.secrets.get('KURGIN_ADMIN_PASSWORD', '')
    except Exception:
        secret_password = ''
    return secret_password or os.getenv('KURGIN_ADMIN_PASSWORD', '')


def require_admin_login(session_key: str = 'login') -> None:
    password_value = get_admin_password()
    if not password_value:
        st.error('KURGIN_ADMIN_PASSWORD не задан. Добавь пароль в Streamlit secrets или переменную окружения.')
        st.stop()

    if session_key not in st.session_state:
        st.session_state[session_key] = False

    if not st.session_state[session_key]:
        password = st.text_input('Пароль', type='password')
        if st.button('Войти', type='primary'):
            st.session_state[session_key] = password == password_value
            if st.session_state[session_key]:
                write_admin_action(action='admin_login', entity='session', source='admin_auth', details='Успешный вход в админку')
            st.rerun()
        st.stop()


def logout_button(session_key: str = 'login') -> None:
    if st.button('Выйти'):
        write_admin_action(action='admin_logout', entity='session', source='admin_auth', details='Выход из админки')
        st.session_state[session_key] = False
        st.rerun()
