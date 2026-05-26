# KURGIN_PRICING_ENGINE_SPEC_V1

## 1. Назначение документа

Документ фиксирует Pricing Engine V1 для KURGIN Admin MVP до дальнейшей реализации.

Pricing Engine V1 — внутренний admin-side service layer для расчёта ориентировочной цены. Он помогает администратору подготовить цену, но не подтверждает финальную публичную цену автоматически.

Ключевой принцип:

```text
Index помогает админу назначить цену.
Финальную публичную цену подтверждает KURGIN.
calculated_price_rub ≠ confirmed_public_price_rub.
```

---

## 2. Source of Truth / границы продукта

KURGIN — controlled commerce and analysis platform for laboratory diamonds / lab-grown diamonds.

MVP catalog допускает только контролируемые камни:

```text
loose lab-grown stones
KURGIN-owned / KURGIN-controlled
physically received
checked
verified available
approved independent laboratory document
confirmed price
confirmed availability
```

Обязательные разграничения:

```text
Catalog Price = confirmed KURGIN price на конкретный камень.
KURGIN Index = market benchmark / рыночный ориентир.
Index ≠ exact price.
Index ≠ appraisal.
Index ≠ financial index.
Index ≠ forecast.
Index ≠ price guarantee.
KURGIN Score / Karo Score = quality interpretation, не финансовый рейтинг.
Analyzer ≠ price valuation.
public_visible ≠ public_sellable.
request_price ≠ checkout.
checkout_enabled только если price_confirmed and availability_confirmed.
```

---

## 3. Updated Pricing Engine V1 scope

Pricing Engine V1 применяется только к части каталога:

```text
section = main / large
non-colored stones only
carat >= 1 ct
carat <= примерно 5 ct
```

Исключения из V1:

```text
colored stones → не считаются Pricing Engine V1
small / medium stones < 1 ct → не считаются, будут позже
exclusive stones > 5 ct → отдельный future-процесс
side / pairs / fancy / special categories → позже
```

Камни больше 5 ct должны уходить в `exclusive`, а не в обычный Pricing Engine V1.

Публично не обязательно писать, что Index V1 только Round, но внутри админской логики это должно быть зафиксировано.

---

## 4. Что можно и нельзя публично

### Можно публично

Можно показывать камень как `public_visible`, если он проходит базовые publication flags, но ещё не готов к покупке.

Для request-only item:

```text
public_visible = True
public_sellable = False
checkout_enabled = False
public_action = request_price
```

Публичный CTA:

```text
Запросить цену
```

### Нельзя публично

Нельзя показывать:

```text
0 ₽
```

Нельзя включать checkout, если:

```text
price_rub <= 0
confirmed_public_price_rub <= 0
price_confirmed != True
availability_confirmed != True
current_status != available
```

Нельзя показывать calculated price как confirmed public price.

---

## 5. public_visible vs public_sellable

### public_visible

`public_visible` означает: камень можно показать в каталоге как витрину / preview / item по запросу.

Условия:

```text
base_public_flags = True
current_status = available
```

Если цены нет:

```text
price_status = missing / request_price / score_required
public_visible = True
public_sellable = False
checkout_enabled = False
public_action = request_price
```

### public_sellable

`public_sellable` означает: камень можно вести к покупке.

Условия:

```text
base_public_flags = True
current_status = available
confirmed_public_price_rub > 0
price_confirmed = True
availability_confirmed = True
```

---

## 6. Common base price table

В админке загружается общая таблица базовых цен.

Формат хранения на текущем этапе:

```text
Excel / CSV в админке
```

Значения таблицы:

```text
USD за карат
```

Таблица общая для всех форм внутри scope:

```text
section = main / large
non-colored
1–5 ct
```

Минимальная структура:

```text
price_table_version
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

`shape` можно оставить как future/optional поле, но Pricing Engine V1 не требует отдельной таблицы для каждой формы.

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

Для V1 рабочий диапазон:

```text
1.00 <= carat <= примерно 5.00
```

---

## 8. Round coefficient rule

Для:

```text
shape = Round
section = main / large
non-colored
1–5 ct
```

используется KURGIN Score coefficient.

Score bands:

```text
0 <= score < 50        → 0.5
50 <= score < 70       → 0.7
70 <= score < 80       → 0.8
80 <= score < 90       → 1.0
90 <= score < 95       → 1.2
95 <= score < 98.5     → 1.4
98.5 <= score <= 100   → 1.7
```

Public display:

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

## 9. Non-Round coefficient rule

Для non-Round внутри main/large:

```text
score_coefficient = 1
price считается по общей таблице / индексу
Index V1 публично не считается
```

Это не делает non-Round камень Index-priced публичным товаром.

---

## 10. Colored / exclusive / small / medium exclusions

Исключения:

```text
colored stones → не считаются
carat < 1 ct → не считаются в V1
carat > примерно 5 ct → exclusive / separate process
small / medium → future
exclusive → future/manual
```

Для excluded stones:

```text
price_status = request_price / blocked / future_scope
public_sellable = False until confirmed manually
checkout_enabled = False unless confirmed by separate process
```

---

## 11. Upload-blocking rule for Round main/large without KURGIN Score

Если:

```text
shape = Round
section = main / large
```

и KURGIN Score отсутствует:

```text
import_status = blocked
price_status = score_required
error = KURGIN Score required
price cannot calculate
public_sellable = False
checkout_enabled = False
```

Такие камни не должны проходить загрузку Excel как нормальная партия.

---

## 12. USD/RUB manual rate + CBR reference

Курс USD/RUB вводится вручную в админке:

```text
manual_usd_rub_rate
```

Рядом позже может показываться справочный курс:

```text
reference_cbr_usd_rub_rate
```

Правила:

```text
Reference CBR rate не меняет курс автоматически.
Финальный курс подтверждает админ.
Pricing calculation использует manual_usd_rub_rate.
```

Поля:

```text
manual_usd_rub_rate
reference_cbr_usd_rub_rate
rate_warning_threshold_rub
rate_warning
rate_difference_rub
usd_rub_rate_version
rate_source
rate_date
admin_rate_note
```

---

## 13. Rate warning threshold

Если разница между ручным курсом и reference CBR курсом больше threshold:

```text
rate_warning = True
```

Default threshold:

```text
rate_warning_threshold_rub = 3 ₽
```

Это предупреждение не блокирует расчёт автоматически, но требует внимания администратора.

---

## 14. Use CBR rate action

В будущем нужна кнопка:

```text
Использовать курс ЦБ
```

Правило:

```text
кнопка только копирует reference_cbr_usd_rub_rate в manual_usd_rub_rate после действия админа.
автоматически курс не меняется.
```

Сейчас не делать:

```text
UI курса
онлайн CBR API
автоматическое обновление курса
```

---

## 15. Formula V1 with global adjustment

Формула должна быть controlled template, не Python/eval.

Запрещено:

```text
free Python formula
eval
arbitrary expression execution
automatic price confirmation
```

Формула:

```text
raw_price_rub =
base_price_usd_per_carat
× carat
× manual_usd_rub_rate
× score_coefficient
× global_price_multiplier
```

Глобальная корректировка:

```text
global_price_multiplier = 1 + global_price_adjustment_percent / 100
```

Поля:

```text
formula_version = pricing_formula_v1
formula_display = base_price_usd_per_carat × carat × manual_usd_rub_rate × score_coefficient × global_price_multiplier
global_price_adjustment_percent
global_price_multiplier
```

---

## 16. Rounding rule

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

## 17. Empty base price cell rule

Если ячейка базовой таблицы пустая:

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

## 18. Pricing run + mass confirmation + publish workflow

Workflow:

```text
1. Admin uploads/updates USD price table.
2. Admin enters manual_usd_rub_rate.
3. System may display reference_cbr_usd_rub_rate.
4. System shows rate_warning if difference > threshold.
5. Admin runs pricing_run.
6. System writes calculated_price_rub / index_price_hint separately.
7. Admin reviews errors and warnings.
8. Mass confirmation allowed only for calculated rows without errors.
9. Confirmation writes confirmed_public_price_rub and price_confirmed=True.
10. Site prices change only after pricing_run + confirmation + publish.
```

Important:

```text
calculated_price_rub не публикуется как confirmed price.
price_confirmed не ставится автоматически.
checkout не включается автоматически.
```

---

## 19. Calculated vs confirmed price

Обязательное разграничение:

```text
calculated_price_rub ≠ confirmed_public_price_rub
```

Смысл полей:

```text
index_price_hint = ориентир от Pricing Engine / Index
raw_calculated_price_rub = сырой расчёт до округления
calculated_price_rub = расчёт после округления
admin_final_price_rub = цена, выбранная админом после проверки
confirmed_public_price_rub = финальная публичная цена KURGIN
price_confirmed = ручное подтверждение цены
availability_confirmed = ручное подтверждение наличия
```

---

## 20. Price statuses

Допустимые статусы:

```text
missing
request_price
score_required
calculated
needs_review
confirmed
blocked
future_scope
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
future_scope = вне Pricing Engine V1
```

---

## 21. Required admin fields

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
manual_usd_rub_rate
reference_cbr_usd_rub_rate
rate_warning_threshold_rub
rate_warning
rate_difference_rub
usd_rub_rate_version
score_band_version
formula_version
formula_display
global_price_adjustment_percent
global_price_multiplier
pricing_run_timestamp
```

---

## 22. Required catalog.json fields

В публичный `catalog.json` должны уходить:

```text
price_rub
confirmed_public_price_rub
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

## 23. Audit log requirements

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
manual_usd_rub_rate
reference_cbr_usd_rub_rate
rate_warning
rate_warning_threshold_rub
global_price_adjustment_percent
score_band_version
formula_version
pricing_run_timestamp
```

Минимальные действия:

```text
pricing_table_uploaded
manual_usd_rub_rate_changed
reference_cbr_rate_loaded
pricing_run_started
pricing_run_completed
pricing_run_error
mass_price_confirmation
price_confirmed
availability_confirmed
catalog_published
```

---

## 24. Проверка активных репозиториев

### kurgin-admin-mvp

Current admin has publication/pricing separation. Pricing Engine V1 must remain inside admin-side code and must not be placed into public UI.

### kurgin-data

Published `catalog.json` remains downstream data. New prices should enter it only after pricing run + confirmation + publish.

### kurgin-streamlit-mvp

Public site must treat request_price as request-only and must not display 0 ₽. Public site should not present Index as exact price.

---

## 25. TOP-10 professional audit

1. Architecture: Pricing Engine must stay admin-side service layer, not public UI logic.
2. Data: calculated price and confirmed price must remain separate fields.
3. Product: request_price must not look like checkout.
4. Legal-tech: Index must not be exact price, appraisal, financial index, forecast, or guarantee.
5. Operations: mass confirmation allowed only for calculated rows without errors.
6. Admin UX: rate_warning must be visible before confirmation.
7. Scope: colored, <1 ct, >5 ct, exclusive are out of V1 scope.
8. QA: tests required for rate warning, global adjustment, score_required blocking, rounding, bands.
9. DevOps: no online CBR API until explicit infrastructure step.
10. MVP discipline: do not start SQLite, Index UI, checkout, or publication changes now.

---

## 26. Короткий диагноз

Pricing Engine V1 is now defined as a controlled admin-side pricing workflow for non-colored main/large stones from 1 to about 5 ct.

Round stones use KURGIN Score coefficient. Non-Round stones use coefficient 1. Colored, small, medium, exclusive and >5 ct stones are outside V1 scope.

Main risk: accidentally treating calculated_price_rub as confirmed_public_price_rub or letting request_price items look sellable.

---

## 27. Предупреждения

```text
⚠️ Не публиковать price_rub = 0 как обычную цену.
⚠️ Не включать checkout для request_price.
⚠️ Не считать Index финальной ценой.
⚠️ Не подтверждать price_confirmed автоматически.
⚠️ Не делать pricing formula через eval / free Python.
⚠️ Не подключать онлайн ЦБ API сейчас.
⚠️ Не делать UI курса сейчас.
⚠️ Не начинать Index UI, SQLite, checkout или catalog publish.
```

---

## 28. Один главный следующий шаг после обновления spec

Следующий шаг:

```text
обновить admin_pricing_rules.py под новую спецификацию
```

Только чистые rules:

```text
manual_usd_rub_rate
reference_cbr_usd_rub_rate
rate_warning_threshold_rub default 3 ₽
global_price_adjustment_percent
Round main/large score blocking
non-colored main/large 1–5 ct scope
calculated vs confirmed separation
```

Без UI, без SQLite, без онлайн CBR API, без Index UI, без checkout, без публикации catalog.json.

---

## 29. Что не делать сейчас

```text
не делать admin UI для курса
не подключать реальный онлайн API ЦБ
не публиковать новые цены
не делать Index UI
не начинать SQLite
не включать checkout
не менять публичный сайт до поддержки request_price / checkout_enabled
```