from datetime import date

import pandas as pd
import streamlit as st

from admin_io import STONE_COLS, batch_summary, load_batches, load_stones, normalize_excel, save_batches, save_stones, upsert_batch_log


def render_batches_tab() -> None:
    st.subheader('Партии')

    stones = load_stones()
    batches = load_batches()
    summary = batch_summary(stones)

    if summary.empty:
        st.info('Партии пока не загружены')
        return

    if not batches.empty:
        meta_cols = ['batch_number', 'upload_date', 'supplier_name']
        meta = batches[meta_cols].drop_duplicates('batch_number', keep='last')
        summary = summary.merge(meta, on='batch_number', how='left')

    st.dataframe(summary, use_container_width=True)

    selected = st.selectbox('Выбрать партию', summary['batch_number'].astype(str).tolist())
    part = stones[stones['batch_number'].astype(str).eq(selected)].copy()

    st.metric('Камней в выбранной партии', len(part))

    edited_part = st.data_editor(
        part,
        num_rows='dynamic',
        use_container_width=True,
        key=f'batch_editor_{selected}',
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button('Сохранить изменения партии', type='primary'):
            rest = stones[~stones['batch_number'].astype(str).eq(selected)]
            edited_part['batch_number'] = selected
            result = pd.concat([rest, edited_part[STONE_COLS]], ignore_index=True)
            save_stones(result)

            supplier = edited_part['supplier_name'].iloc[0] if len(edited_part) else ''
            upload_date = edited_part['upload_date'].iloc[0] if len(edited_part) else ''
            upsert_batch_log(selected, upload_date, supplier, len(edited_part), 'batch edited')
            st.success(f'Партия {selected} обновлена')

    with col2:
        if st.button('Снять партию с публикации'):
            all_rows = stones.copy()
            mask = all_rows['batch_number'].astype(str).eq(selected)
            all_rows.loc[mask, 'show_in_catalog'] = False
            all_rows.loc[mask, 'current_status'] = 'internal_review'
            save_stones(all_rows)
            st.success(f'Партия {selected} снята с публикации')
            st.rerun()

    st.divider()
    st.subheader('Заменить выбранную партию новым .xlsx')

    replacement = st.file_uploader('Новый .xlsx для этой партии', type=['xlsx'], key=f'repl_{selected}')

    if replacement is None:
        return

    replacement_date = st.date_input('Дата замены', value=date.today(), key=f'date_{selected}')
    old_supplier = str(part['supplier_name'].iloc[0]) if len(part) else ''
    replacement_supplier = st.text_input('Поставщик', value=old_supplier, key=f'supplier_{selected}')
    replacement_notes = st.text_area('Заметка по замене', key=f'notes_{selected}')

    raw = pd.read_excel(replacement)
    new_part = normalize_excel(raw, selected, replacement_date, replacement_supplier.strip(), replacement_notes or 'batch replaced')

    st.write('Preview новой партии')
    st.dataframe(new_part.head(20), use_container_width=True)

    confirm_replace = st.checkbox('Подтверждаю замену выбранной партии', key=f'confirm_{selected}')

    if st.button('Заменить выбранную партию', type='primary', disabled=not (confirm_replace and replacement_supplier.strip()), key=f'replace_{selected}'):
        rest = stones[~stones['batch_number'].astype(str).eq(selected)]
        save_stones(pd.concat([rest, new_part], ignore_index=True))
        upsert_batch_log(selected, replacement_date, replacement_supplier.strip(), len(new_part), replacement_notes or 'batch replaced')
        st.success(f'Партия {selected} заменена. Камней: {len(new_part)}')
