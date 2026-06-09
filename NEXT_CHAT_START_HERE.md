# NEXT CHAT START HERE — KURGIN Admin

Stable checkpoint:

```text
Checkpoint 32 — Stage 8A.0 Controlled Publish Path Rules
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
```

## 8A.0 rules

Future intended flow:

```text
KURGIN Admin
↓
7F public_stones_v1.csv preview/download
↓
manual controlled publish
↓
kurgin-data
↓
public site / catalog card
```

V1 publish must remain manual and controlled.

`public_stones_v1.csv` must not silently replace legacy/current `stones.csv`.

The public site must not:

```text
read stones_master.csv directly
calculate prices
receive supplier/internal/start/working prices
receive formula internals
receive admin metadata
```

Empty export handling:

```text
headers-only CSV is valid for preview/download.
Publishing empty public_stones_v1.csv to kurgin-data must require explicit warning and confirmation.
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
8A — manual publish package / snapshot structure
```

Do not start 8A code until rules are confirmed.
