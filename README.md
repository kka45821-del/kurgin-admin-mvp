# KURGIN Admin — Stage 02 Stones Management

Этап 2: управление камнями.

Сохраняет рабочую логику Этапа 1 и добавляет:

- фильтры в разделе «Камни»;
- поиск по `stone_id`, `KURGIN Import ID`, `Report #`, `Stock #`;
- карточку камня;
- просмотр всех raw-параметров Results / Details / Issues;
- редактирование только административных полей:
  - Раздел;
  - Статус записи;
  - Наличие;
  - Заметка администратора;
  - Комментарий проверки;
- backup перед сохранением изменений.

## Запуск

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Не входит в Этап 2

- полноценная система цен;
- публикация;
- экспорт;
- редактирование геммологических данных;
- фото/видео;
- клиентская карточка товара.


## Этап 3

Добавлены сводка поставок, карточка поставки, платежи и вложения.


## Добавлено

- блок «Сводка ассортимента» в разделе «Камни»;
- группировка по форме, диапазону веса, цвету и чистоте;
- подсчёт: всего, в наличии, забронировано, продано, снято, архив.


## Этап 4 — Конфликты ID и повторные загрузки

Добавлено:

- конфликт по совпадению `Report #`;
- экран конфликтов в предпросмотре импорта;
- действия:
  - исправить `Report #` в новой строке;
  - обновить существующий камень;
  - пропустить строку;
- массовая логика через выбор действий по строкам;
- ручные поля не перезаписываются молча.


## Этап 5 — Разделы каталога

Добавлен раздел «Разделы»: названия RU/EN, публичность, порядок, комментарий.


## Fix included

This package includes the safe existing-stone update fix from Stage 4.


## Этап 6A — Настройки цен

Добавлен раздел «Цены».

Входит:

- цена поставщика за карат;
- коэффициенты расходов;
- маржи по диапазонам веса;
- коэффициенты KURGIN Score;
- ручные курсы валют.

Не входит:

- финальный расчёт по камням;
- Index;
- просмотр маржи;
- публикация;
- экспорт.


## 6A.1 — Удобная таблица цены поставщика

Вкладка «Цены → Цена поставщика» теперь показывает цены матрицами:

- отдельный блок по каждому цвету D/E/F/G;
- строки = чистота;
- колонки = диапазоны веса;
- данные сохраняются в прежнюю нормальную структуру CSV.


## Этап 6B — Расчёт корневых цен за карат

Добавлена вкладка «Цены → Расчёт USD».

Показывает цепочку:

- цена поставщика за карат;
- внутренняя цена за карат;
- стартовая цена за карат;
- рабочая цена за карат;
- публичная цена за карат.

Пока без KURGIN Score, без Index и без финальных цен по камням.


## Этап 6C — Индексная таблица с KURGIN Score

Добавлена вкладка «Цены → Index».

Показывает:
- публичную цену за карат из 6B;
- выбранный коэффициент KURGIN Score;
- итоговую индексную цену за карат;
- валюты RUB / USD / INR;
- таблицы по цветам D/E/F/G, строкам чистоты и колонкам диапазонов веса.

Пока без просмотра маржи по камням, публикации и экспорта.


## 6C.1 — Описание формул цен

В разделе «Цены» добавлен раскрываемый блок «Как считаются цены».

Он объясняет:

- цену поставщика;
- внутреннюю цену;
- стартовую цену;
- рабочую цену;
- публичную цену;
- Index с KURGIN Score;
- округление RUB вверх до 100 ₽.

Формулы и расчёты не изменены.


## 6B.1 — Понятные маржи и защита пустой цены поставщика

Изменено:

- во вкладке «Маржи» добавлены названия:
  - Маржа 1 — стартовая;
  - Маржа 2 — рабочая;
  - Маржа 3 — публичная;
- добавлены текстовые формулы;
- если цена поставщика пустая или 0, дальнейшие цены не рассчитываются;
- в Index такие ячейки остаются пустыми.


## 6C.3 — Комментарии к Index

Во вкладке «Цены → Index» добавлены пояснения:

- «Index по цветам» — удобный публичный вид таблицы;
- «Полная таблица Index» — техническая проверка расчёта.

Этот пакет также сохраняет правило: если цена поставщика пустая или 0, Index не рассчитывается.


## 6C.4 — Логический порядок вкладок цен

В разделе «Цены» вкладки переставлены по цепочке расчёта:

1. Цена поставщика
2. Расходы
3. Внутренняя цена
4. Маржа 1
5. Маржа 2
6. Маржа 3
7. KURGIN Score
8. Курсы валют
9. Расчёт USD
10. Index

Вкладка «Маржи» разделена на три отдельные вкладки, чтобы было понятно, какая маржа формирует какой уровень цены.


## 6C.5 — Цепочка цен по вкладкам

Вкладки раздела «Цены» перестроены по логике расчёта:

1. Цена поставщика за карат
2. Расходы
3. Внутренняя цена за карат
4. Маржа 1
5. Стартовая цена за карат
6. Маржа 2
7. Рабочая цена за карат
8. Маржа 3
9. Публичная цена за карат
10. KURGIN Score
11. Курсы валют
12. Index

Для внутренней, стартовой, рабочей и публичной цены добавлены отдельные удобные таблицы по цветам, чистотам и диапазонам веса.


## 6C.6 — Полные диапазоны веса в таблицах цен

В таблицах цен короткие заголовки заменены на полные диапазоны:

- 1.00–1.49
- 1.50–1.99
- 2.00–2.49
- 2.50–2.99
- 3.00–3.99
- 4.00–4.99
- 5.00+

Формулы и расчёты не изменены.


## 6C.7 — Округление RUB Index до 100 ₽

Публичный Index в RUB округляется вверх до 100 ₽.

Пример:

- 22 650 ₽ → 22 700 ₽
- 22 601 ₽ → 22 700 ₽
- 22 600 ₽ → 22 600 ₽

Формулы расчёта не изменены.


## 6D — Просмотр маржи по камням

Добавлена вкладка «Цены → Просмотр маржи».

Показывает контрольную таблицу по конкретным камням:

- ID;
- Report #;
- вес;
- цвет;
- чистота;
- KURGIN Score;
- цену поставщика за камень;
- внутреннюю цену за камень;
- стартовую цену за камень;
- рабочую цену за камень;
- публичную цену за камень;
- разницы между уровнями.

Экран только для просмотра. Менять можно только валюту отображения: RUB / USD / INR.


## 6E.1 — Компактная навигация цен по группам

Длинная строка вкладок в разделе «Цены» заменена на компактную навигацию по группам.

Группы:

- База цены
- Маржи
- Расчётные цены
- Коэффициенты и валюты
- Index и просмотр

Внутри выбранной группы показываются только нужные страницы.

Это интерфейсное изменение. Формулы, расчёты и файлы данных не изменены.


## 7B — Предпросмотр записи цен

Добавлена страница «Цены → Index и просмотр → Запись цен».

Это только предпросмотр. Он не записывает данные в stones_master.csv.

Показывает:

- сколько камней получат цены;
- сколько камней без цены поставщика;
- сколько камней с ручной ценой;
- сколько будет пропущено;
- какие камни будут записаны;
- какие камни могут быть показаны как «Цена по запросу».


## 7B.1 — Исправление предпросмотра записи цен

Исправлена логика предпросмотра записи цен.

Теперь «Запись цен» использует тот же статус расчёта, что и «Просмотр маржи»:

- рассчитанные камни попадают в «Камни, которым будут записаны цены»;
- камни без цены поставщика попадают в «Камни без рассчитанной цены».

Данные всё ещё не записываются в stones_master.csv.

## 7C — Подтверждение и запись итоговых цен

Добавлена безопасная запись итоговых price-полей в `data/stones_master.csv` через вкладку:

```text
Цены → Index и просмотр → Запись цен
```

Поток 7C:

1. сформировать предпросмотр;
2. проверить группы: рассчитанные, без цены поставщика, ручные;
3. поставить чекбокс подтверждения;
4. ввести контрольную фразу `ЗАПИСАТЬ ЦЕНЫ`;
5. система создаёт backup;
6. только после этого записывает данные в `stones_master.csv`.

Записываемые поля:

- цены за карат USD: supplier / internal / start / working / public;
- цены за камень USD;
- цены за камень RUB;
- служебные поля: `price_currency_base`, `price_fx_usd_rub`, `price_calculated_at`, `price_status`, `price_warning`, `price_source`, `public_price_display`, `allow_price_on_request`.

Защиты 7C:

- строки с `price_source = manual` не перезаписываются;
- перед каждой записью создаётся backup;
- подтверждение привязано к fingerprint предпросмотра, устаревший предпросмотр не записывается;
- если для рассчитанных камней не задан `USD_RUB`, запись блокируется;
- камни без цены поставщика не получают числовые price-поля;
- основная запись не включает “Цена по запросу”: `allow_price_on_request = true` и `public_price_display = Цена по запросу` ставятся только отдельной кнопкой с фразой `ВКЛЮЧИТЬ ПО ЗАПРОСУ` и отдельным backup.
## Checkpoint 25 — Stage 7C completed and locked

Checkpoint 25 фиксирует стабильное состояние после завершения Stage 7C.

Порядок процесса после 7C:

```text
1. Сначала убедиться, что 7C реально завершён и проверен.
2. Зафиксировать правила и ограничения после 7C.
3. Сделать checkpoint ZIP по состоянию после 7C.
4. Только потом обсуждать 7D.
5. Сначала согласовать правила 7D.
6. Только после этого делать ZIP с кодом 7D.
```

Фактическое состояние:

```text
7C работает
код 7C находится в GitHub main
commit: Stage 7C: add confirmed price write to stones_master
Streamlit обновлён и проверен
запись цен в stones_master.csv сработала
backup перед записью создался
GitHub Desktop после проверки был чистый
```

Правила после 7C:

```text
backup перед записью обязателен
запись цен подтверждается вручную
ручные цены не перезаписываются молча
камни без цены поставщика не получают числовую цену
“Цена по запросу” не включается автоматически
allow_price_on_request включается только отдельным подтверждаемым действием
устаревший preview не должен записываться
```

Итоговые price-поля, добавленные 7C в `stones_master.csv`:

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

Что ещё не сделано после 7C:

```text
публикация
публичный слой каталога
экспорт для сайта
автоматический sync
правила отбора камней для публичного отображения
```

Следующий этап 7D не реализован в этом checkpoint. До кода 7D нужно отдельно согласовать правила: что считается публикацией, какие камни попадают в публичный слой, какие исключаются, как учитывать `allow_price_on_request`, `status`, `availability_status`, `catalog_section`, скрытые разделы и price-поля.

Предыдущий черновой ZIP 7D, выданный до фиксации checkpoint 25, считать неактуальным и не устанавливать.


## 7D.0 — Unified KURGIN Report / PDF / Assets foundation

7D.0 — документационный foundation после закрытого 7C. Нового кода, PDF-генерации, asset manager и изменений CSV-схемы в этом этапе нет.

Цель 7D.0:

```text
заложить единый будущий контракт KURGIN Report / PDF / Assets,
чтобы Admin, Analyzer, сайт, Mass Analyzer и будущая карточка камня не получили разные несовместимые PDF-генераторы.
```

Главный принцип:

```text
один общий ReportPayloadV1
один будущий unified KURGIN Report / PDF generator
несколько режимов ReportMode
отдельные visibility rules для каждого режима
```

Режимы отчёта:

```text
internal_admin
private_analyzer
public_stone_analyzer
mass_analyzer_row
catalog_stone_card
```

PDF generator в будущем должен принимать готовый `ReportPayloadV1`, применять visibility policy и возвращать PDF + metadata. Он не должен считать цены, менять `stones_master.csv`, менять статусы, публиковать камень, создавать заказ/резерв/покупку, включать `allow_price_on_request`, раскрывать внутреннюю формулу или зависеть необратимо от Streamlit Cloud.

Карточка камня на сайте в будущем должна иметь public-safe summary:

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

Цена входит в публичную карточку, но только как готовое публичное отображение `public_price_display` или разрешённая “Цена по запросу”. Карточка, сайт и будущий PDF generator не считают цену.

При клике детальная карточка сможет показывать эту же карточку, расширенные данные, будущий KURGIN Analyzer Report PDF, lab report, фото/видео/assets. В 7D.0 это только контракт на будущее, не реализация.

V1 граница:

```text
PDF generator не реализуется
PDF viewer не реализуется
asset manager не реализуется
stone_assets.csv не активируется
stones_master.csv не меняется
экспорт/публикация на сайт не делаются
```

Подробный контракт зафиксирован в:

```text
docs/UNIFIED_KURGIN_REPORT_FOUNDATION_V1.md
```

Дополнение 7D.0 по будущим кабинетам специалиста:

```text
ReportMode и PriceVisibilityContext разделены.
internal_admin, specialist_private, specialist_client_view, public_catalog и public_analyzer могут иметь разные разрешённые price display.
specialist_client_view должен быть клиентским безопасным режимом и не должен раскрывать specialist margin, specialist purchase price, supplier price, internal price, working price или admin price metadata.
V1 не реализует specialist pricing, price tiers или кабинеты. Это только future visibility rule.
```

## 7D — Public Layer Rules

7D is a documentation-only stage. It defines which stones may later be shown outside Admin and in what form.

No code, export, sync, PDF generation, asset manager or CSV mutation is added in 7D.

Public eligibility baseline:

```text
status = published
availability_status = in_stock
catalog_section is filled
catalog_section exists in catalog_sections.csv
catalog_sections.is_public = true
```

Price is part of the future public stone card. The public layer may show only prepared `public_price_display`:

```text
numeric price: price_status = calculated and public_price_display is filled
Цена по запросу: price_status = missing_supplier_price and allow_price_on_request = true
```

The card/site/PDF generator must not calculate price and must not expose supplier/internal/start/working prices, margins, `price_source`, FX metadata, admin notes or formula internals.

Future public card summary:

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

Detailed rules are documented in:

```text
docs/PUBLIC_LAYER_RULES_V1.md
```

Next implementation stage after accepting 7D rules:

```text
7E — Admin preview/audit of the public layer
```

## 7E — Admin preview/audit публичного слоя

7E adds a read-only Admin preview/audit for the future public layer:

```text
Цены → Index и просмотр → Публичный слой
```

7E applies the rules documented in `docs/PUBLIC_LAYER_RULES_V1.md` and separates stones into audit groups:

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

7E is not publication and not export. It does not write CSV files, does not create backups, does not write to `exports/`, does not sync with the site, does not change `status`, `availability_status`, `catalog_section`, prices or `allow_price_on_request`, and does not create PDF/assets.

The business logic is implemented as a portable read-only function:

```text
build_public_layer_preview()
```

Streamlit only displays the returned preview/audit tables.

## 7E.1 — Public layer UI fixes

7E.1 keeps the public-layer audit read-only and adds UI/data clarity:

- KURGIN Score coefficient settings now show recorded score ranges:
  - poor: `<60`
  - fair: `60–69.99`
  - standard: `70–79.99`
  - high: `80–89.99`
  - premium: `90–94.99`
  - elite: `95+`
  - not_calculated: `Не рассчитано`
- KURGIN Score ranges are shown in Index labels and the full Index technical table.
- Public-layer audit includes `Диапазон KURGIN Score`.
- Fluorescence displays `None` when fluorescence is empty/none-like, because `None` is a real fluorescence value alongside Faint / Medium / Strong.
- Price navigation separates KURGIN Score coefficients and currency rates into separate top-level buttons.

7E.1 does not change prices, does not write public exports, does not publish stones, does not sync with the site and does not generate PDFs.

## 7F.0 — Public Export / Public Card Schema Contract

7F.0 is documentation only. It defines the future public export and public card schema contract after the 7E.1 public-layer audit UI fixes.

Canonical future export file:

```text
public_stones_v1.csv
```

The file is versioned and must not silently replace existing/legacy `stones.csv` until the public site is explicitly migrated.

Future flow:

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

Future public card/export fields include public-safe data only:

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
height / depth_mm
cut_grade
symmetry
polish
fluorescence
tags
availability_status_public
future availability flags for detail/report/assets
```

The public site may show only prepared `public_price_display`. It must not calculate price and must not receive supplier/internal/start/working prices, margins, `price_source`, FX metadata, admin notes, formula internals or raw diagnostics.

7F.0 does not add code, does not generate exports, does not write `exports/`, does not write `kurgin-data`, does not sync with the site and does not change CSV data.

Detailed contract:

```text
docs/PUBLIC_EXPORT_CONTRACT_V1.md
```

Next possible implementation stage after 7F.0 is accepted:

```text
7F — Admin in-memory public export preview/download
```

## 7F — Admin in-memory public export preview/download

7F adds a safe Admin preview/download block for the future public export file:

```text
public_stones_v1.csv
```

Location:

```text
Цены → Index и просмотр → Публичный слой
```

7F uses the same public-layer result as 7E and builds the export table only in memory. It does not write `exports/`, does not write `kurgin-data`, does not sync with the public site and does not mutate Admin CSV files.

Allowed in 7F:

```text
read stones_master.csv
read catalog_sections.csv
apply 7D public-layer rules
build public_stones_v1.csv preview from public candidates
show public-safe export rows
download public_stones_v1.csv through Streamlit download_button
```

Forbidden in 7F:

```text
write exports/
write kurgin-data
sync with the site
change stones_master.csv
change catalog_sections.csv
change status / availability_status / catalog_section
change prices
turn on allow_price_on_request
create backups
create PDFs/assets
create orders/reserves/payments
```

If there are no public candidates, 7F still allows downloading `public_stones_v1.csv` with headers only. This is valid while all stones are still `draft`.



## 8A.0 — Controlled publish path to kurgin-data

8A.0 is documentation only. It defines the future controlled publish path from Admin to the public data layer.

Intended future flow:

```text
KURGIN Admin
↓
7F public_stones_v1.csv preview/download
↓
manual controlled publish
↓
kurgin-data
↓
public site / catalog card
```

For V1, publish must remain manual and controlled. Admin may generate and download `public_stones_v1.csv`, but 8A.0 does not write to `kurgin-data`, does not sync with the public site and does not create automation.

Core rule:

```text
kurgin-admin-mvp generates public export.
kurgin-data is the public data layer.
kurgin-streamlit-mvp / public site reads public data.
The public site must not read stones_master.csv directly.
```

`public_stones_v1.csv` must not silently replace legacy/current `stones.csv`. Any migration of the public site to the new schema must be a separate stage.

Before a future publish to `kurgin-data`, the operator must verify:

```text
schema_version = public_stones_v1
only public-safe columns are present
forbidden internal/admin/formula fields are absent
public_price_display is filled for every export row
price_display_type is numeric or price_on_request
public_card_status is public_numeric_price or public_price_on_request
KURGIN Score range is filled
fluorescence uses None for empty/none-like display
row_count is intentional
```

Empty export handling:

```text
Headers-only public_stones_v1.csv is allowed for preview/download.
Publishing an empty public_stones_v1.csv to kurgin-data must require a separate warning and explicit confirmation.
```

Future controlled publish should create or preserve a publish manifest:

```text
publish_manifest.json
```

with at least:

```text
schema_version
published_at
source_repo
source_checkpoint
export_file
row_count
numeric_count
price_on_request_count
export_hash
published_by
notes
```

8A.0 does not change code, data, Streamlit UI, export generation, PDF/assets, database or site integration.

Detailed rules:

```text
docs/CONTROLLED_PUBLISH_PATH_V1.md
```

Next possible implementation stage after 8A.0 is accepted:

```text
8A — manual publish package / snapshot structure
```

8A code must not start until its implementation rules are separately agreed.

## 8A — Manual publish package / snapshot structure

Added a safe in-memory manual publish package for the future controlled publish path.

Location:

```text
Цены → Index и просмотр → Публичный слой → Manual publish package — kurgin-data
```

The package is downloaded as a ZIP and contains:

```text
public_stones_v1.csv
publish_manifest.json
publish_checks.json
README_MANUAL_PUBLISH.md
```

8A is still not an automatic publish/sync. It does not write `exports/`, does not update `kurgin-data`, does not change Admin CSV files, does not create PDF/assets and does not contact the public site.

Empty `public_stones_v1.csv` packages are allowed for preview/download, but publishing an empty file to `kurgin-data` requires separate human confirmation.
