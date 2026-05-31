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
        "items": [],
    },
    {
        "id": "price_management",
        "title": "Управление ценами",
        "icon": "₽",
        "status": ACTIVE,
        "description": "Публичный режим цен: показывать подтверждённые цены или временно показывать все цены как «по запросу».",
        "items": [],
    },
    {
        "id": "product_management",
        "title": "Управление товаром",
        "icon": "📦",
        "status": ACTIVE,
        "description": "Главная рабочая зона админки: камни, загрузка Excel, партии, статусы, формирование цены, preview, публикация и разделы витрины.",
        "items": [],
    },
    {
        "id": "settings",
        "title": "Настройки",
        "icon": "🛠",
        "status": ACTIVE,
        "description": "Настройки страниц, разделов, фильтров, сортировок и журнал действий.",
        "items": [
            {"id": "settings_page_settings", "title": "Настройки страниц", "status": ACTIVE, "description": "Страницы, разделы, фильтры и сортировки."},
            {"id": "settings_logs", "title": "Журнал действий", "status": ACTIVE, "description": "Минимальный журнал действий администратора."},
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
