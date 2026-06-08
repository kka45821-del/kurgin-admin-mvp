# NEXT CHAT START HERE — KURGIN Admin

Stable checkpoint:

```text
Checkpoint 31 — Stage 7F Public Export Preview/Download
```

Previous checkpoints:

```text
Checkpoint 25 — Stage 7C completed / rules locked
Checkpoint 26 — Stage 7D.0 Unified Report / PDF / Assets foundation
Checkpoint 27 — Stage 7D Public Layer Rules
Checkpoint 28 — Stage 7E Public Layer Preview/Audit
Checkpoint 29 — Stage 7E.1 Public Layer UI Fixes
Checkpoint 30 — Stage 7F.0 Public Export / Public Card Schema Contract
```

## Current state

```text
7C writes final prices to stones_master.csv with preview + confirmation + backup.
7D documents public-layer rules.
7E adds read-only Admin preview/audit of the future public layer.
7E.1 fixes KURGIN Score range visibility, price navigation and fluorescence display.
7F.0 documents the future public export / public card schema contract.
7F implements Admin in-memory public_stones_v1.csv preview/download.
```

## 7F behavior

Location:

```text
Цены → Index и просмотр → Публичный слой
```

7F adds:

```text
Public export preview — public_stones_v1.csv
```

It:

```text
builds export rows only from 7E public candidates
shows only public-safe fields
allows download through Streamlit download_button
returns headers-only CSV when public candidates = 0
```

It does not:

```text
write exports/
write kurgin-data
sync with public site
change stones_master.csv
change catalog_sections.csv
change status / availability / section / prices
turn on allow_price_on_request
create backups
create PDF/assets
create orders/reserves/payments
```

## Important V1 limitation

```text
Streamlit Cloud runtime data may reset after redeploy/reboot.
Do not deeply fix persistence in V1.
V2 database should become source of truth.
```

## Next reasonable topic

Discuss next stage rules before code.

Likely topic:

```text
8A — controlled publish path to kurgin-data
```

Do not start 8A code until rules are confirmed.
