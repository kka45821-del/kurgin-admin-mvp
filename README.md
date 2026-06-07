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
