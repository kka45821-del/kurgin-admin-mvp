# KURGIN Admin MVP — update notes

Что изменено:

- Пересобран `apps/admin/app.py` в более практичную админку KURGIN.
- Добавлена компактная боковая навигация.
- Добавлен главный экран со статусами по каталогу, индексу и текстам.
- Добавлена ручная редактируемая таблица каталога через `st.data_editor`.
- Добавлена ручная редактируемая таблица KURGIN Index ₽/ct.
- Добавлена ручная таблица текстов/переводов сайта.
- Добавлен предпросмотр public snapshot для каталога и индекса.
- Добавлен экспорт CSV и JSON.
- Добавлен Risk Center: дубли stone_id, публичные камни без report_number, show без готового статуса, ошибки диапазонов индекса.
- API теперь не ломает интерфейс, если FastAPI временно выключен: ошибка показывается в UI.
- В `requirements.txt` добавлен явный `pandas==2.2.3`.

Важно:

- Это всё ещё MVP UI. Редактирование сохраняется в текущей Streamlit-сессии.
- Для настоящей рабочей версии нужно добавить сохранение в PostgreSQL через FastAPI endpoints.
- Следующий backend-слой: `POST/PUT /admin/catalog`, `POST/PUT /admin/index`, `POST /admin/publish/catalog`, `POST /admin/publish/index`.

Проверка:

- `python -m compileall apps/admin/app.py`
- `pytest -q`
- Результат: 5 passed.
