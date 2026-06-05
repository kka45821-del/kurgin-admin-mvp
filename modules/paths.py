from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
EXPORTS_DIR = ROOT / "exports"
BACKUPS_DIR = ROOT / "backups"
RULES_DIR = ROOT / "rules"

STONES_FILE = DATA_DIR / "stones_master.csv"
SHIPMENTS_FILE = DATA_DIR / "shipments.csv"
IMPORT_LOG_FILE = DATA_DIR / "import_log.csv"
PAYMENTS_FILE = DATA_DIR / "shipment_payments.csv"
CATALOG_SECTIONS_FILE = DATA_DIR / "catalog_sections.csv"

def ensure_dirs() -> None:
    for path in [DATA_DIR, RAW_DIR, EXPORTS_DIR, BACKUPS_DIR, RULES_DIR]:
        path.mkdir(parents=True, exist_ok=True)
