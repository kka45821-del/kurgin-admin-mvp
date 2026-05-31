import pandas as pd

from admin_io import load_batch_payments, load_batches, load_stones


ERROR = "error"
WARNING = "warning"
INFO = "info"


def _empty_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=["severity", "check", "entity", "declared", "actual", "message"])


def _batch_counts(stones: pd.DataFrame) -> pd.DataFrame:
    if stones.empty or "batch_number" not in stones.columns:
        return pd.DataFrame(columns=["batch_number", "actual_stones"])
    result = stones.copy()
    result["batch_number"] = result["batch_number"].fillna("").astype(str).str.strip()
    result = result[result["batch_number"] != ""]
    if result.empty:
        return pd.DataFrame(columns=["batch_number", "actual_stones"])
    return result.groupby("batch_number", dropna=False).size().reset_index(name="actual_stones")


def build_integrity_report(stones: pd.DataFrame | None = None, batches: pd.DataFrame | None = None, payments: pd.DataFrame | None = None) -> pd.DataFrame:
    stones = load_stones() if stones is None else stones
    batches = load_batches() if batches is None else batches
    payments = load_batch_payments() if payments is None else payments

    rows = []

    if not batches.empty and "batch_number" in batches.columns:
        batch_table = batches.copy()
        batch_table["batch_number"] = batch_table["batch_number"].fillna("").astype(str).str.strip()
        counts = _batch_counts(stones)
        merged = batch_table.merge(counts, on="batch_number", how="left")
        merged["actual_stones"] = pd.to_numeric(merged["actual_stones"], errors="coerce").fillna(0).astype(int)
        merged["stones_count"] = pd.to_numeric(merged.get("stones_count", 0), errors="coerce").fillna(0).astype(int)

        for _, row in merged.iterrows():
            batch_number = str(row.get("batch_number", "")).strip()
            if not batch_number:
                rows.append({
                    "severity": ERROR,
                    "check": "batch_number_missing",
                    "entity": "upload_batches.csv",
                    "declared": "",
                    "actual": "",
                    "message": "В upload_batches.csv есть строка без batch_number.",
                })
                continue

            declared = int(row.get("stones_count", 0) or 0)
            actual = int(row.get("actual_stones", 0) or 0)
            status = str(row.get("batch_status", "") or "").strip().lower()

            if declared != actual:
                severity = WARNING if status in {"archived", "removed_from_sale", "permanently_deleted"} else ERROR
                rows.append({
                    "severity": severity,
                    "check": "batch_stones_count_mismatch",
                    "entity": batch_number,
                    "declared": declared,
                    "actual": actual,
                    "message": f"Партия {batch_number}: заявлено stones_count={declared}, фактически строк stones={actual}.",
                })

            if actual == 0 and declared > 0:
                severity = WARNING if status in {"archived", "removed_from_sale", "permanently_deleted"} else ERROR
                rows.append({
                    "severity": severity,
                    "check": "orphan_batch_without_stones",
                    "entity": batch_number,
                    "declared": declared,
                    "actual": actual,
                    "message": f"Партия {batch_number} есть в upload_batches.csv, но строк камней по ней нет.",
                })

    if not stones.empty and "batch_number" in stones.columns:
        stone_batches = stones["batch_number"].fillna("").astype(str).str.strip()
        known_batches = set()
        if not batches.empty and "batch_number" in batches.columns:
            known_batches = set(batches["batch_number"].fillna("").astype(str).str.strip())
        orphan_mask = stone_batches.ne("") & ~stone_batches.isin(known_batches)
        for batch_number, count in stone_batches[orphan_mask].value_counts().items():
            rows.append({
                "severity": ERROR,
                "check": "orphan_stones_without_batch",
                "entity": str(batch_number),
                "declared": 0,
                "actual": int(count),
                "message": f"Есть {int(count)} строк stones с batch_number={batch_number}, но такой партии нет в upload_batches.csv.",
            })

    if not stones.empty and "stone_id" in stones.columns:
        ids = stones["stone_id"].fillna("").astype(str).str.strip()
        dup = ids[ids.ne("") & ids.duplicated(keep=False)]
        for stone_id, count in dup.value_counts().items():
            rows.append({
                "severity": ERROR,
                "check": "duplicate_stone_id",
                "entity": str(stone_id),
                "declared": 1,
                "actual": int(count),
                "message": f"stone_id={stone_id} повторяется {int(count)} раз.",
            })

    if not payments.empty and "batch_number" in payments.columns:
        payment_batches = payments["batch_number"].fillna("").astype(str).str.strip()
        known_batches = set()
        if not batches.empty and "batch_number" in batches.columns:
            known_batches = set(batches["batch_number"].fillna("").astype(str).str.strip())
        orphan_payment_mask = payment_batches.ne("") & ~payment_batches.isin(known_batches)
        for batch_number, count in payment_batches[orphan_payment_mask].value_counts().items():
            rows.append({
                "severity": ERROR,
                "check": "orphan_payments_without_batch",
                "entity": str(batch_number),
                "declared": 0,
                "actual": int(count),
                "message": f"Есть {int(count)} оплат по batch_number={batch_number}, но такой партии нет.",
            })

    if not rows:
        return _empty_frame()
    return pd.DataFrame(rows, columns=["severity", "check", "entity", "declared", "actual", "message"])


def integrity_summary(report: pd.DataFrame) -> dict:
    if report.empty:
        return {"errors": 0, "warnings": 0, "issues": 0}
    severity = report["severity"].astype(str).str.lower()
    errors = int(severity.eq(ERROR).sum())
    warnings = int(severity.eq(WARNING).sum())
    return {"errors": errors, "warnings": warnings, "issues": int(len(report))}
