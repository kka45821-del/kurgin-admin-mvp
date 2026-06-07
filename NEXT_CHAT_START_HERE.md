# NEXT CHAT START HERE — KURGIN Admin

Continue from stable checkpoint **26**.

## Stable checkpoint

```text
Checkpoint 26 — Stage 7D.0 Unified Report / PDF / Assets foundation
```

## Previous stable base

```text
Checkpoint 25 — Stage 7C completed / rules locked
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
GitHub main contains 7C
```

## Stage 7D.0 status

```text
docs-only foundation added
no app.py changes
no modules changes
no data/schema changes
no Streamlit UI changes
no PDF generator
no asset manager
no export/sync
```

## Unified report principle

```text
one shared ReportPayloadV1
one future unified KURGIN Report / PDF generator
multiple ReportMode values
mode-specific visibility rules
```

## ReportMode values

```text
internal_admin
private_analyzer
public_stone_analyzer
mass_analyzer_row
catalog_stone_card
```

## Future catalog card summary

```text
shape
carat
color
clarity
kurgin_score
public_price_display
min_diameter
max_diameter
height
cut_grade
symmetry
polish
fluorescence
tags
```

Price is part of the future public card summary only as prepared public display. The card/site/PDF generator must not calculate price.

Detail card may later show the same card, more details, KURGIN Analyzer PDF/report, lab report, photos/videos/assets.


## Future price visibility contexts

Keep `ReportMode` separate from `PriceVisibilityContext`.

Future contexts:

```text
internal_admin
specialist_private
specialist_client_view
public_catalog
public_analyzer
```

`specialist_private` and `specialist_client_view` may show different prepared price displays in future. Client view must not reveal specialist margin, specialist purchase price, supplier price, internal price, working price or admin price metadata.

V1 does not implement specialist pricing, price tiers or account-specific price calculation.

## Do not do without separate approval

```text
Do not implement PDF generator.
Do not add PDF viewer.
Do not upload/link real assets.
Do not activate stone_assets.csv.
Do not change stones_master.csv schema for assets.
Do not create kurgin-report-core yet.
Do not start public-layer code before rules are agreed.
Do not install old draft 7D ZIPs.
```

## Next discussion

Discuss **Stage 7D — public layer rules** only:

```text
what publication means
which stones enter public layer
which stones are excluded
how status is handled
how availability_status is handled
how catalog_section and is_public are handled
how allow_price_on_request is handled
how price_status and public_price_display are handled
which catalog card fields are public-safe
what is summary_view vs detail_view
what exactly is exported later
```

Only after these rules are confirmed should any 7D code ZIP be created.
