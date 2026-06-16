# NEXT CHAT START HERE — KURGIN Admin

Stable checkpoint:

```text
Checkpoint 33 — Stage 8A Manual Publish Package / Snapshot Structure
```

Previous checkpoints:

```text
Checkpoint 25 — Stage 7C completed / rules locked
Checkpoint 26 — Stage 7D.0 Unified Report / PDF / Assets foundation
Checkpoint 27 — Stage 7D Public Layer Rules
Checkpoint 28 — Stage 7E Public Layer Preview/Audit
Checkpoint 29 — Stage 7E.1 Public Layer UI Fixes
Checkpoint 30 — Stage 7F.0 Public Export / Public Card Schema Contract
Checkpoint 31 — Stage 7F Public Export Preview/Download
Checkpoint 32 — Stage 8A.0 Controlled Publish Path Rules
```

## Current state

```text
7C writes final prices to stones_master.csv with preview + confirmation + backup.
7D documents public-layer rules.
7E adds read-only Admin preview/audit of the future public layer.
7E.1 fixes KURGIN Score ranges, price navigation and fluorescence display.
7F.0 documents the public export / public card schema contract.
7F implements Admin in-memory public_stones_v1.csv preview/download.
8A.0 documents the controlled publish path to kurgin-data.
8A implements an in-memory manual publish package ZIP.
```

## 8A status

Location:

```text
Цены → Index и просмотр → Публичный слой → Manual publish package — kurgin-data
```

Package contents:

```text
public_stones_v1.csv
publish_manifest.json
publish_checks.json
README_MANUAL_PUBLISH.md
```

8A does not:

```text
write exports/
write kurgin-data
sync with site
change stones_master.csv
change catalog_sections.csv
change status / availability_status / catalog_section
change prices
turn on allow_price_on_request
create PDF/assets
```

Empty export is valid for package preview/download, but publishing an empty package to `kurgin-data` requires separate human confirmation.

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
8B — public site reads public_stones_v1.csv
```

Do not start 8B code until rules are confirmed.
