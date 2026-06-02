from enum import StrEnum

class UserRole(StrEnum):
    GUEST = "guest"
    CUSTOMER = "customer"
    SPECIALIST = "specialist"
    JEWELER = "jeweler"
    PARTNER = "partner"
    ADMIN = "admin"
    OWNER = "owner"

class PriceChannel(StrEnum):
    PUBLIC_SITE = "public_site"
    SPECIALIST_PURCHASE = "specialist_purchase"
    SPECIALIST_CLIENT_DISPLAY = "specialist_client_display"

class CartItemType(StrEnum):
    STONE_PUBLIC_PURCHASE = "stone_public_purchase"
    STONE_SPECIALIST_PURCHASE = "stone_specialist_purchase"
    ANALYZER_SINGLE_RUN = "analyzer_single_run"
    ANALYZER_SUBSCRIPTION = "analyzer_subscription"
    PRIVATE_OFFER = "private_offer"
    QUOTE_REQUEST = "quote_request"
