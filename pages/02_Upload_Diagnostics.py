import streamlit as st
from admin_upload import render_upload_tab

st.set_page_config(page_title='KURGIN Upload Diagnostics', page_icon='📄', layout='wide')
st.title('KURGIN Upload Diagnostics')
st.caption('Выбор листа Excel, диагностика листов и распознавание колонок.')
render_upload_tab()
