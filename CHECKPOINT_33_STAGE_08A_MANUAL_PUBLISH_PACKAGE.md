# Checkpoint 33 — Stage 8A Manual Publish Package

Stable checkpoint:

```text
Checkpoint 33 — Stage 8A Manual Publish Package / Snapshot Structure
```

## What changed

8A adds an in-memory manual publish package on the public-layer page.

Location:

```text
Цены → Index и просмотр → Публичный слой
```

The new block is:

```text
Manual publish package — kurgin-data
```

## Package contents

The package is downloaded as:

```text
kurgin-public-publish-package-YYYYMMDD-HHMMSS.zip
```

It contains:

```text
public_stones_v1.csv
publish_manifest.json
publish_checks.json
README_MANUAL_PUBLISH.md
```

## Rules preserved

```text
8A creates the package only in memory.
8A does not write exports/.
8A does not write kurgin-data.
8A does not sync with the site.
8A does not change stones_master.csv.
8A does not change catalog_sections.csv.
8A does not change status / availability_status / catalog_section.
8A does not change prices.
8A does not turn on allow_price_on_request.
8A does not create backup.
8A does not create PDF/assets.
```

## Empty export rule

```text
Headers-only public_stones_v1.csv is valid for package preview/download.
Publishing an empty package to kurgin-data must require separate human confirmation.
```

## Files changed

```text
README.md
NEXT_CHAT_START_HERE.md
CHECKPOINT_33_STAGE_08A_MANUAL_PUBLISH_PACKAGE.md
app.py
modules/storage.py
rules/README_RULES.md
docs/CONTROLLED_PUBLISH_PATH_V1.md
docs/MANUAL_PUBLISH_PACKAGE_V1.md
```

## Next possible stage

```text
8B — public site reads public_stones_v1.csv
```

Do not start 8B code until rules are separately agreed.
