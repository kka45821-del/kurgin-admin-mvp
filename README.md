# KURGIN Admin — Stage 01 v2-delete-fields

Этап 1: безопасный импорт поставки.

Добавлено к рабочей v2:

- безопасное удаление конкретной поставки полностью;
- поля камня: `fluorescence`, `min_diameter`, `max_diameter`, `depth_mm`;
- сохранение текущей логики импорта v2.

## Запуск

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Важно

Streamlit Cloud runtime не считать постоянным хранилищем настоящих данных.
