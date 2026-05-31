from packages.cvdlab_core.contracts.public_catalog import build_public_catalog_snapshot, FORBIDDEN_PUBLIC_FIELDS
from packages.cvdlab_core.contracts.public_index import PublicIndexRow, build_public_index_snapshot
from packages.cvdlab_core.contracts.site_settings import build_site_settings_snapshot
from packages.cvdlab_core.domain.enums import UserRole, PriceChannel
from packages.cvdlab_core.services.price_channels import StonePriceChannels, checkout_price_for_role, display_price_for_context, price_channel_for_cart
from packages.cvdlab_core.pricing.formula_v02_lite import calculate_pricing_v02_lite


def test_public_catalog_does_not_export_internal_fields():
    payload = build_public_catalog_snapshot([{"stone_id": "S1", "supplier_total": 10, "calculated_public_price_rub": 1000000}])
    assert not FORBIDDEN_PUBLIC_FIELDS.intersection(payload["stones"][0].keys())


def test_public_index_is_rub_per_ct():
    payload = build_public_index_snapshot([PublicIndexRow("D", "VS1", 1, 1.5, "standard", "Standard", 780000)], active_index_version="v1")
    assert payload["currency"] == "RUB"
    assert payload["unit_label"] == "₽/ct"


def test_site_settings_four_locales():
    payload = build_site_settings_snapshot()
    assert set(payload["locales"]) == {"ru", "en", "zh-CN", "hy"}


def test_client_mode_display_not_checkout_price():
    channels = StonePriceChannels(1200000, 1000000, 1150000)
    assert display_price_for_context(channels, UserRole.SPECIALIST, client_mode=True) == 1150000
    assert checkout_price_for_role(channels, UserRole.SPECIALIST, client_mode=True) == 1000000
    assert price_channel_for_cart(UserRole.SPECIALIST) == PriceChannel.SPECIALIST_PURCHASE


def test_formula_three_prices_ordered():
    result = calculate_pricing_v02_lite(base_price_rub_per_ct=780000, carat=1.5, score_coefficient=1.2)
    assert result.calculated_specialist_purchase_price_rub < result.calculated_specialist_client_display_price_rub < result.calculated_public_price_rub
