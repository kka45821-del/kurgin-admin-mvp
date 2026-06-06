PRICE_WRITE_STONE_COLUMNS = [
    "supplier_price_per_ct_usd",
    "internal_price_per_ct_usd",
    "start_price_per_ct_usd",
    "working_price_per_ct_usd",
    "public_price_per_ct_usd",
    "supplier_price_total_usd",
    "internal_price_total_usd",
    "start_price_total_usd",
    "working_price_total_usd",
    "public_price_total_usd",
    "supplier_price_total_rub",
    "internal_price_total_rub",
    "start_price_total_rub",
    "working_price_total_rub",
    "public_price_total_rub",
    "price_currency_base",
    "price_fx_usd_rub",
    "price_calculated_at",
    "price_status",
    "price_warning",
    "price_source",
    "public_price_display",
    "allow_price_on_request",
]

STONES_COLUMNS = [
    "stone_id",
    "kurgin_import_id",
    "report_number",
    "stock_number",
    "lab",
    "shape",
    "weight",
    "color",
    "clarity",
    "cut",
    "polish",
    "symmetry",
    "fluorescence",
    "measurements",
    "min_diameter",
    "max_diameter",
    "depth_mm",
    "kurgin_score",
    "score_status",
    "catalog_section",
    "status",
    "availability_status",
    "shipment_id",
    "import_id",
    "source_file",
    "imported_at",
    "supplier_name",
    "shipment_date",
    "currency",
    "published_price",
    "admin_note",
    "validation_status",
    "validation_message",
    "warning_status",
    "warning_message",
    "updated_at",
    "updated_import_id",
    "last_source_file",
    *PRICE_WRITE_STONE_COLUMNS,
]

SHIPMENTS_COLUMNS = [
    "shipment_id",
    "import_id",
    "supplier_id",
    "supplier_name",
    "shipment_date",
    "shipment_name",
    "currency",
    "total_purchase_cost",
    "advance_paid",
    "payment_comment",
    "comment",
    "original_filename",
    "stored_filename",
    "source_file_path",
    "created_at",
]

IMPORT_LOG_COLUMNS = [
    "import_id",
    "source_file",
    "original_filename",
    "stored_filename",
    "imported_at",
    "excel_template_version",
    "rows_total",
    "rows_saved",
    "rows_not_saved",
    "warnings_count",
    "conflicts_count",
    "status",
    "message",
]

REQUIRED_SHEETS = ["Results", "Details", "Issues", "System"]


PAYMENTS_COLUMNS = [
    "payment_id",
    "shipment_id",
    "payment_date",
    "amount",
    "currency",
    "comment",
    "created_at",
]


CATALOG_SECTIONS_COLUMNS = [
    "section_id",
    "section_name_ru",
    "section_name_en",
    "is_public",
    "sort_order",
    "comment",
]


PRICE_SUPPLIER_COLUMNS = [
    "weight_range_id",
    "color",
    "clarity",
    "supplier_price_per_ct_usd",
    "comment",
    "updated_at",
]

PRICE_EXPENSE_RATES_COLUMNS = [
    "expense_key",
    "expense_name_ru",
    "rate",
    "is_active",
    "comment",
    "updated_at",
]

PRICE_MARGINS_COLUMNS = [
    "margin_type",
    "weight_range_id",
    "numerator",
    "divisor",
    "comment",
    "updated_at",
]

PRICE_SCORE_COEFFICIENTS_COLUMNS = [
    "score_key",
    "score_name_ru",
    "coefficient",
    "sort_order",
    "comment",
    "updated_at",
]

CURRENCY_RATES_COLUMNS = [
    "rate_key",
    "rate_name_ru",
    "rate_value",
    "updated_at",
    "comment",
]

WEIGHT_RANGES = [
    ("1.00-1.49", "1.00–1.49 ct"),
    ("1.50-1.99", "1.50–1.99 ct"),
    ("2.00-2.49", "2.00–2.49 ct"),
    ("2.50-2.99", "2.50–2.99 ct"),
    ("3.00-3.99", "3.00–3.99 ct"),
    ("4.00-4.99", "4.00–4.99 ct"),
    ("5.00+", "5.00+ ct"),
]

PRICE_COLORS = ["D", "E", "F", "G"]
PRICE_CLARITIES = ["IF", "VVS1", "VVS2", "VS1", "VS2"]
