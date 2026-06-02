from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "local"
    public_site_url: str = "http://localhost:8501"
    admin_url: str = "http://localhost:8502"
    api_url: str = "http://localhost:8000"
    cookie_domain: str = "localhost"
    database_url: str
    session_secret: str
    password_pepper: str
    real_payment_provider_enabled: bool = False
    mock_payments_enabled: bool = True
    public_checkout_enabled: bool = False
    specialist_checkout_enabled: bool = False
    partner_registration_enabled: bool = False
    analyzer_payments_enabled: bool = False
    public_price_display_enabled: bool = False
    public_index_enabled: bool = True
    default_locale: str = "ru"
    supported_locales: str = "ru,en,zh-CN,hy"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()
