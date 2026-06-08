# Checkpoint 31 — Stage 7F Public Export Preview/Download

Status: **implemented**  
Base: Checkpoint 30 — Stage 7F.0 Public Export / Public Card Schema Contract

## What 7F adds

7F adds a safe Admin in-memory preview/download block for:

```text
public_stones_v1.csv
```

Location:

```text
Цены → Index и просмотр → Публичный слой
```

The export preview is built from the 7E public-layer preview/audit result. It contains only public candidates and only public-safe fields.

## Allowed in 7F

```text
read stones_master.csv
read catalog_sections.csv
apply 7D public-layer rules
build public export preview in memory
show public_stones_v1.csv preview
download public_stones_v1.csv via download_button
```

## Forbidden in 7F

```text
write exports/
write kurgin-data
sync with public site
change stones_master.csv
change catalog_sections.csv
change status
change availability_status
change catalog_section
change prices
turn on allow_price_on_request
create backup
create PDF/assets
create orders/reserves/payments
```

## Public export filename

```text
public_stones_v1.csv
```

## Expected current behavior

If all stones are still `draft`, then:

```text
public candidates = 0
public_stones_v1.csv = headers only
```

This is correct.

## Files changed

```text
README.md
NEXT_CHAT_START_HERE.md
CHECKPOINT_31_STAGE_07F_PUBLIC_EXPORT_PREVIEW.md
app.py
modules/storage.py
rules/README_RULES.md
docs/PUBLIC_EXPORT_CONTRACT_V1.md
```

## Not changed / not committed

```text
data/
backups/
exports/
__pycache__/
tmp/
current_working_code/
test files
```

## Next stage

Do not proceed automatically. Next stage must be discussed separately.

Likely future topic:

```text
8A — controlled publish path to kurgin-data
```

But 8A must not start before rules are agreed.
