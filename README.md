# KURGIN Platform

Профессиональный no-payment MVP для каталога камней, KURGIN Score, анализа цены и локального избранного.

## Что внутри

- Streamlit UI с несколькими страницами.
- Импорт CSV/XLSX.
- Расчет `KURGIN Score` по модульной формуле.
- Поиск, фильтры и экспорт результатов.
- Локальное избранное через SQLite.
- RU/EN интерфейс.
- Тестовый каталог `data/sample_stones.csv` и `data/sample_stones.xlsx`.
- Без платежей, checkout, подписок и внешних API.

## Быстрый запуск

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

Или:

```bash
chmod +x run_local.sh
./run_local.sh
```

## Как загрузить в новый репозиторий

```bash
git init
git add .
git commit -m "Initial KURGIN Platform MVP"
git branch -M main
git remote add origin <YOUR_REPOSITORY_URL>
git push -u origin main
```

## Формат каталога

Минимальные колонки:

| column | meaning |
|---|---|
| `stone_id` | уникальный ID |
| `type` | тип камня |
| `carat` | вес |
| `color` | цвет |
| `clarity` | чистота |
| `cut` | огранка/качество |
| `certificate` | лаборатория |
| `price_usd` | цена |
| `availability` | наличие |

Полный шаблон доступен на странице **Data Quality**.

## KURGIN Score

Формула находится в `kurgin/formula.py`.

Компоненты:

- `quality_score` — качество: цвет, чистота, огранка, полировка, симметрия, флуоресценция, сертификат.
- `value_score` — относительная цена за карат внутри peer-группы.
- `risk_score` — доступность, надежность сертификата, полнота данных.
- `kurgin_score` — итоговая взвешенная оценка 0–100.

Это стартовая MVP-логика. Ее можно заменить на вашу proprietary-формулу без изменения UI.

## Локальное хранение

Избранное сохраняется в:

```text
.kurgin/kurgin.db
```

Файл не коммитится в Git.

## Проверка проекта

```bash
python scripts/validate_project.py
pytest
```

## Деплой

Подходит для Streamlit Community Cloud, Render, Railway или любого VPS, где доступен Python 3.10+.

Команда запуска:

```bash
python -m streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

## Важно

В этой сборке нет платежей. Нет Stripe, PayPal, YooKassa, CloudPayments, checkout-страниц, подписок, billing webhooks или скрытой монетизации.
