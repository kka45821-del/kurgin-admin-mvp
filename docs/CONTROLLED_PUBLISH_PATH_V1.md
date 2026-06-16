# Controlled Publish Path V1 — 8A.0

Status: docs-only foundation.

This document defines the future controlled publish path from KURGIN Admin to the public data layer. It does not implement publishing, sync, export writing, PDF, assets, database or site integration.

## Stable base

```text
Checkpoint 31 — Stage 7F Public Export Preview/Download
```

Current completed flow:

```text
7C → writes final prices inside Admin after preview + confirmation + backup
7D → documents public-layer rules
7E → shows read-only public-layer audit in Admin
7F → builds public_stones_v1.csv preview/download in memory
```

## Purpose

8A.0 defines how the future public export may move from Admin to `kurgin-data` safely.

Target future flow:

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

In 8A.0 this is only a rule contract. No code is added.

## Repository roles

```text
kurgin-admin-mvp
```

Source of Admin decisions, prices, public-layer audit and public export generation.

```text
kurgin-data
```

Public data layer for the site. It may later hold `public_stones_v1.csv` and publish metadata.

```text
kurgin-streamlit-mvp
```

Public site / catalog UI reader. It must read public-safe data only.

Rules:

```text
Admin generates public_stones_v1.csv.
kurgin-data stores public data.
The public site reads kurgin-data.
The public site does not read stones_master.csv directly.
The public site does not calculate prices.
The public site does not receive private/admin/formula fields.
```

## V1 publish model

For V1, publish must be manual and controlled.

Allowed future manual flow:

```text
1. Admin builds public-layer audit.
2. Admin builds public_stones_v1.csv preview/download.
3. Operator reviews public candidates, warnings, manual review and data problems.
4. Operator downloads public_stones_v1.csv.
5. Operator updates kurgin-data separately.
6. Public site reads public_stones_v1.csv from kurgin-data.
```

Not allowed in V1 by default:

```text
automatic sync
auto-publish on price write
auto-publish on status change
site reading Admin runtime files
site reading stones_master.csv
site filtering private fields itself
```

## Export file boundary

Canonical future file:

```text
public_stones_v1.csv
```

Legacy/current public data file:

```text
stones.csv
```

Rule:

```text
public_stones_v1.csv must not silently replace stones.csv.
```

Any migration of the public site to `public_stones_v1.csv` must be a separate stage.

## Required checks before future publish

Before future publish to `kurgin-data`, the operator must verify:

```text
schema_version = public_stones_v1
only public-safe columns are present
forbidden internal/admin/formula fields are absent
there are no data-problem rows in export
public_price_display is filled for every export row
price_display_type is numeric or price_on_request
public_card_status is public_numeric_price or public_price_on_request
KURGIN Score range is filled
fluorescence uses None for empty/none-like display
row_count is intentional
```

## Empty export rule

Headers-only `public_stones_v1.csv` is valid for Admin preview/download.

Publishing an empty export to `kurgin-data` is dangerous because it may clear the public catalog.

Therefore future publish of an empty file must require:

```text
explicit warning
explicit confirmation
operator acknowledgement that public catalog may become empty
```

## Public-safe data only

Future publish may only use the fields approved by:

```text
docs/PUBLIC_EXPORT_CONTRACT_V1.md
```

Forbidden fields must not reach `public_stones_v1.csv` or `kurgin-data`:

```text
supplier_price_*
internal_price_*
start_price_*
working_price_*
price_fx_usd_rub
price_calculated_at
price_source
price_warning
admin_note
price_comment
shipment_id
supplier_id
supplier_name
import_id
updated_import_id
last_source_file
raw_source_file
margins
expense coefficients
formula internals
formula thresholds
formula penalties
raw diagnostics
breakdown
manual/auto technical marker
private API keys
private service URLs
```

## Publish manifest — future rule

Future controlled publish should create or preserve:

```text
publish_manifest.json
```

Minimum fields:

```text
schema_version
published_at
source_repo
source_checkpoint
export_file
row_count
numeric_count
price_on_request_count
export_hash
published_by
notes
```

Purpose:

```text
track published data version
make rollback/manual restore possible
separate public data state from Admin runtime state
```

## Backup / snapshot rule

A future publish stage should preserve the previous public data state before replacing public data.

Possible future snapshot files:

```text
public_stones_v1.previous.csv
publish_manifest.previous.json
```

or a timestamped snapshot folder in the publish package.

8A.0 does not implement this. It only defines the rule.

## What 8A.0 does not do

```text
does not write kurgin-data
does not write exports/
does not sync with public site
does not use GitHub API
does not create workflow
does not change stones_master.csv
does not change catalog_sections.csv
does not change public_stones_v1.csv generation
does not change status / availability_status / catalog_section
does not change prices
does not turn on allow_price_on_request
does not create backup
does not create PDF/assets
does not create database
```

## Future stages

Recommended sequence:

```text
8A.0 — docs-only controlled publish rules
8A — manual publish package / snapshot structure
8B — public site reads public_stones_v1.csv
8C — controlled sync or semi-automatic publish
V2 — database source of truth
V2 — unified PDF generator / assets
```

## Implementation rule

No 8A implementation code should start until the implementation rules are separately agreed.

## 8A implementation note — manual publish package

8A implements the first safe package step without publishing automatically.

Admin can create an in-memory ZIP package:

```text
kurgin-public-publish-package-YYYYMMDD-HHMMSS.zip
```

The package contains:

```text
public_stones_v1.csv
publish_manifest.json
publish_checks.json
README_MANUAL_PUBLISH.md
```

This package is for operator-controlled manual movement into `kurgin-data`. It does not write `exports/`, does not update `kurgin-data`, does not sync with the public site and does not replace legacy `stones.csv`.

Detailed package contract:

```text
docs/MANUAL_PUBLISH_PACKAGE_V1.md
```
