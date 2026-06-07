# Checkpoint 29 — Stage 7E.1 Public Layer UI Fixes

Stable base: **Checkpoint 28 — Stage 7E Public Layer Preview/Audit**

## What changed

7E.1 keeps 7E read-only and fixes UI/data clarity after Streamlit testing.

Implemented:

```text
KURGIN Score ranges are recorded in coefficient settings
KURGIN Score ranges are visible in Index selector labels
KURGIN Score ranges are visible in the full Index technical table
KURGIN Score ranges are visible in public-layer audit
KURGIN Score coefficients and currency rates are separate top-level price navigation buttons
fluorescence displays None when blank/none-like
```

## KURGIN Score ranges V1

```text
poor            <60
fair            60–69.99
standard        70–79.99
high            80–89.99
premium         90–94.99
elite           95+
not_calculated  Не рассчитано
```

## Fluorescence rule

```text
None is a real fluorescence value, not a missing-value marker.
Display/audit must show None instead of an empty cell for blank/none-like fluorescence.
```

## Still forbidden

7E.1 must not:

```text
write exports
publish stones
sync with the site
write public-layer CSV
change status / availability_status / catalog_section
change or recalculate prices
turn on allow_price_on_request
create PDF/assets
```

## Files changed

```text
README.md
NEXT_CHAT_START_HERE.md
CHECKPOINT_29_STAGE_07E1_UI_FIXES.md
app.py
modules/schema.py
modules/storage.py
rules/README_RULES.md
```
