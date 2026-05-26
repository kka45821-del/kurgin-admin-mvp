# KURGIN_PRICING_ENGINE_SPEC_V1

## 1. Назначение документа

Этот документ фиксирует Pricing Engine V1 для KURGIN Admin MVP.

Цель документа — до написания кода зафиксировать границы, правила, статусы, поля данных и запреты, чтобы Pricing Engine не превратился в неявный Index, оценку стоимости, финансовый рейтинг или автоматическую публичную цену.

Pricing Engine V1 — это внутренний административный инструмент расчёта ориентировочной цены. Он помогает администратору назначить цену, но не подтверждает финальную публичную цену автоматически.

Ключевой принцип:

```text
Index помогает админу назначить цену.
Финальную публичную цену подтверждает KURGIN.
```

---

## 2. Source of Truth / границы продукта

KURGIN — controlled commerce and analysis platform for laboratory diamonds / lab-grown diamonds.

MVP catalog допускает только камни, которые соответствуют контролируемым требованиям:

```text
KURGIN-owned
physically received
checked
verified available
loose lab-grown stones
approved independent laboratory document
confirmed price
confirmed availability
```

Обязательные разграничения:

```text
Catalog Price = подтверждённая цена KURGIN на конкретный камень.
KURGIN Index = рыночный ориентир / market benchmark.
Index ≠ exact price.
Index ≠ appraisal.
Index ≠ financial index.
Index ≠ price guarantee.
KURGIN Score / Karo Score = quality interpretation, не финансовый рейтинг.
Analyzer ≠ price valuation.
Request-only / no-price item must not look like ordinary checkout item.
public_visible ≠ public_sellable.
checkout_enabled только если price_confirmed and availability_confirmed.
```

---

## 3. Что можно и нельзя публично

### Можно публично

Можно показывать камень как `public_visible`, если он проходит базовые publication flags, но ещё не готов к покупке.

Для таких камней допустимое публичное действие:

```text
public_action = request_price
checkout_enabled = False
```

На сайте это должно отображаться как:

```text
Запросить цену
```

### Нельзя публично

Нельзя показывать:

```text
0 ₽
```

Нельзя включать обычный checkout, если:

```text
price_rub <= 0
price_confirmed != True
availability_confirmed != True
current_status != available
```

Нельзя называть расчётную цену Index точной ценой, оценкой, финансовым индексом, прогнозом или гарантией.

---

## 4. Два режима публичности

### 4.1 public_visible

`public_visible` означает: камень можно показать в каталоге как витрину, preview или item по запросу.

Условия:

```text
base_public_flags = True
current_status = available
```

Если цены нет, камень может быть visible только в request-only режиме:

```text
price_status = missing / request_price / score_required
public_visible = True
public_sellable = False
checkout_enabled = False
public_action = request_price
```

### 4.2 public_sellable

`public_sellable` означает: камень можно вести к покупке.

Условия:

```text
base_public_flags = True
current_status = available
price_rub > 0
price_confirmed = True
availability_confirmed = True
```

---

## 5. Базовая price table

В админке загружается таблица базовых цен.

Значения таблицы:

```text
USD за карат
```

Минимальная структура:

```text
price_table_version
shape
section
carat_band_from
carat_band_to
color
clarity
base_price_usd_per_carat
is_active
admin_note
created_at
updated_at
```

Для Pricing Engine V1 основной рабочий scope:

```text
shape = Round
section = main / large
```

Остальные формы могут быть в данных, но Index V1 для них пока не считается.

---

## 6. USD/RUB rate

В админке задаётся курс USD/RUB.

Обязательные поля:

```text
usd_rub_rate
usd_rub_rate_version
rate_source
rate_date
admin_rate_note
```

Правило:

```text
pricing run должен знать, какой курс использовался.
курс не должен применяться без версии.
```

---

## 7. Carat bands

Правило диапазонов:

```text
левая граница включительно
правая граница не включительно
```

Примеры:

```text
1.00 <= carat < 1.50
1.50 <= carat < 2.00
2.00 <= carat < 2.50
```

Публичное отображение:

```text
1.00–1.49
1.50–1.99
2.00–2.49
```

---

## 8. KURGIN Score bands and coefficients

Внутренние диапазоны и коэффициенты:

```text
0 <= score < 50        → 0.5
50 <= score < 70       → 0.7
70 <= score < 80       → 0.8
80 <= score < 90       → 1.0
90 <= score < 95       → 1.2
95 <= score < 98.5     → 1.4
98.5 <= score <= 100   → 1.7
```

Публичное отображение:

```text
0–49.99
50–69.99
70–79.99
80–89.99
90–94.99
95–98.49
98.5–100
```

Обязательная версия:

```text
score_band_version
```

---

## 9. Formula V1

Формула должна быть controlled template.

Запрещено:

```text
free Python formula
eval
arbitrary expression execution
```

Формула:

```text
pricing_formula_v1 =
base_price_usd_per_carat
× carat
× usd_rub_rate
× score_coefficient
```

Поля:

```text
formula_version = pricing_formula_v1
formula_display = base_price_usd_per_carat × carat × usd_rub_rate × score_coefficient
```

---

## 10. Rounding rule

Округление всегда вверх до 1 000 ₽.

Примеры:

```text
123 100 ₽ → 124 000 ₽
123 999 ₽ → 124 000 ₽
124 000 ₽ → 124 000 ₽
```

Поля:

```text
raw_calculated_price_rub
calculated_price_rub
rounding_rule = ceil_to_1000_rub
```

---

## 11. Empty-cell rule

Если ячейка базовой price table пустая:

```text
price_status = request_price / missing
public_visible = True
public_sellable = False
checkout_enabled = False
public_action = request_price
```

Публичный сайт:

```text
не показывает 0 ₽
показывает “Запросить цену”
```

---

## 12. Round main/large score-required rule

Если:

```text
shape = Round
section = main / large
```

то KURGIN Score обязателен для расчёта цены.

Если score отсутствует:

```text
price_status = score_required
calculated_price_rub = empty
public_sellable = False
checkout_enabled = False
public_action = request_price / ask_manager
```

---

## 13. Non-Round coefficient rule

Если камень не Round или не main/large:

```text
score_coefficient = 1
Index V1 не считается
```

Такой камень может быть в каталоге, но не должен выглядеть как Index-priced stone.

---

## 14. Index V1 Round-only rule

Index V1:

```text
только Round
только market benchmark
не точная цена
не appraisal
не financial index
не forecast
не price guarantee
```

Index может формировать `index_price_hint`, но не может автоматически создавать `confirmed_public_price_rub`.

---

## 15. Calculated vs confirmed price

Обязательное разграничение:

```text
calculated_price_rub ≠ confirmed_public_price_rub
```

Смысл полей:

```text
index_price_hint = ориентир от Index / Pricing Engine
raw_calculated_price_rub = сырой расчёт до округления
calculated_price_rub = расчёт после округления
admin_final_price_rub = цена, выбранная админом после проверки
confirmed_public_price_rub = финальная публичная цена KURGIN
price_confirmed = ручное подтверждение цены
availability_confirmed = ручное подтверждение наличия
```

Финальная публичная цена появляется только после admin confirmation.

---

## 16. Price statuses

Допустимые статусы:

```text
missing
request_price
score_required
calculated
needs_review
confirmed
blocked
```

Значения:

```text
missing = цены нет
request_price = цена только по запросу
score_required = нужен KURGIN Score для расчёта
calculated = расчёт сделан, но не подтверждён
needs_review = требуется проверка администратора
confirmed = цена подтверждена KURGIN
blocked = цену нельзя публиковать
```

---

## 17. Price sources

Допустимые источники:

```text
excel
manual
index_hint
supplier_quote
not_set
```

`index_hint` не равен финальной цене.

`supplier_quote` не равен публичной цене KURGIN.

---

## 18. Required admin fields

Минимальные поля в админке:

```text
price_rub
price_confirmed
availability_confirmed
price_source
price_status
index_price_hint
raw_calculated_price_rub
calculated_price_rub
admin_final_price_rub
confirmed_public_price_rub
admin_price_note
show_without_price
public_visible
public_sellable
checkout_enabled
public_action
price_table_version
usd_rub_rate
usd_rub_rate_version
score_band_version
formula_version
formula_display
pricing_run_timestamp
```

---

## 19. Required catalog.json fields

В публичный `catalog.json` должны уходить:

```text
price_rub
price_status
price_source
price_confirmed
availability_confirmed
public_visible
public_sellable
checkout_enabled
public_action
index_price_hint
calculated_price_rub
confirmed_public_price_rub
formula_version
price_table_version
usd_rub_rate_version
score_band_version
pricing_run_timestamp
```

Публичный сайт обязан соблюдать:

```text
if checkout_enabled = False → не показывать обычную покупку
if public_action = request_price → показывать “Запросить цену”
if price_rub = 0 → не показывать “0 ₽”
```

---

## 20. Audit log requirements

Каждый pricing run должен писать событие в audit log.

Поля события:

```text
created_at
action
entity
rows_count
source
result
details
price_table_version
usd_rub_rate_version
score_band_version
formula_version
pricing_run_timestamp
```

Минимальные действия:

```text
pricing_table_uploaded
usd_rub_rate_changed
pricing_run_started
pricing_run_completed
pricing_run_error
price_confirmed
availability_confirmed
catalog_published
```

---

## 21. Warnings for public site

Публичный сайт должен учитывать:

```text
не показывать 0 ₽
не включать checkout для request-only
не показывать Index как точную цену
не показывать calculated price как confirmed public price
не смешивать request_price и buy/checkout
```

Если:

```text
public_action = request_price
```

то CTA:

```text
Запросить цену
```

---

## 22. Проверка текущего состояния репозиториев

### kurgin-admin-mvp

Уже есть `admin_publication_rules.py` с разделением `public_visible_mask`, `public_sellable_mask`, `public_preview`.

`public_sellable` требует:

```text
price_rub > 0
price_confirmed = True
availability_confirmed = True
```

В `admin_io.py` уже добавлены price lifecycle поля:

```text
price_confirmed
availability_confirmed
price_source
price_status
index_price_hint
admin_final_price_rub
admin_price_note
show_without_price
```

### kurgin-data

Published data repo содержит `catalog.json`, который читается публичным сайтом.

Если в опубликованном `catalog.json` есть `price_rub = 0`, такой камень должен считаться request-only, а не sellable.

### kurgin-streamlit-mvp

Публичный сайт читает `catalog.json` из `kurgin-data`.

Следовательно, любые новые поля `public_sellable`, `checkout_enabled`, `public_action`, `price_status` должны быть поддержаны публичным UI до включения реальной продажи.

---

## 23. TOP-10 professional audit

1. Architecture: Pricing logic нельзя помещать в `app.py`.
2. Data: price lifecycle должен быть явным, не неявным через `price_rub = 0`.
3. Product: request-only item не должен выглядеть как ordinary checkout item.
4. Legal-tech: Index нельзя показывать как exact price / appraisal / financial index / guarantee.
5. Operations: availability_confirmed должно быть ручным операционным подтверждением.
6. Admin UX: calculated, needs_review, confirmed и blocked должны быть визуально различимы.
7. Public UX: 0 ₽ запрещено; нужен “Запросить цену”.
8. QA: нужны тесты на округление, bands, empty cell, score_required, sellable gate.
9. DevOps: pricing run должен сохранять версии таблицы, курса, score bands и формулы.
10. Future-proof: SQLite/SQLAlchemy делать после фикса rules, не до.

---

## 24. Короткий диагноз

Pricing Engine V1 нужен как admin-side pricing assistant, а не как автоматический public price engine.

Текущая архитектура уже сделала правильный шаг: `public_visible` и `public_sellable` разделены. Следующий риск — не зафиксировать Pricing Engine как версионированный controlled calculation и случайно превратить calculated price в public confirmed price.

---

## 25. Предупреждения

```text
⚠️ Не публиковать price_rub = 0 как обычную цену.
⚠️ Не включать checkout для request_price.
⚠️ Не считать Index финальной ценой.
⚠️ Не подтверждать price_confirmed автоматически после Excel.
⚠️ Не делать pricing formula через eval / свободный Python.
⚠️ Не начинать Index UI до фикса Pricing Engine rules.
```

---

## 26. Один главный следующий шаг после spec

Следующий шаг после этого документа:

```text
создать admin_pricing_rules.py
```

Сначала реализовать только чистые правила:

```text
score coefficient
carat band selection
rounding ceil_to_1000
empty-cell rule
score_required rule
calculated vs confirmed separation
```

Без UI, без SQLite, без Index-страниц, без checkout.

---

## 27. Что не делать сейчас

```text
не строить весь Index
не подключать оплату
не делать checkout
не делать supplier portal
не переносить всё на SQLite прямо сейчас
не добавлять роли
не делать paid Analyzer
не делать формулу через eval
не превращать calculated_price_rub в confirmed_public_price_rub
```
