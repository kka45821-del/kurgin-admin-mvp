# KURGIN Platform Architecture

## Scope

This package is a no-payment MVP for a stone catalog and scoring platform. It is
intended to be pushed into a new repository and run immediately with Streamlit.

## Modules

- `app.py` — landing page.
- `pages/` — Streamlit pages for search, analyzer, favorites, data quality and info.
- `kurgin/formula.py` — KURGIN Score formula and scoring utilities.
- `kurgin/data_io.py` — CSV/XLSX import, export and filters.
- `kurgin/storage.py` — local SQLite favorites.
- `kurgin/validators.py` — catalog validation.
- `translations_lang/` — RU/EN dictionaries.
- `assets/` — CSS and logo.

## Data flow

1. CSV/XLSX catalog is loaded.
2. Columns are normalized with aliases.
3. `score_catalog()` computes the composite score and score components.
4. The UI filters, displays and exports the scored catalog.
5. Favorites are written to local SQLite.

## Payment stance

No payment routes, checkout integrations, billing tables, subscriptions, webhooks
or payment API clients are included.
