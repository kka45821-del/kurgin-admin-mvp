# KURGIN Admin Rules — Stage 03

Этап 3 — Поставки.

Добавлено: общая сводка по поставкам, supplier_id, карточка поставки, сводка по камням, платежи, вложения до 5 файлов, скачивание вложений.

Не входит: CRM, личный кабинет поставщика, бухгалтерия, публикация, экспорт.


## Сводка ассортимента

В разделе «Камни» добавлен блок «Сводка ассортимента».

Колонки:
Форма, Диапазон веса, Цвет, Чистота, Всего, В наличии, Забронировано, Продано, Снято, Архив.


## Этап 4 — Конфликты ID

Report # уникален. Один Report # = один камень.

Если при новой загрузке совпал Report #, это конфликт.

Действия:
- исправить Report # в новой строке;
- обновить существующий камень;
- пропустить строку;
- отменить импорт.

Ручные поля не перезаписываются молча.


## Этап 5 — Разделы каталога

Только main и large. Редактируются названия, is_public, sort_order, comment. Камни вручную между разделами не переносим.


## Этап 6A — Настройки цен

Раздел «Цены» пока только сохраняет исходные таблицы.

Не делает финальный расчёт по камням, Index, просмотр маржи, публикацию или экспорт.


## 6A.1 — Таблица цены поставщика

Для удобства ввода цена поставщика отображается матрицами:

- цвет отдельным блоком;
- строки = чистота;
- колонки = диапазоны веса.

Формулы и правила Этапа 6 не меняются.


## Этап 6B — Расчёт корневых цен

Вкладка «Расчёт USD» показывает корневые цены за карат.

Формулы:

- внутренняя = цена поставщика × (1 + активные расходы);
- стартовая = внутренняя + стартовая маржа;
- рабочая = стартовая + рабочая маржа;
- публичная = рабочая + публичная маржа.

Без KURGIN Score, Index и финальных цен по камням.


## Этап 6C — Index

Вкладка «Index» показывает публичную индексную цену:

```text
публичная цена за карат × выбранный KURGIN Score коэффициент
```

По умолчанию выбран:

```text
Стандартный ×1.00
```

Для RUB в публичном Index округление идёт вверх до 100 ₽.

Финальные цены по камням, просмотр маржи, публикация и экспорт не входят в 6C.


## 6C.1 — Описание формул цен

В интерфейсе «Цены» должен быть блок «Как считаются цены», чтобы пользователь видел логику расчёта:

- цена поставщика;
- внутренняя цена;
- стартовая цена;
- рабочая цена;
- публичная цена;
- Index с KURGIN Score;
- округление RUB.

Этот блок информационный. Формулы и данные не меняет.


## 6B.1 — Понятные маржи и защита пустой цены поставщика

Маржи в интерфейсе называются:

- Маржа 1 — стартовая;
- Маржа 2 — рабочая;
- Маржа 3 — публичная.

Формулы:

```text
Стартовая цена = Внутренняя цена + Маржа 1
Рабочая цена = Стартовая цена + Маржа 2
Публичная цена = Рабочая цена + Маржа 3
```

Если цена поставщика пустая или 0, внутренняя, стартовая, рабочая, публичная и Index-цена не рассчитываются.


## 6C.3 — Комментарии к Index

В интерфейсе нужно различать:

- Index по цветам — основной удобный вид таблицы;
- Полная таблица Index — техническая проверка расчёта.

Полная таблица нужна для проверки формулы, курса, коэффициента KURGIN Score и округления.


## 6C.4 — Логический порядок вкладок цен

Вкладки цен должны идти по цепочке расчёта:

Цена поставщика → Расходы → Внутренняя цена → Маржа 1 → Маржа 2 → Маржа 3 → KURGIN Score → Курсы валют → Расчёт USD → Index.

Маржи разделяются:

- Маржа 1 — стартовая;
- Маржа 2 — рабочая;
- Маржа 3 — публичная.


## 6C.5 — Цепочка цен по вкладкам

Вкладки цен должны идти в порядке расчёта:

Цена поставщика за карат → Расходы → Внутренняя цена за карат → Маржа 1 → Стартовая цена за карат → Маржа 2 → Рабочая цена за карат → Маржа 3 → Публичная цена за карат → KURGIN Score → Курсы валют → Index.

Каждая расчётная цена должна иметь текстовую формулу и удобную таблицу по диапазонам веса.


## 6C.6 — Полные диапазоны веса

В таблицах цен нужно показывать полные диапазоны веса, а не короткие значения.

Правильно:

- 1.00–1.49
- 1.50–1.99
- 2.00–2.49
- 2.50–2.99
- 3.00–3.99
- 4.00–4.99
- 5.00+

Это интерфейсное правило. Формулы не меняет.


## 6C.7 — Округление RUB Index до 100 ₽

Публичный Index в RUB округляется вверх до 100 ₽.

Пример:

- 22 650 ₽ → 22 700 ₽
- 22 601 ₽ → 22 700 ₽
- 22 600 ₽ → 22 600 ₽

Формулы расчёта не изменены.


## 6D — Просмотр маржи по камням

Вкладка «Просмотр маржи» — это контрольный экран, а не настройка цен.

Единственное управление:

- валюта отображения: RUB / USD / INR.

Редактирование запрещено:

- цены;
- маржи;
- коэффициенты;
- курсы;
- данные камня.

Если цена поставщика не найдена по диапазону веса + цвету + чистоте, цены по камню не рассчитываются.

Если ROUND камень не имеет KURGIN Score, показывать предупреждение «Нет KURGIN Score».


## 6E.1 — Компактная навигация цен

Раздел «Цены» не должен использовать длинную строку вкладок.

Навигация должна быть сгруппирована:

- База цены
- Маржи
- Расчётные цены
- Коэффициенты и валюты
- Index и просмотр

Это нужно для удобства и переносимости интерфейса на разные размеры экрана.


## 7B — Предпросмотр записи цен

Страница «Запись цен» в 7B ничего не записывает.

Она только показывает предпросмотр будущей записи цен.

Запись в stones_master.csv будет только на этапе 7C после отдельного подтверждения.


## 7B.1 — Исправление предпросмотра записи цен

Предпросмотр записи цен должен использовать тот же расчётный статус, что и «Просмотр маржи».

Если «Просмотр маржи» показывает камень как рассчитанный, он должен попадать в таблицу будущей записи цен.

Если статус «Нет цены поставщика», камень должен попадать в блок «Камни без рассчитанной цены».

7B.1 всё ещё ничего не записывает в stones_master.csv.

## 7C — Подтверждение и запись итоговых цен

Фактическая запись итоговых цен разрешена только после предпросмотра и явного подтверждения.

Обязательный поток:

```text
предпросмотр
↓
контрольная подпись предпросмотра
↓
чекбокс подтверждения
↓
фраза ЗАПИСАТЬ ЦЕНЫ
↓
backup
↓
запись в stones_master.csv
```

Ручные цены:

```text
price_source = manual
```

не перезаписываются действием 7C.

Камни без цены поставщика получают только служебный статус:

```text
price_source = not_calculated
price_status = missing_supplier_price
price_warning = Нет цены поставщика
```

Числовые price-поля для таких камней должны быть пустыми.

Основная запись цен не включает «Цена по запросу»: `allow_price_on_request = true` и `public_price_display = Цена по запросу` ставятся только отдельным массовым действием после предпросмотра, отдельного подтверждения и отдельного backup.
## Checkpoint 25 — Stage 7C completed and locked

Checkpoint 25 — стабильная точка после завершения Stage 7C.

Правильный порядок следующих работ:

```text
1. Проверить, что 7C завершён и работает.
2. Зафиксировать правила и ограничения после 7C.
3. Сделать checkpoint ZIP по состоянию после 7C.
4. Только потом обсуждать 7D.
5. Сначала согласовать правила 7D.
6. Только после этого делать ZIP с кодом 7D.
```

7C считается завершённым, если выполнено:

```text
7C работает в Streamlit
перед записью создаётся backup
запись цен в stones_master.csv требует ручного подтверждения
ручные цены не перезаписываются молча
камни без цены поставщика не получают числовую цену
“Цена по запросу” не включается автоматически
```

Записываемые 7C price-поля:

```text
supplier_price_per_ct_usd
internal_price_per_ct_usd
start_price_per_ct_usd
working_price_per_ct_usd
public_price_per_ct_usd
supplier_price_total_usd
internal_price_total_usd
start_price_total_usd
working_price_total_usd
public_price_total_usd
supplier_price_total_rub
internal_price_total_rub
start_price_total_rub
working_price_total_rub
public_price_total_rub
price_currency_base
price_fx_usd_rub
price_calculated_at
price_status
price_warning
price_source
public_price_display
allow_price_on_request
```

Правила защиты после 7C:

```text
price_source = manual не перезаписывать без отдельного правила
missing_supplier_price не получает числовую цену
allow_price_on_request не включать основной записью цен
“Цена по запросу” включать только отдельным подтверждением
перед любым действием записи нужен backup
preview должен быть актуальным
runtime data не добавлять в кодовый commit
```

В следующих Changes не должно быть:

```text
data/
backups/
exports/
__pycache__/
tmp/
current_working_code/
тестовые файлы
```

Что ещё не сделано:

```text
публикация
публичный слой каталога
экспорт для сайта
автоматический sync
правила отбора камней для публичного отображения
```

7D пока не реализован. Перед 7D нужно отдельно согласовать правила публикации и публичного слоя:

```text
какие камни попадают в публичный слой
какие камни исключаются
как учитывать status
как учитывать availability_status
как учитывать catalog_section
как учитывать скрытые разделы
как учитывать allow_price_on_request
как учитывать price_status и public_price_display
что именно экспортируется наружу
```

Код 7D нельзя писать до подтверждения этих правил.


## 7D.0 — Unified KURGIN Report / PDF / Assets foundation

7D.0 — только документационный foundation. Код, PDF, exports, asset manager и изменения CSV-схемы в 7D.0 запрещены.

Правильный порядок после checkpoint 25:

```text
1. Checkpoint 25 — Stage 7C completed / rules locked.
2. 7D.0 — docs-only foundation для Unified Report / PDF / Assets.
3. 7D — правила публичного слоя.
4. 7E — preview/audit публичного слоя в Admin.
5. 7F / 8A — export/public card schema.
6. V1 release — без PDF generator.
7. V2 — общий PDF generator.
```

### Единый PDF/report принцип

Запрещено создавать независимые PDF-генераторы для:

```text
Admin
private analyzer
public stone analyzer
mass analyzer
catalog stone card
```

Разрешённая будущая архитектура:

```text
ReportPayloadV1
↓
ReportMode
↓
Visibility Policy
↓
Unified KURGIN Report / PDF generator
↓
PDF bytes/file + metadata
```

Существующая PDF/report-логика в analyzer считается prototype / candidate source. Она не должна становиться отдельным production generator для сайта и Admin.

### ReportMode

Канонические режимы:

```text
internal_admin
private_analyzer
public_stone_analyzer
mass_analyzer_row
catalog_stone_card
```

`catalog_stone_card` имеет два будущих уровня:

```text
summary_view
detail_view
```

### Public catalog card summary

Будущая карточка камня на сайте должна иметь минимальный public-safe набор:

```text
shape
carat
color
clarity
kurgin_score
public_price_display
min_diameter
max_diameter
height
cut_grade
symmetry
polish
fluorescence
tags
```

Цена является частью будущей публичной карточки, но только как готовое публичное отображение. Карточка не считает цену.

Детальная карточка после клика может показывать:

```text
ту же карточку
расширенные public-safe details
KURGIN Analyzer Report PDF / report reference
lab report reference
фото / видео / future assets
```

Карточка камня не генерирует PDF. PDF generator не генерирует карточку. Оба будущих слоя используют общий `ReportPayloadV1` и visibility rules.


### Price visibility contexts — future-only

`ReportMode` не должен смешиваться с ценовыми правами. Для будущих кабинетов и публичного сайта нужно отдельно держать `PriceVisibilityContext`.

Канонические будущие контексты:

```text
internal_admin
specialist_private
specialist_client_view
public_catalog
public_analyzer
```

Правила:

```text
public_catalog показывает только public_price_display или разрешённую “Цена по запросу”.
specialist_private может иметь будущую профессиональную цену, но не обязан видеть supplier/internal Admin cost.
specialist_client_view является клиентским безопасным режимом и не должен раскрывать specialist margin, specialist purchase price, supplier price, internal price, working price или admin price metadata.
public_analyzer обычно не показывает цену каталога, если анализируемый камень явно не связан с публичной карточкой.
PDF generator, карточка и сайт не считают цены. Все price display должны приходить из Admin/export price policy.
```

В V1 не реализуются:

```text
specialist pricing
price tiers
account-specific price calculation
specialist cabinet
client-view cabinet
```

### PDF generator — запреты

Будущий generator не должен:

```text
считать цены
менять stones_master.csv
менять status
менять availability_status
менять catalog_section
включать allow_price_on_request
публиковать камень
создавать заказ / резерв / покупку
раскрывать внутреннюю формулу
зависеть необратимо от Streamlit Cloud
```

### PDF generator — обязанности будущего V2

Будущий generator должен:

```text
принимать готовый ReportPayloadV1
применять visibility policy
создавать PDF bytes/file
возвращать report_id
возвращать report_status
возвращать template_version
возвращать created_at
быть переиспользуемым между Admin, Analyzer и сайтом
```

### V1 boundary

В V1 фиксируются только правила и контракт:

```text
ReportPayloadV1
ReportMode
visibility rules
Catalog Stone Card Contract
future report_refs
future asset_refs
future stone_assets.csv concept
```

В V1 запрещено делать:

```text
PDF generation
PDF viewer
PDF upload
active asset manager
active stone_assets.csv
automatic KURGIN Report creation
public site PDF integration
separate kurgin-report-core package
```

### V2 boundary

На V2 остаётся:

```text
общий PDF generator
kurgin-report-core или аналогичный общий пакет
PDF bytes/file generation
PDF viewer
report storage lifecycle
active stone_assets.csv
asset manager
lab report linking
photos/videos/gallery
интеграция отчёта в детальную карточку сайта
```

Подробный foundation-документ должен находиться в:

```text
docs/UNIFIED_KURGIN_REPORT_FOUNDATION_V1.md
```

## 7D — Public Layer Rules

7D is rules-only. Code, exports, sync, PDF generation, asset manager and CSV mutation are forbidden in this stage.

### Public eligibility baseline

A stone may enter the future public catalog layer only if:

```text
status = published
availability_status = in_stock
catalog_section is not empty
catalog_section exists in catalog_sections.csv
catalog_sections.is_public = true
```

If any condition is false, the stone is not public.

### Status rules

```text
draft      → not public
ready      → ready inside Admin, but not public
published  → may continue public checks
archived   → not public
```

### Availability rules

```text
in_stock  → may continue public checks
reserved  → not public in V1
sold      → not public
removed   → not public
```

### Section rules

```text
catalog_section empty        → hidden by section
catalog_section not found    → data problem
is_public != true            → hidden by section
is_public = true             → may continue public checks
```

### Price rules

Price is part of the public stone card, but only as prepared public display.

Allowed public price field:

```text
public_price_display
```

Forbidden public price/internal fields:

```text
supplier price
internal price
start price
working price
margin
price_source
price_fx_usd_rub
price_calculated_at
admin price metadata
```

Numeric public price is allowed only when:

```text
price_status = calculated
public_price_display is filled
public_price_total_rub is filled
```

“Цена по запросу” is allowed only when:

```text
price_status = missing_supplier_price
allow_price_on_request = true
public_price_display = Цена по запросу
```

If `price_status = missing_supplier_price` and `allow_price_on_request != true`, the stone must not enter the public commercial catalog.

### Future public card summary

```text
shape
carat / weight
color
clarity
kurgin_score
public_price_display
min_diameter
max_diameter
height / depth_mm
cut_grade
symmetry
polish
fluorescence
tags
```

Required blockers for V1 public card:

```text
shape
weight
color
clarity
kurgin_score
public_price_display
```

Warning-only fields for V1:

```text
min_diameter
max_diameter
height / depth_mm
cut_grade
symmetry
polish
fluorescence
tags
```

### Future public-layer audit groups

```text
Public OK — numeric price
Public OK — price on request
Ready but not published
Hidden by status
Hidden by availability_status
Hidden by catalog_section
Missing price
Manual price review
Data problems
```

Full rules are documented in:

```text
docs/PUBLIC_LAYER_RULES_V1.md
```

Next code stage must be separate:

```text
7E — Admin preview/audit of the public layer
```

## 7E — Admin preview/audit публичного слоя

7E implements a read-only Admin UI preview/audit for the future public layer.

Location:

```text
Цены → Index и просмотр → Публичный слой
```

Allowed in 7E:

```text
read stones_master.csv
read catalog_sections.csv
apply 7D public-layer rules
show public-safe preview rows
show audit groups
show data problems
show warnings/manual review
filter/search audit table
```

Forbidden in 7E:

```text
write stones_master.csv
write catalog_sections.csv
create backup
write exports/
sync with site
change status
change availability_status
change catalog_section
change prices
turn on allow_price_on_request
create PDF
create asset manager
create orders/reserves/payments
```

7E audit groups:

```text
Public OK — numeric price
Public OK — price on request
Ready but not published
Hidden by status
Hidden by availability_status
Hidden by catalog_section
Missing price
Manual price review
Data problems
```

7E must keep business logic portable:

```text
modules/storage.py → build_public_layer_preview()
app.py → display only
```

7E does not create public export/schema. Export/public card schema remains a later stage:

```text
7F / 8A — export/public card schema
```

## 7E.1 — Public layer UI fixes

7E.1 is a small UI/data-clarity fix after testing 7E.

Allowed in 7E.1:

```text
show recorded KURGIN Score ranges in the coefficient table
show KURGIN Score ranges in Index labels and technical Index table
show KURGIN Score ranges in public-layer audit
separate KURGIN Score coefficients and currency rates into separate top-level price navigation buttons
render empty/none-like fluorescence values as None
```

KURGIN Score ranges for V1:

```text
poor            <60
fair            60–69.99
standard        70–79.99
high            80–89.99
premium         90–94.99
elite           95+
not_calculated  Не рассчитано
```

Fluorescence rule:

```text
None is a real fluorescence value.
If fluorescence is blank or none-like in display/audit, show None, not an empty cell.
```

Forbidden in 7E.1:

```text
change price formulas
recalculate or write final prices
write exports
create backups as part of audit
change stones_master.csv from the public-layer page
change status / availability_status / catalog_section
turn on allow_price_on_request
publish or sync stones
create PDF/assets
```

## 7F.0 — Public Export / Public Card Schema Contract

7F.0 is docs-only. It defines the future public export and public card schema contract. Code, export files, sync, site integration, PDF/assets and CSV mutation are forbidden in this stage.

Stable base:

```text
Checkpoint 29 — Stage 7E.1 Public Layer UI Fixes
```

### Purpose

7F.0 defines what Admin may later export for the public site/catalog card.

Intended future flow:

```text
KURGIN Admin
↓
7E public-layer preview/audit
↓
7F public export preview/download
↓
8A controlled publish path
↓
kurgin-data
↓
public site / catalog card
```

### Future export file

Canonical future export file:

```text
public_stones_v1.csv
```

This file must be versioned and must not silently replace legacy/current `stones.csv` until the public site is explicitly migrated.

### Allowed public export rows

Only rows that pass the 7D / 7E public-layer rules may enter `public_stones_v1.csv`.

Allowed export statuses:

```text
public_numeric_price
public_price_on_request
```

Internal audit-only states must not be exported as public rows:

```text
not_public
data_problem
hidden_by_status
hidden_by_availability_status
hidden_by_catalog_section
missing_price
ready_but_not_published
```

### Public card schema fields

Future public card/export may include:

```text
schema_version
exported_at
stone_id
report_number
lab
catalog_section
section_name
public_card_status
public_visibility_reason
shape
weight
carat_label
color
clarity
kurgin_score
kurgin_score_range_label
public_price_display
price_display_type
min_diameter
max_diameter
height
depth_mm
cut_grade
symmetry
polish
fluorescence
tags
availability_status_public
detail_available
kurgin_report_available
lab_report_available
main_image_available
```

### Price display contract

The public site must show only:

```text
public_price_display
```

Canonical `price_display_type` values:

```text
numeric
price_on_request
```

The public site, card UI and PDF generator must not calculate price.

### Forbidden export fields

Future public export must not include:

```text
supplier_price_*
internal_price_*
start_price_*
working_price_*
price_fx_usd_rub
price_calculated_at
price_source
price_warning
admin_note
price_comment
shipment_id
supplier_id
supplier_name
import_id
updated_import_id
last_source_file
raw_source_file
margins
expense coefficients
formula internals
formula thresholds
formula penalties
raw diagnostics
breakdown
private API keys
private service URLs
```

### kurgin-data boundary

7F.0 does not write to `kurgin-data`.

A later controlled publish stage may write public data there only after:

```text
public_stones_v1.csv schema is accepted
Admin preview/download is tested
site reader compatibility is confirmed
rollback/manual restore path is known
```

### Future-only flags

Public export may reserve future flags:

```text
detail_available
kurgin_report_available
lab_report_available
main_image_available
```

V1 still does not implement:

```text
PDF generation
PDF upload/viewer
asset manager
active stone_assets.csv
lab report storage
photo/video/gallery storage
```

Full contract is documented in:

```text
docs/PUBLIC_EXPORT_CONTRACT_V1.md
```

Next implementation stage must be separate:

```text
7F — Admin in-memory public export preview/download
```

7F must still be safe: build downloadable public export from memory only, without writing `exports/`, without writing `kurgin-data`, without sync and without mutating `stones_master.csv`.
