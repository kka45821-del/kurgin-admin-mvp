SUPPORTED_LOCALES = ("ru", "en", "zh-CN", "hy")
DEFAULT_LOCALE = "ru"
TRANSLATIONS = {
    "partner.my_batches": {"ru": "Мои партии", "en": "My batches", "zh-CN": "我的批次", "hy": "Իմ խմբաքանակները"},
    "partner.on_site": {"ru": "На сайте", "en": "On site", "zh-CN": "网站展示中", "hy": "Կայքում"},
    "partner.sold": {"ru": "Продано", "en": "Sold", "zh-CN": "已售出", "hy": "Վաճառված"},
    "partner.removed": {"ru": "Снятые с продажи", "en": "Removed from sale", "zh-CN": "已下架", "hy": "Հանված վաճառքից"},
}

def t(key: str, locale: str = DEFAULT_LOCALE) -> str:
    values = TRANSLATIONS.get(key, {})
    return values.get(locale) or values.get(DEFAULT_LOCALE) or key
