# KURGIN PRODUCT MANAGEMENT WORKFLOW LOCK v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: docs-only business logic lock.
Status: approved workflow reference for next implementation prompt.

This document locks the intended Product Management workflow before implementation work.

This document does not change code, data, public Streamlit, `kurgin-data`, Analyzer, formula/scoring, production claims, deployment, payment, reserve or sold logic.

## 1. Main workflow

The Product Management admin flow is:

```text
Загрузка
-> Установить цену
-> Опубликовать
-> Загруженные партии
-> Состояние / Подробнее
-> Все камни
```

The internal menu order must be:

1. Загрузка
2. Установить цену
3. Опубликовать
4. Загруженные партии
5. Редактирование
6. Состояние
7. Все камни

`Все камни` stays at the end of the menu.

## 2. Загрузка

Rules:

- Excel contains stone parameters, not the final public price.
- `Заменить весь каталог` must not be available in the Product Management upload flow.
- Product Management upload is add-only:

```text
Добавить к текущим
```

Batch-level purchase fields are entered during upload:

- `общая сумма покупки`
- `аванс`
- `долг`

Debt formula:

```text
долг = общая сумма покупки - аванс
```

These values belong to the batch, not to individual stones.

After a successful batch save, the UI must show:

```text
Далее
```

`Далее` opens:

```text
Установить цену
```

Batch metadata should preserve:

- `batch_number`
- `upload_date`
- `supplier_name`
- `notes`
- `stones_count`
- `purchase_total_rub`
- `purchase_advance_rub`
- `purchase_debt_rub`

If older batch rows do not have purchase fields, they must remain readable and missing numeric values must be treated as `0`.

## 3. Установить цену

Initial state:

```text
Сначала загрузите и сохраните партию в разделе Загрузка.
```

After upload/save, the page shows the current batch summary:

- номер партии
- дата
- поставщик
- комментарий
- количество камней
- общая сумма покупки
- аванс
- долг

Below that, it shows the stones in this batch.

The batch stone table must include three price columns:

- `цена на сайте`
- `цена в режиме клиента`
- `цена для ювелира`

Public site rule:

```text
Публичный сайт использует только цену на сайте.
```

Client-mode and jeweler price fields are future/admin fields:

- `цена в режиме клиента` is future/admin-only.
- `цена для ювелира` is future/admin-only.

This stage does not implement a real pricing engine.

No price must be calculated from Excel in this stage.

After review, the page must show:

```text
Далее
```

`Далее` opens:

```text
Опубликовать
```

## 4. Опубликовать

Initial state:

- It should not claim readiness until a batch has passed upload/review.
- It must use the existing Publication Gate / publish flow.
- Publish must happen only through the existing controlled flow.
- The publish logic must not be rewritten in this workflow implementation.

After reviewing the publish page, the UI may show:

```text
Далее
```

`Далее` opens:

```text
Загруженные партии
```

If publish was not executed, the UI must not claim that publication passed.

## 5. Загруженные партии

Batches are shown as separate rows.

Required fields:

- `batch_number`
- дата загрузки
- поставщик
- комментарий
- количество камней всего
- общая сумма покупки
- аванс
- долг
- статус

Allowed row actions:

- `Раскрыть`
- `Скачать Excel`
- `Подробнее`

No dangerous delete / rollback actions should be added here unless separately approved.

## 6. Состояние

The state page shows batch / aggregate rows.

Required fields:

- дата
- имя поставщика
- комментарий
- количество камней всего
- количество на сайте
- количество проданных
- количество в избранных
- количество забронированных
- количество в корзине
- кнопка `Подробнее`

`Подробнее` must open a separate internal page, not expand an inline table on the same page.

## 7. Подробнее

The detail page is a separate internal Product Management page.

It must have:

```text
← Назад к состоянию
```

The page header must include:

- `batch_number`
- дата
- поставщик
- комментарий

### 7.1. Financial block

The financial block shows:

- общая сумма покупки
- аванс
- дополнительные оплаты
- остаток

Outstanding balance formula:

```text
остаток = общая сумма покупки - аванс - сумма дополнительных оплат
```

### 7.2. Supplier payments

Payments are internal supplier payments.

They are not:

- client payment;
- checkout;
- payment session;
- public payment logic.

Preferred storage:

```text
data/batch_payments.csv
```

Required payment fields:

- `batch_number`
- `payment_date`
- `amount_rub`
- `note`
- `created_at`

The UI may allow adding multiple payments.

After adding a payment, outstanding balance must be recalculated.

## 8. Three tables in Подробнее

The detail page must show three Excel-like tables side by side or as clearly separated table blocks:

1. Камни на сайте / продаются ещё
2. Проданные камни
3. Сняты с продажи

Each table has its own Excel download button.

Each table uses fields:

- номер партии
- relevant date:
  - дата загрузки на сайт
  - дата продажи
  - дата снятия с продажи
- номер сертификата
- огранка
- карат
- цвет
- чистота

There must also be a full batch Excel report with 4 sheets:

1. Камни на сайте
2. Проданные камни
3. Сняты с продажи
4. Оплаты поставщику

If there are no sold / removed rows, show an empty table or safe placeholder.

Do not create active sale, reserve, cart or sold automation.

## 9. Снять партию с продажи

Removing a batch from sale is not physical deletion.

Sold stones must not be modified by this action.

Active / available stones in the batch should be soft-removed:

- `show_in_catalog = false`
- `is_mvp_eligible = false`
- `current_status = removed_from_sale`
- `removed_from_sale_at = current date`

Public boundary:

```text
Публичный сайт изменится только после отдельной публикации.
```

The action must be logged in `admin_actions.csv`.

This is Admin-side state control only.

It must not directly update `kurgin-data` or public Streamlit.

## 10. Редактирование

`Редактирование` remains a safe placeholder unless a separate task approves editing behavior.

Required text:

```text
Здесь позже будет безопасное редактирование камней, партий и статусов.
```

Do not add mass editing in this workflow stage.

## 11. Все камни

`Все камни` stays at the end of the Product Management menu.

It is a general Excel-like view of all stones with extended fields:

- `stone_id`
- `batch_number`
- `supplier_name`
- `upload_date`
- `title`
- `shape`
- `carat`
- `color`
- `clarity`
- `lab`
- `report_number`
- `section`
- `KURGIN Score`
- `site_price_rub`
- `client_mode_price_rub`
- `jeweler_price_rub`
- `price_status`
- `current_status`
- `public_status`
- tags if present

No dangerous mass editing should be enabled in this view.

## 12. Forbidden actions

This workflow lock forbids:

- changing public Streamlit;
- changing `kurgin-data` directly;
- changing Analyzer/formula/scoring;
- implementing client payment;
- implementing checkout;
- implementing active reserve/sold logic;
- making production deployment;
- physically deleting data;
- changing production claims.

## 13. Implementation notes

Allowed future implementation work inside `kurgin-admin-mvp`:

- Product Management navigation and state handling;
- add-only upload flow;
- batch purchase metadata fields;
- `data/upload_batches.csv` backward-compatible expansion;
- `data/batch_payments.csv` for supplier payment records;
- internal supplier payment add flow;
- Admin-only soft remove from sale;
- Excel downloads for batch tables and report.

Implementation must keep existing import and publish flows usable.

## 14. Acceptance lock

This document is accepted if:

- `docs/KURGIN_PRODUCT_MANAGEMENT_WORKFLOW_LOCK_V0_1.md` exists;
- no code changes are made;
- no data changes are made;
- public Streamlit is not changed;
- `kurgin-data` is not changed;
- Analyzer/formula/scoring are not touched;
- the Product Management workflow is clear enough for the next implementation prompt.

## 15. Closure

Final status:

```text
WORKFLOW LOCKED
```

This document is the reference for the next Product Management implementation task.
