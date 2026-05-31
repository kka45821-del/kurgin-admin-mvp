import pandas as pd

from admin_publication_rules import public_preview, public_sellable_mask, public_visible_mask


def base_stone(**overrides):
    row = {
        "stone_id": "T-001",
        "show_in_catalog": True,
        "is_mvp_eligible": True,
        "has_lab_document": True,
        "physically_received": True,
        "checked_by_kurgin": True,
        "upload_confirmed": True,
        "current_status": "available",
        "price_rub": 100000,
        "price_confirmed": True,
        "availability_confirmed": True,
        "price_status": "confirmed",
        "show_without_price": False,
    }
    row.update(overrides)
    return row


def frame(*rows):
    return pd.DataFrame(list(rows))


def first_preview(row):
    result = public_preview(frame(row))
    assert len(result) == 1
    return result.iloc[0]


def test_confirmed_price_is_sellable_contact_without_checkout():
    row = first_preview(base_stone())
    assert bool(row["public_visible"]) is True
    assert bool(row["public_sellable"]) is True
    assert bool(row["checkout_enabled"]) is False
    assert row["public_action"] == "request_price"
    assert bool(row["is_request_price"]) is False
    assert row["public_state"] == "sellable_contact"
    assert row["public_reason"] == "checkout_not_enabled"
    assert int(row["price_rub"]) == 100000


def test_needs_review_never_checkout_or_sellable():
    row = first_preview(base_stone(price_status="needs_review"))
    assert bool(row["public_visible"]) is True
    assert bool(row["public_sellable"]) is False
    assert bool(row["checkout_enabled"]) is False
    assert row["public_action"] == "request_price"
    assert bool(row["is_request_price"]) is True
    assert row["public_state"] == "request_price"
    assert row["public_reason"] == "price_missing"
    assert int(row["price_rub"]) == 0


def test_index_pending_is_visible_request_price_only():
    row = first_preview(base_stone(price_status="index_pending", price_confirmed=False))
    assert bool(row["public_visible"]) is True
    assert bool(row["public_sellable"]) is False
    assert bool(row["is_request_price"]) is True
    assert row["public_state"] == "request_price"
    assert row["public_reason"] == "price_missing"
    assert int(row["price_rub"]) == 0


def test_missing_price_can_be_visible_request_price_when_show_without_price():
    row = first_preview(base_stone(price_rub=0, price_confirmed=False, price_status="missing", show_without_price=True))
    assert bool(row["public_visible"]) is True
    assert bool(row["public_sellable"]) is False
    assert row["public_action"] == "request_price"
    assert row["public_reason"] == "price_missing"
    assert int(row["price_rub"]) == 0


def test_sold_or_missing_public_flags_are_not_visible():
    sold = frame(base_stone(current_status="sold"))
    assert not bool(public_visible_mask(sold).iloc[0])
    assert public_preview(sold).empty

    missing_flag = frame(base_stone(checked_by_kurgin=False))
    assert not bool(public_visible_mask(missing_flag).iloc[0])
    assert public_preview(missing_flag).empty


def test_sellable_requires_allowed_price_status():
    df = frame(
        base_stone(stone_id="ok", price_status="confirmed"),
        base_stone(stone_id="bad", price_status="needs_review"),
        base_stone(stone_id="missing", price_status=""),
    )
    mask = public_sellable_mask(df)
    assert mask.tolist() == [True, False, False]
