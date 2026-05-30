ACTIVE = "active"
STUB = "stub"
HIDDEN = "hidden"
FUTURE = "future"
RESTRICTED = "restricted"

STATUS_LABELS = {
    ACTIVE: "Активно",
    STUB: "В разработке",
    HIDDEN: "Скрыто",
    FUTURE: "Будущее",
    RESTRICTED: "Ограничено",
}

ADMIN_MENU = [
    {
        "id": "dashboard",
        "title": "Обзор",
        "icon": "◇",
        "status": ACTIVE,
        "description": "Общий статус платформы, ошибки, риски и быстрые действия.",
        "items": [
            {"id": "dashboard_status", "title": "Общий статус", "status": ACTIVE, "description": "Ключевые показатели каталога, партий и публикации."},
            {"id": "dashboard_risks", "title": "Ошибки и риски", "status": ACTIVE, "description": "Критические ошибки, предупреждения и зоны, которые нельзя запускать без проверки."},
            {"id": "dashboard_actions", "title": "Быстрые действия", "status": ACTIVE, "description": "Быстрые переходы к загрузке Excel, preview и публикации."},
        ],
    },
    {
        "id": "product_management",
        "title": "Управление товаром",
        "icon": "📦",
        "status": ACTIVE,
        "description": "Отдельная рабочая зона: камни, загрузка, цена, публикация, партии и состояние.",
        "items": [],
    },
    {
        "id": "catalog",
        "title": "Каталог",
        "icon": "💎",
        "status": ACTIVE,
        "description": "Рабочая зона MVP: камни, импорт Excel, партии, preview, цены, статусы, разделы и публикация. Временно сохранено как fallback.",
        "items": [
            {"id": "catalog_all", "title": "Все камни", "status": ACTIVE, "description": "Рабочая таблица всех камней в системе."},
            {"id": "catalog_import", "title": "Импорт Excel", "status": ACTIVE, "description": "Загрузка Excel, диагностика листов, распознавание колонок и нормализация."},
            {"id": "catalog_batches", "title": "Партии", "status": ACTIVE, "description": "История загруженных партий и количество камней."},
            {"id": "catalog_preview", "title": "Публичный preview", "status": ACTIVE, "description": "Какие камни проходят в публичный catalog.json."},
            {"id": "catalog_publication", "title": "Publication Gate", "status": ACTIVE, "description": "Проверка и публикация catalog.json в kurgin-data."},
            {"id": "catalog_sections", "title": "Разделы каталога", "status": ACTIVE, "description": "Основной, крупные, средние, мелкие, цветные, боковые, парные, эксклюзив."},
            {"id": "catalog_statuses", "title": "Статусы камней", "status": ACTIVE, "description": "available, reserved, sold, unavailable, hidden, draft, internal review."},
            {"id": "catalog_prices", "title": "Цены", "status": ACTIVE, "description": "Публичная цена, цена за карат, дата и источник цены."},
            {"id": "catalog_documents", "title": "Документы камней", "status": STUB, "description": "Лаборатория, номер документа, файл, ссылка и статус проверки."},
            {"id": "catalog_score", "title": "KURGIN Score на камнях", "status": STUB, "description": "Score, диапазон, теги, сильные стороны, риски и версия методологии."},
            {"id": "catalog_tags", "title": "Теги карточек", "status": STUB, "description": "Огонь, блеск, контраст, баланс, цена, крупный, проверка, elite."},
            {"id": "catalog_add", "title": "Добавить камень", "status": STUB, "description": "Ручное добавление одного камня."},
        ],
    },
    {
        "id": "orders",
        "title": "Заказы",
        "icon": "🧾",
        "status": STUB,
        "description": "Будущая зона заказов. Оплата, sold и возвраты не являются рабочей логикой MVP.",
        "items": [
            {"id": "orders_all", "title": "Все заказы", "status": STUB, "description": "Будущий список заказов."},
            {"id": "orders_carts", "title": "Корзины", "status": STUB, "description": "Камни, добавленные пользователями в корзину."},
            {"id": "orders_checkout", "title": "Checkout", "status": RESTRICTED, "description": "Проверка цены и статуса перед оплатой."},
            {"id": "orders_payment", "title": "Payment sessions", "status": RESTRICTED, "description": "Платёжные сессии. Требуется отдельная проверка."},
            {"id": "orders_processing", "title": "Paid order processing", "status": RESTRICTED, "description": "Состояние после оплаты, но до sold."},
            {"id": "orders_sold", "title": "Sold confirmation", "status": RESTRICTED, "description": "Ручное финальное подтверждение продажи."},
            {"id": "orders_claims", "title": "Refund / Claims", "status": RESTRICTED, "description": "Возвраты и претензии."},
        ],
    },
    {
        "id": "requests",
        "title": "Заявки",
        "icon": "📩",
        "status": ACTIVE,
        "description": "Вопрос по камню, подбор, matching, bulk request, special order и внешний Analyzer-запрос. Заявка не является заказом.",
        "items": [
            {"id": "requests_all", "title": "Все заявки", "status": STUB, "description": "Общий список заявок."},
            {"id": "requests_question", "title": "Вопрос по камню", "status": STUB, "description": "Обращения по конкретному камню."},
            {"id": "requests_pick", "title": "Подбор одного камня", "status": STUB, "description": "Параметры желаемого камня."},
            {"id": "requests_matching", "title": "Matching", "status": STUB, "description": "Подбор похожих камней."},
            {"id": "requests_bulk", "title": "Bulk request", "status": STUB, "description": "Запрос группы камней."},
            {"id": "requests_special", "title": "Special order", "status": STUB, "description": "Специальный заказ под поставку."},
            {"id": "requests_external", "title": "External Analyzer request", "status": STUB, "description": "Анализ внешнего камня."},
        ],
    },
    {
        "id": "analyzer",
        "title": "Analyzer",
        "icon": "⚙️",
        "status": STUB,
        "description": "Будущее управление анализом качества. Analyzer не сертификат, не оценка цены, не инвестиционная рекомендация.",
        "items": [
            {"id": "analyzer_formulas", "title": "Формулы", "status": STUB, "description": "Веса, правила, диапазоны и penalty."},
            {"id": "analyzer_score", "title": "KURGIN Score", "status": STUB, "description": "Шкала, диапазоны и описания."},
            {"id": "analyzer_reports", "title": "PDF / Reports", "status": RESTRICTED, "description": "Шаблоны отчётов. Не должны выглядеть как сертификат."},
            {"id": "analyzer_batch", "title": "Batch / Excel", "status": RESTRICTED, "description": "Массовый анализ Excel. Требует отдельной проверки."},
        ],
    },
    {
        "id": "index",
        "title": "Index",
        "icon": "📊",
        "status": STUB,
        "description": "KURGIN Index как рыночный ориентир. Не точная цена, не финансовый индекс, не прогноз.",
        "items": [
            {"id": "index_dashboard", "title": "Dashboard", "status": STUB, "description": "Состояние индекса и дата обновления."},
            {"id": "index_tables", "title": "Таблицы Index", "status": STUB, "description": "Значения по параметрам."},
            {"id": "index_ranges", "title": "Диапазоны", "status": STUB, "description": "Вес, цвет, чистота, KURGIN Score."},
            {"id": "index_methodology", "title": "Методология", "status": STUB, "description": "Публичное описание и внутренняя версия."},
        ],
    },
    {
        "id": "content",
        "title": "Контент",
        "icon": "📝",
        "status": ACTIVE,
        "description": "Тексты публичных страниц, системные сообщения и пояснения.",
        "items": [
            {"id": "content_platform", "title": "KURGIN Platform", "status": STUB, "description": "Главная информационная страница."},
            {"id": "content_catalog", "title": "Catalog texts", "status": ACTIVE, "description": "Тексты каталога, пустые состояния, фильтры."},
            {"id": "content_system", "title": "System messages", "status": ACTIVE, "description": "Ошибки, предупреждения и success-сообщения."},
        ],
    },
    {
        "id": "users",
        "title": "Пользователи",
        "icon": "👤",
        "status": STUB,
        "description": "Аккаунты, роли, verification, privileges, entitlements и user history. Роль не равна привилегиям.",
        "items": [
            {"id": "users_all", "title": "Все пользователи", "status": STUB, "description": "Список пользователей."},
            {"id": "users_roles", "title": "Роли", "status": STUB, "description": "guest, customer, specialist applicant, verified specialist, admin, manager."},
            {"id": "users_privileges", "title": "Privileges", "status": STUB, "description": "Доступные возможности."},
        ],
    },
    {
        "id": "specialists",
        "title": "Специалисты",
        "icon": "🧑‍💼",
        "status": STUB,
        "description": "Ювелиры, мастерские, консультанты, дизайнеры и профессиональные пользователи. Не marketplace специалистов.",
        "items": [
            {"id": "specialists_applications", "title": "Applications", "status": STUB, "description": "Заявки специалистов."},
            {"id": "specialists_privileges", "title": "Privileges", "status": STUB, "description": "Назначенные возможности."},
            {"id": "specialists_client_safe", "title": "Client-safe mode", "status": RESTRICTED, "description": "Что можно показывать клиенту."},
        ],
    },
    {
        "id": "suppliers",
        "title": "Поставщики",
        "icon": "🏭",
        "status": RESTRICTED,
        "description": "Внутренний supply-side контур. Поставщик не является публичным продавцом и не публикует камни напрямую.",
        "items": [
            {"id": "suppliers_all", "title": "Suppliers", "status": RESTRICTED, "description": "Список поставщиков."},
            {"id": "suppliers_stones", "title": "Supplier stones", "status": RESTRICTED, "description": "Внутренние камни поставщика."},
            {"id": "suppliers_quotes", "title": "Supplier quotes", "status": RESTRICTED, "description": "Внутренние предложения."},
        ],
    },
    {
        "id": "documents",
        "title": "Документы",
        "icon": "📄",
        "status": STUB,
        "description": "Лабораторные документы, публичные документы, версии и дисклеймеры.",
        "items": [
            {"id": "documents_lab", "title": "Stone lab documents", "status": STUB, "description": "Документы конкретных камней."},
            {"id": "documents_public", "title": "Public documents", "status": RESTRICTED, "description": "Privacy, terms, payment terms, reserve terms."},
            {"id": "documents_disclaimers", "title": "Disclaimers", "status": STUB, "description": "Analyzer, KURGIN Score, Index, payment, reserve, reports."},
        ],
    },
    {
        "id": "navigation",
        "title": "Навигация",
        "icon": "🧭",
        "status": ACTIVE,
        "description": "Видимость страниц, порядок, нижняя панель и внутренние ссылки.",
        "items": [
            {"id": "navigation_bottom", "title": "Bottom nav", "status": ACTIVE, "description": "KURGIN, Инструменты, Каталог, Избранное, Корзина, Профиль."},
            {"id": "navigation_visibility", "title": "Page visibility", "status": ACTIVE, "description": "Включить, скрыть, future, admin only."},
        ],
    },
    {
        "id": "brand_ui",
        "title": "Бренд / UI",
        "icon": "🎨",
        "status": STUB,
        "description": "Будущие визуальные настройки. Финальный дизайн пока не включаем.",
        "items": [
            {"id": "brand_logo", "title": "Logo", "status": STUB, "description": "Логотип, favicon, SVG."},
            {"id": "brand_typography", "title": "Typography", "status": STUB, "description": "Cinzel, Didot/Bodoni, Inter."},
            {"id": "brand_theme", "title": "Theme", "status": STUB, "description": "Demo, grayscale, production."},
        ],
    },
    {
        "id": "settings",
        "title": "Настройки",
        "icon": "🛠",
        "status": ACTIVE,
        "description": "App mode, feature flags, data sources, import/export и журнал действий.",
        "items": [
            {"id": "settings_mode", "title": "App mode", "status": ACTIVE, "description": "Demo, staging, production."},
            {"id": "settings_flags", "title": "Feature flags", "status": ACTIVE, "description": "Включить / скрыть Analyzer, Index, Academy, Specialists, Checkout."},
            {"id": "settings_data_sources", "title": "Data sources", "status": ACTIVE, "description": "Local demo, external catalog, production catalog."},
            {"id": "settings_import_export", "title": "Import / Export", "status": ACTIVE, "description": "Экспорт catalog.json, backup, restore."},
            {"id": "settings_logs", "title": "Журнал действий", "status": ACTIVE, "description": "Минимальный журнал действий администратора."},
        ],
    },
    {
        "id": "security",
        "title": "Безопасность",
        "icon": "🔐",
        "status": STUB,
        "description": "Администраторы, права доступа и журнал действий.",
        "items": [
            {"id": "security_admins", "title": "Admin users", "status": STUB, "description": "Список администраторов."},
            {"id": "security_permissions", "title": "Permissions", "status": STUB, "description": "Права на редактирование каталога, цен, публикации и пользователей."},
            {"id": "security_audit", "title": "Audit trail", "status": STUB, "description": "Полный audit trail будет позже. Сейчас используется минимальный журнал действий."},
        ],
    },
]


def visible_sections():
    return [section for section in ADMIN_MENU if section.get("status") != HIDDEN]


def visible_items(section: dict):
    return [item for item in section.get("items", []) if item.get("status") != HIDDEN]


def find_section(section_id: str):
    return next((section for section in ADMIN_MENU if section.get("id") == section_id), ADMIN_MENU[0])


def find_item(section: dict, item_id: str | None):
    items = visible_items(section)
    if not items:
        return None
    if item_id:
        found = next((item for item in items if item.get("id") == item_id), None)
        if found:
            return found
    return items[0]
