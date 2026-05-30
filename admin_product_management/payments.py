import pandas as pd

from admin_io import load_batch_payments


def batch_payment_rows(batch_number: str) -> pd.DataFrame:
    payments = load_batch_payments()
    if payments.empty or "batch_number" not in payments.columns:
        return pd.DataFrame(columns=["batch_number", "payment_date", "amount_rub", "note", "created_at"])
    return payments[payments["batch_number"].astype(str).eq(str(batch_number))].copy()
