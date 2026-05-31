import pandas as pd

from admin_integrity import build_integrity_report, integrity_summary


def test_batch_count_mismatch_is_reported():
    stones = pd.DataFrame([
        {"stone_id": "S1", "batch_number": "P-0001"},
    ])
    batches = pd.DataFrame([
        {"batch_number": "P-0001", "stones_count": 3, "batch_status": "uploaded"},
    ])
    report = build_integrity_report(stones=stones, batches=batches, payments=pd.DataFrame())

    assert "batch_stones_count_mismatch" in set(report["check"])
    row = report[report["check"] == "batch_stones_count_mismatch"].iloc[0]
    assert row["entity"] == "P-0001"
    assert int(row["declared"]) == 3
    assert int(row["actual"]) == 1
    assert row["severity"] == "error"


def test_archived_orphan_batch_is_warning_not_error():
    stones = pd.DataFrame(columns=["stone_id", "batch_number"])
    batches = pd.DataFrame([
        {"batch_number": "P-0002", "stones_count": 174, "batch_status": "archived"},
    ])
    report = build_integrity_report(stones=stones, batches=batches, payments=pd.DataFrame())

    assert "orphan_batch_without_stones" in set(report["check"])
    assert set(report["severity"]) == {"warning"}
    summary = integrity_summary(report)
    assert summary["errors"] == 0
    assert summary["warnings"] >= 1


def test_orphan_stones_without_batch_is_error():
    stones = pd.DataFrame([
        {"stone_id": "S1", "batch_number": "P-MISSING"},
        {"stone_id": "S2", "batch_number": "P-MISSING"},
    ])
    batches = pd.DataFrame([
        {"batch_number": "P-0001", "stones_count": 1, "batch_status": "uploaded"},
    ])
    report = build_integrity_report(stones=stones, batches=batches, payments=pd.DataFrame())

    assert "orphan_stones_without_batch" in set(report["check"])
    row = report[report["check"] == "orphan_stones_without_batch"].iloc[0]
    assert row["severity"] == "error"
    assert row["entity"] == "P-MISSING"
    assert int(row["actual"]) == 2


def test_duplicate_stone_id_is_error():
    stones = pd.DataFrame([
        {"stone_id": "DUP", "batch_number": "P-0001"},
        {"stone_id": "DUP", "batch_number": "P-0001"},
    ])
    batches = pd.DataFrame([
        {"batch_number": "P-0001", "stones_count": 2, "batch_status": "uploaded"},
    ])
    report = build_integrity_report(stones=stones, batches=batches, payments=pd.DataFrame())

    assert "duplicate_stone_id" in set(report["check"])
    row = report[report["check"] == "duplicate_stone_id"].iloc[0]
    assert row["severity"] == "error"
    assert row["entity"] == "DUP"
    assert int(row["actual"]) == 2
