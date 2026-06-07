# NEXT CHAT START HERE — KURGIN Admin

Continue from stable checkpoint **28**.

## Stable checkpoint

```text
Checkpoint 28 — Stage 7E Public Layer Preview/Audit
```

## Previous stable checkpoints

```text
Checkpoint 25 — Stage 7C completed / rules locked
Checkpoint 26 — Stage 7D.0 Unified Report / PDF / Assets foundation
Checkpoint 27 — Stage 7D Public Layer Rules
```

## Current confirmed state

```text
7C works
price write to stones_master.csv works
backup before price write is mandatory
manual prices are not silently overwritten
missing supplier price stones do not receive numeric prices
allow_price_on_request is not enabled automatically
Цена по запросу requires separate confirmed action
```

## Stage 7D.0 status

```text
Unified Report / PDF / Assets foundation documented
ReportPayloadV1 future contract documented
ReportMode values documented
Catalog Stone Card future contract documented
PriceVisibilityContext future rule documented
no PDF generator
no asset manager
no export/sync
```

## Stage 7D status

```text
public-layer rules documented
price is part of public catalog card
public layer may show only prepared public_price_display
status / availability_status / catalog_section / price rules documented
no Streamlit UI in 7D
no export/sync in 7D
```

## Stage 7E status

```text
Admin preview/audit for public layer implemented
location: Цены → Index и просмотр → Публичный слой
logic: modules/storage.py → build_public_layer_preview()
Streamlit displays the result only
read-only: no CSV mutation, no backup, no exports/, no sync, no PDF
```

## 7E audit groups

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

## Public eligibility baseline

A stone may enter the future public catalog layer only if:

```text
status = published
availability_status = in_stock
catalog_section is filled
catalog_section exists in catalog_sections.csv
catalog_sections.is_public = true
```

## Price rule

Price is part of the public stone card. The public layer may show only prepared:

```text
public_price_display
```

Numeric price requires:

```text
price_status = calculated
public_price_display is filled
public_price_total_rub is filled
```

“Цена по запросу” requires:

```text
price_status = missing_supplier_price
allow_price_on_request = true
public_price_display = Цена по запросу
```

## Do not do without separate approval

```text
Do not implement PDF generator.
Do not add PDF viewer.
Do not upload/link real assets.
Do not activate stone_assets.csv.
Do not change stones_master.csv schema for assets.
Do not create kurgin-report-core yet.
Do not write public export files.
Do not sync to site.
Do not mutate stones_master.csv in public-layer audit.
Do not create orders/reserves/payments.
```

## Next recommended topic

Discuss rules first, no code until approved:

```text
7F / 8A — export/public card schema
```

Main question:

```text
What exact public-safe data should leave Admin, where should it be stored, and how should the public site consume it?
```
