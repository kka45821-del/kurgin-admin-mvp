from __future__ import annotations

from pathlib import Path

APP_NAME = "KURGIN Platform"
APP_VERSION = "0.1.0"
APP_TAGLINE = "Stone catalog, scoring and decision support."
DEFAULT_LANGUAGE = "ru"
SUPPORTED_LANGUAGES = {"ru": "Русский", "en": "English"}

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
LOCAL_STATE_DIR = BASE_DIR / ".kurgin"
DB_PATH = LOCAL_STATE_DIR / "kurgin.db"

SAMPLE_CSV_PATH = DATA_DIR / "sample_stones.csv"
SAMPLE_XLSX_PATH = DATA_DIR / "sample_stones.xlsx"

PAYMENTS_ENABLED = False

CANONICAL_COLUMNS = [
    "stone_id",
    "supplier",
    "origin",
    "type",
    "shape",
    "carat",
    "color",
    "clarity",
    "cut",
    "polish",
    "symmetry",
    "fluorescence",
    "certificate",
    "price_usd",
    "availability",
    "notes",
]

REQUIRED_COLUMNS = [
    "stone_id",
    "type",
    "carat",
    "color",
    "clarity",
    "cut",
    "certificate",
    "price_usd",
    "availability",
]

DISPLAY_COLUMNS = [
    "stone_id",
    "supplier",
    "origin",
    "type",
    "shape",
    "carat",
    "color",
    "clarity",
    "cut",
    "certificate",
    "price_usd",
    "price_per_carat",
    "kurgin_score",
    "rating",
    "availability",
]

GRADE_COLUMNS = ["color", "clarity", "cut", "polish", "symmetry", "fluorescence", "certificate"]
