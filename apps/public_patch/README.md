# Public site patch

Patch adapters for `kurgin-streamlit-mvp`:

- load `site_settings.json` to hide/show pages and texts;
- load `public_index.json` for KURGIN Index ₽/ct;
- use API cart/order instead of static cart placeholder;
- use role-aware price channel resolver;
- partner cabinet must call `/partner/*` API, not public catalog.
