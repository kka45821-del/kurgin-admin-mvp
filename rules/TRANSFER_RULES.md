# TRANSFER_RULES.md

## Переносимость

Первая версия должна быть переносимой.

Нельзя завязывать бизнес-логику на GitHub, Streamlit Cloud, абсолютные локальные пути или ручные действия в UI хостинга.

## Структура

```text
app.py
requirements.txt
config/
data/
exports/
backups/
modules/
assets/
```

## Запуск

```text
streamlit run app.py
```

## CSV сейчас, база позже

CSV должны проектироваться как будущие таблицы базы:

```text
stones_master.csv → stones
shipments.csv → shipments
import_log.csv → import_logs
catalog_sections.csv → catalog_sections
price_index.csv → price_rules
```

PostgreSQL можно подключить позже, когда структура стабилизируется.
