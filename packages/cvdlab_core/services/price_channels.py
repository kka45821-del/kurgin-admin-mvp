from dataclasses import dataclass
from packages.cvdlab_core.domain.enums import UserRole, PriceChannel

@dataclass(frozen=True)
class StonePriceChannels:
    public_checkout_price_rub: int
    specialist_checkout_price_rub: int
    specialist_client_display_price_rub: int

def checkout_price_for_role(channels: StonePriceChannels, role: UserRole, *, client_mode: bool = False) -> int:
    if role in {UserRole.SPECIALIST, UserRole.JEWELER}:
        return channels.specialist_checkout_price_rub
    return channels.public_checkout_price_rub

def display_price_for_context(channels: StonePriceChannels, role: UserRole, *, client_mode: bool = False) -> int:
    if client_mode and role in {UserRole.SPECIALIST, UserRole.JEWELER}:
        return channels.specialist_client_display_price_rub
    if role in {UserRole.SPECIALIST, UserRole.JEWELER}:
        return channels.specialist_checkout_price_rub
    return channels.public_checkout_price_rub

def price_channel_for_cart(role: UserRole) -> PriceChannel:
    if role in {UserRole.SPECIALIST, UserRole.JEWELER}:
        return PriceChannel.SPECIALIST_PURCHASE
    return PriceChannel.PUBLIC_SITE
