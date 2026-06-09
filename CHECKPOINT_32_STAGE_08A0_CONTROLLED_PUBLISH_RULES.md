# Checkpoint 32 — Stage 8A.0 Controlled Publish Rules

Stable checkpoint:

```text
Checkpoint 32 — Stage 8A.0 Controlled Publish Path to kurgin-data
```

## What was done

8A.0 is documentation only.

It documents the future controlled publish path:

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

## Rules locked

```text
kurgin-admin-mvp generates public export.
kurgin-data is the public data layer.
kurgin-streamlit-mvp / public site reads public data.
The public site must not read stones_master.csv directly.
The public site must not calculate prices.
public_stones_v1.csv must not silently replace legacy stones.csv.
V1 publish must remain manual and controlled.
```

## Empty export rule

```text
Headers-only public_stones_v1.csv is valid for preview/download.
Publishing an empty file to kurgin-data requires explicit warning and confirmation.
```

## Future publish manifest

Future publish should use or preserve:

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

## Not implemented in 8A.0

```text
code changes
Streamlit UI changes
writing exports/
writing kurgin-data
sync with site
GitHub API publishing
automation/workflows
CSV mutation
PDF/assets
DB
```

## Files changed

```text
README.md
rules/README_RULES.md
docs/CONTROLLED_PUBLISH_PATH_V1.md
CHECKPOINT_32_STAGE_08A0_CONTROLLED_PUBLISH_RULES.md
NEXT_CHAT_START_HERE.md
```

## Next possible stage

```text
8A — manual publish package / snapshot structure
```

Do not start 8A code until implementation rules are separately agreed.
