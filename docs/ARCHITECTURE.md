# KURGIN Admin MVP architecture

This admin remains a single Streamlit app entrypoint: `app.py`.

The working MVP should keep Streamlit as a UI shell only. Business decisions must move gradually into separated modules:

- `domain/` — business objects and rules
- `application/` — use cases
- `infrastructure/` — storage and external services
- `ui/` — Streamlit pages and components
- `tests/` — safety checks

Current working import and publication flows must not be broken while the skeleton is introduced.
