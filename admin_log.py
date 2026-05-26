from datetime import datetime
from pathlib import Path

import pandas as pd

DATA_DIR = Path('data')
LOG_FILE = DATA_DIR / 'admin_actions.csv'
COLUMNS = ['created_at', 'action', 'entity', 'rows_count', 'source', 'result', 'details']


def load_admin_actions() -> pd.DataFrame:
    if LOG_FILE.exists():
        df = pd.read_csv(LOG_FILE)
    else:
        df = pd.DataFrame(columns=COLUMNS)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ''
    return df[COLUMNS]


def write_admin_action(action: str, entity: str = '', rows_count: int = 0, source: str = 'admin', result: str = 'success', details: str = '') -> None:
    DATA_DIR.mkdir(exist_ok=True)
    row = pd.DataFrame([{
        'created_at': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'action': action,
        'entity': entity,
        'rows_count': int(rows_count or 0),
        'source': source,
        'result': result,
        'details': details,
    }])
    pd.concat([load_admin_actions(), row], ignore_index=True)[COLUMNS].to_csv(LOG_FILE, index=False)
