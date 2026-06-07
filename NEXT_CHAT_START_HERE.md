# NEXT CHAT START HERE — KURGIN Admin

Stable checkpoint:

```text
Checkpoint 29 — Stage 7E.1 Public Layer UI Fixes
```

Previous checkpoints:

```text
Checkpoint 25 — Stage 7C completed / rules locked
Checkpoint 26 — Stage 7D.0 Unified Report / PDF / Assets foundation
Checkpoint 27 — Stage 7D Public Layer Rules
Checkpoint 28 — Stage 7E Public Layer Preview/Audit
```

## Current state

```text
7C writes final prices to stones_master.csv with preview + confirmation + backup.
7D documents public-layer rules.
7E adds read-only Admin preview/audit of the future public layer.
7E.1 fixes KURGIN Score range visibility, price navigation and fluorescence display.
```

## 7E.1 details

```text
KURGIN Score coefficient table shows recorded score ranges.
Index score selector labels include score ranges.
Full Index technical table includes score_range_label.
Public-layer audit includes Диапазон KURGIN Score.
KURGIN Score and Курсы валют are separate top-level buttons in price navigation.
Fluorescence blank/none-like values display as None.
```

## Important constraints

```text
Do not write exports yet.
Do not publish/sync stones yet.
Do not create PDF/assets yet.
Do not change stones_master.csv from public-layer audit.
Do not change status / availability_status / catalog_section from public-layer audit.
Do not turn on allow_price_on_request from public-layer audit.
```

## Next reasonable topic

After Streamlit confirmation of 7E.1, discuss the next stage before code.
Likely next stage:

```text
7F / 8A — future public export / public card schema rules
```
