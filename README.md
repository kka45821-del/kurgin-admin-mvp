# CVDLAB / KURGIN Platform

PostgreSQL-first, API-first foundation for CVDLAB/KURGIN.

## Domains

```text
cvdlab.ru        public platform
admin.cvdlab.ru  admin UI
api.cvdlab.ru    backend API
```

## V1 Core

- FastAPI backend.
- Streamlit Admin v2 shell.
- PostgreSQL required.
- Native auth foundation.
- Roles / policies / entitlements foundation.
- Cart / orders / mock payment foundation.
- Partner cabinet foundation with RU / EN / zh-CN / HY.
- KURGIN Index public ₽/ct contract.
- Pricing formula v0.2-lite with 3 price channels.
- Safe public catalog / public index / site settings snapshots.
- Public site patch adapters.

## Safe defaults

```text
REAL_PAYMENT_PROVIDER_ENABLED=false
PUBLIC_CHECKOUT_ENABLED=false
SPECIALIST_CHECKOUT_ENABLED=false
PARTNER_REGISTRATION_ENABLED=false
ANALYZER_PAYMENTS_ENABLED=false
PUBLIC_PRICE_DISPLAY_ENABLED=false
PUBLIC_INDEX_ENABLED=true
MOCK_PAYMENTS_ENABLED=true
```

## Local start

```bash
cp .env.example .env
docker compose up --build
```

Then:

```bash
alembic -c migrations/alembic.ini upgrade head
python scripts/create_owner.py --email owner@cvdlab.ru --password 'change-me'
```

## Rule

Do not expose internal/supplier/specialist/admin fields in public snapshots.
