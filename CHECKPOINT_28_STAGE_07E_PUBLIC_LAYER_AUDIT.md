# Checkpoint 28 — Stage 7E Public Layer Preview/Audit

Status: **completed implementation checkpoint**  
Stable base: **Checkpoint 27 — Stage 7D Public Layer Rules**

## What Stage 7E adds

Stage 7E adds a read-only Admin preview/audit for the future public layer.

Location:

```text
Цены → Index и просмотр → Публичный слой
```

The screen applies the rules from:

```text
docs/PUBLIC_LAYER_RULES_V1.md
```

and shows:

```text
summary metrics
audit group counts
future public-safe preview rows
full audit table with filters
Data problems
Warnings / Manual price review
```

## Portable logic

The public-layer audit logic is implemented outside Streamlit:

```text
modules/storage.py → build_public_layer_preview()
```

Streamlit only displays the returned data.

This keeps the logic portable for future site/export/API layers.

## Audit groups

```text
Public OK — numeric price
Public OK — price on request
Ready but not published
Hidden by status
Hidden by availability_status
Hidden by catalog_section
Missing price
Manual price review
Data problems
```

## 7E must remain read-only

7E must not:

```text
write stones_master.csv
write catalog_sections.csv
create backup
write exports/
sync with site
change status
change availability_status
change catalog_section
change prices
turn on allow_price_on_request
create PDF
create assets/asset manager
create orders/reserves/payments
```

## Files changed in Stage 7E

```text
README.md
NEXT_CHAT_START_HERE.md
CHECKPOINT_28_STAGE_07E_PUBLIC_LAYER_AUDIT.md
app.py
modules/storage.py
rules/README_RULES.md
```

## Files not changed

```text
modules/schema.py
data/
backups/
exports/
__pycache__/
tmp/
current_working_code/
test files
```

## Next possible stage

Next stage should not be code until rules are agreed.

Recommended next topic:

```text
7F / 8A — export/public card schema
```

That stage should define what leaves Admin and how `kurgin-data` / public site receive public-safe data.
