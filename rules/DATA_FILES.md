# DATA_FILES.md

## Основная структура

```text
data/
  stones_master.csv
  shipments.csv
  import_log.csv
  catalog_sections.csv
  price_index.csv
  raw/
exports/
backups/
config/
modules/
assets/
```

## `data/stones_master.csv`

Компактная рабочая таблица камней первой версии.

Основные поля: `stone_id`, `kurgin_import_id`, `report_number`, `stock_number`, `shape`, `weight`, `color`, `clarity`, `kurgin_score`, `score_status`, `catalog_section`, `status`, `availability_status`, `shipment_id`, `import_id`, `source_file`, `imported_at`, `supplier_name`, `shipment_date`, `published_price`, `admin_note`, `validation_status`, `validation_message`.

Ценовые поля будут уточнены на Этапе 6.

## `data/shipments.csv`

Список поставок. Одна строка = одна подтверждённая загрузка Excel.

Поля: `shipment_id`, `import_id`, `supplier_name`, `shipment_date`, `shipment_name`, `currency`, `total_purchase_cost`, `advance_paid`, `payment_comment`, `comment`, `original_filename`, `stored_filename`, `source_file_path`, `created_at`.

Остаток к оплате считается автоматически: стоимость закупки всей партии минус аванс. `payment_status` пока не используется.

## `data/import_log.csv`

Технический журнал загрузок.

Поля: `import_id`, `source_file`, `original_filename`, `stored_filename`, `imported_at`, `excel_template_version`, `rows_total`, `rows_saved`, `rows_not_saved`, `warnings_count`, `conflicts_count`, `status`, `message`.

## `data/raw/{import_id}/`

После подтверждения импорта сохраняются:

```text
original.xlsx
results_full.csv
details_full.csv
issues_full.csv
system_info.csv
```

До подтверждения raw-папка не создаётся.

## `data/catalog_sections.csv`

Будет использоваться на этапе разделов. Минимум: `section_id`, `section_name_ru`, `section_name_en`, `is_public`, `sort_order`, `comment`.

## `data/price_index.csv`

Будет использоваться на этапе цен. Пока структура не фиксируется полностью.

## `exports/`

На Этапе 1 публичный экспорт не создаётся.

## `backups/`

Резервные копии перед записью и опасными действиями.
