# Architecture

```text
cvdlab.ru        public UI and cabinets
admin.cvdlab.ru  Streamlit Admin UI
api.cvdlab.ru    FastAPI backend
PostgreSQL       source of truth
```

Rules:

1. Streamlit is UI only.
2. PostgreSQL is source of truth.
3. Public data exits only through allowlist snapshots.
4. Public Index is ₽/ct benchmark, not stone price or offer.
5. All purchases go through cart/order.
6. Client mode displays client display price; checkout uses specialist purchase price.
7. Partners see batches only through explicit access.
