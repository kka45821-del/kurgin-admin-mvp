# Manual Publish Package V1 — 8A

Status: implementation rules + Admin in-memory package builder.

8A adds a safe manual publish package for the future controlled publish path:

```text
KURGIN Admin
↓
public_stones_v1.csv preview/download
↓
manual publish package ZIP
↓
operator-controlled update of kurgin-data
↓
public site / catalog card
```

8A does not publish to `kurgin-data` automatically.

## Package filename

```text
kurgin-public-publish-package-YYYYMMDD-HHMMSS.zip
```

## Package contents

```text
public_stones_v1.csv
publish_manifest.json
publish_checks.json
README_MANUAL_PUBLISH.md
```

### public_stones_v1.csv

The public-safe catalog export prepared by the 7F public export contract.

Rules:

```text
only public-safe fields
no supplier/internal/start/working prices
no formula internals
no admin metadata
no price_source
no price_warning
no automatic site sync
```

### publish_manifest.json

Manifest for tracking the package and future published data version.

Minimum fields:

```text
schema_version
package_version
created_at
published_at
source_app
source_checkpoint
export_file
package_files
row_count
numeric_count
price_on_request_count
data_problem_count
warning_count
blocker_count
is_empty_export
requires_empty_export_confirmation
export_sha256
export_hash
publish_checks_sha256
manifest_sha256
published_by
notes
```

`published_at` stays empty in the Admin-generated package because 8A does not actually publish.

### publish_checks.json

Validation results for the package.

Blocking checks include:

```text
missing required public export columns
forbidden internal/admin columns in export
invalid schema_version
missing public_price_display
invalid price_display_type
invalid public_card_status
missing KURGIN Score range
blank fluorescence display
```

Warnings include:

```text
empty export
public-layer audit data problems outside export
public-layer audit warnings/manual review
manual price review rows
```

### README_MANUAL_PUBLISH.md

Operator instructions for manual V1 publishing.

## Empty export rule

Headers-only `public_stones_v1.csv` is valid for preview/download and for package creation.

Publishing an empty export to `kurgin-data` remains dangerous and must require separate human confirmation, because it may empty the public catalog.

## V1 manual publish rule

8A creates a ZIP package only in memory.

It does not:

```text
write exports/
write kurgin-data
sync with the public site
use GitHub API
create workflows
automatically replace stones.csv
change stones_master.csv
change catalog_sections.csv
change status / availability_status / catalog_section
change prices
turn on allow_price_on_request
create backups
create PDF/assets
create a database
```

## Future kurgin-data manual steps

A later manual publish procedure should be:

```text
1. Download the package from KURGIN Admin.
2. Review publish_checks.json.
3. If blockers exist, do not publish.
4. If export is empty, confirm separately that empty catalog is intended.
5. Open kurgin-data locally.
6. Preserve the previous public_stones_v1.csv and publish_manifest.json according to snapshot rules.
7. Replace public_stones_v1.csv.
8. Replace publish_manifest.json.
9. Commit and push kurgin-data.
10. Verify the public site.
```

## Next stages

```text
8B — public site reads public_stones_v1.csv
8C — controlled sync / semi-automatic publish, only after manual flow is safe
V2 — database source of truth
```
