# KURGIN ADMIN SAVE BATCH IMPACT CHECK v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: docs-only impact check before clean save smoke.
Status: pre-save impact analysis / no save executed.

This document records what the Admin button `Сохранить партию` changes before any clean save smoke is executed.

This task did not click save, did not publish, did not change code, did not change UI, did not change data, did not change schema, did not change Streamlit, did not change Analyzer, and did not change formula/scoring.

## 1. Final verdict

```text
RISK
```

Interpretation:

- Save batch impact is understandable and limited to local Admin repository data files, not `kurgin-data`.
- The button can be used for a controlled save smoke without production publish if the operator keeps the mode as `Добавить к текущим` and uses traceable smoke IDs such as `KRG-CLEAN-*`.
- However, save still mutates local Admin data files and writes an admin action log, so it is not a no-op.
- A clean rollback plan is required before clicking save.

Why not `SAFE_TO_SAVE`:

- The save action writes to local admin CSV files.
- The save action appends or replaces catalog rows depending on UI mode.
- The save action writes batch metadata and an admin action log.
- A safe rollback is possible only if smoke rows and batch metadata are clearly identifiable and the operator does not use replace mode by mistake.

Why not `BLOCKED`:

- No source-level blocker was found.
- The impact is narrow and identifiable.
- Production publish is separate and not triggered by `Сохранить партию`.

## 2. What triggers save

The save path is inside `admin_upload.py` in `render_upload_tab()`.

The button is enabled only when:

- the confirmation checkbox is selected;
- there are no critical errors;
- `batch_number` is not empty;
- `supplier_name` is not empty.

Save button logic:

```text
can_save = confirmed and critical_errors.empty and bool(batch_number.strip()) and bool(supplier_name.strip())
```

When clicked, the save path:

1. loads current stones from local Admin data;
2. either appends normalized rows or replaces the whole local catalog depending on selected mode;
3. saves resulting stones through `save_stones(result)`;
4. upserts the batch log through `upsert_batch_log(...)`;
5. writes an admin action through `write_admin_action(...)`.

## 3. Files changed by save batch

### 3.1. Direct files changed

The save batch path can change these local Admin repository data files:

| File | Change type | Why |
|---|---|---|
| `data/stones.csv` | Append or replace depending on mode | `save_stones(result)` writes the full stone table. |
| `data/upload_batches.csv` | Upsert batch row | `upsert_batch_log(...)` removes any existing same batch number and writes a new batch metadata row. |
| `data/admin_actions.csv` | Append action row | `write_admin_action(...)` records `import_excel_batch`. |

### 3.2. Files not changed by save batch

The save batch path does not directly change:

- `kurgin-data/catalog.json`;
- `kurgin-data/data/catalog.json`;
- `kurgin-data/stones.csv`;
- `kurgin-data/upload_batches.csv`;
- Streamlit public app files;
- Analyzer files;
- Formula/scoring files;
- CI files;
- public publish outputs.

## 4. Does save add rows to `data/stones.csv`?

Answer:

```text
Yes, if mode is `Добавить к текущим`.
```

In add mode, the save code does:

```text
result = current + normalized
save_stones(result)
```

Therefore a clean save smoke will append the normalized smoke fixture rows to local Admin `data/stones.csv`.

Important risk:

```text
If mode is `Заменить весь каталог`, save writes only the normalized fixture and replaces the local Admin catalog table.
```

For smoke testing, only this mode is acceptable:

```text
Добавить к текущим
```

## 5. Does save add a record to `data/upload_batches.csv`?

Answer:

```text
Yes.
```

`upsert_batch_log(...)` loads existing batches, removes any row with the same `batch_number`, and writes a new batch metadata row with:

- `batch_number`;
- `upload_date`;
- `supplier_name`;
- `stones_count`;
- `upload_confirmed = True`;
- `notes`.

This means a smoke batch can be identified and removed later by its `batch_number` if the batch number is unique and controlled.

## 6. Does save add a record to `data/admin_actions.csv`?

Answer:

```text
Yes.
```

`write_admin_action(...)` appends an action row with:

- `created_at`;
- `action = import_excel_batch`;
- `entity = batch_number`;
- `rows_count = len(normalized)`;
- `source = admin_upload`;
- `result = success` by default;
- details with supplier, sheet and mode.

This log entry is not published to `kurgin-data`, but it is a local Admin repo data mutation.

## 7. Can smoke rows be distinguished by `stone_id = KRG-CLEAN-*`?

Answer:

```text
Yes, if the clean fixture explicitly uses unique stone_id values with the `KRG-CLEAN-*` prefix.
```

Recommended fixture IDs:

- `KRG-CLEAN-001`
- `KRG-CLEAN-002`
- `KRG-CLEAN-003`

Required smoke discipline:

- every smoke row must use `stone_id` prefix `KRG-CLEAN-`;
- batch number should also be smoke-specific, for example `SMOKE-CLEAN-001` or `P-SMOKE-CLEAN-001`;
- supplier name should include `SMOKE`;
- notes should include `smoke_clean_save_no_publish`;
- mode must be `Добавить к текущим`.

If `stone_id` is empty, the import code can auto-generate IDs from the batch number, which is less clean for targeted rollback. Therefore smoke fixtures should not leave `stone_id` empty.

## 8. Safe rollback options

### 8.1. Preferred rollback if save is clicked

Safe rollback after a smoke save requires removing only smoke rows and smoke batch/action records.

Rollback targets:

1. Remove rows from `data/stones.csv` where `stone_id` starts with `KRG-CLEAN-`.
2. Remove the smoke batch row from `data/upload_batches.csv` by exact `batch_number`.
3. Optionally remove or preserve the `data/admin_actions.csv` smoke action row.

Recommended handling of `admin_actions.csv`:

- Prefer preserving the log row and adding a later rollback log entry if audit trail matters.
- If the requirement is strict data cleanup, remove only the exact smoke action row by `entity = batch_number` and `action = import_excel_batch` in a separate approved cleanup/rollback task.

### 8.2. Git rollback option

If the save happens inside a tracked repo state and the smoke save commit is isolated, rollback can be done by reverting the smoke-save commit.

However, this only works cleanly if:

- no unrelated Admin data changes are mixed into the same commit;
- no production publish happened;
- save result is committed separately;
- the smoke batch is clearly named.

### 8.3. Manual CSV rollback option

Manual rollback is possible by editing local Admin CSV files, but it should be done only through a separate approved rollback task.

Manual deletion from CSV is not approved by this impact check.

## 9. Can save smoke be done without publishing to `kurgin-data`?

Answer:

```text
Yes.
```

`Сохранить партию` affects local Admin data files only.

Production publish to `kurgin-data` is a separate flow in the publish tab and is not triggered by save batch.

Required operator boundary:

- do not open/confirm the publish action;
- do not click `Опубликовать catalog.json`;
- do not manually upload downloaded files to `kurgin-data`;
- stop after save verification if clean save smoke is approved.

## 10. Pre-save checklist

Before any clean save smoke, confirm:

- mode is `Добавить к текущим`, not `Заменить весь каталог`;
- `batch_number` is unique and smoke-specific;
- all fixture `stone_id` values start with `KRG-CLEAN-`;
- supplier name contains `SMOKE`;
- notes contain `smoke_clean_save_no_publish`;
- no critical errors are shown;
- `price_rub = 0` warning is expected if present;
- production publish tab is not used;
- no `kurgin-data` operation is performed;
- rollback plan is accepted before save.

## 11. Impact summary

| Question | Answer |
|---|---|
| Which files does save batch change? | Local Admin `data/stones.csv`, `data/upload_batches.csv`, `data/admin_actions.csv`. |
| Does it add rows to `data/stones.csv`? | Yes in `Добавить к текущим` mode. |
| Does it add a record to `data/upload_batches.csv`? | Yes, upsert by `batch_number`. |
| Can smoke rows be identified by `KRG-CLEAN-*`? | Yes, if fixture uses those `stone_id` values explicitly. |
| Is rollback possible? | Yes, if smoke rows/batch/action are uniquely identifiable. |
| Can save smoke be done without publishing to `kurgin-data`? | Yes. Save batch is separate from publish. |
| Is it a no-op? | No. It mutates local Admin data files. |
| Is production publish triggered? | No, not by save batch itself. |

## 12. Blocked actions

Blocked by this impact check:

- clicking save now;
- publish to `kurgin-data`;
- changing `catalog.json`;
- changing `data/catalog.json`;
- changing public `stones.csv` / `upload_batches.csv` in `kurgin-data`;
- Streamlit changes;
- Analyzer changes;
- formula/scoring changes;
- schema changes;
- production deploy;
- cleanup deletion/move;
- file deletion;
- file moving;
- code changes.

## 13. Recommended next step

Recommended next step:

```text
controlled clean save smoke may proceed only after operator confirms rollback plan and pre-save checklist
```

Suggested verdict handling:

- This document verdict remains `RISK` until the operator confirms the rollback plan.
- After confirmation, the practical execution status can be treated as `SAFE_TO_SAVE` for one isolated clean save smoke using `KRG-CLEAN-*` IDs and no publish.

## 14. Acceptance checklist

This document satisfies the impact-check task if:

- `docs/KURGIN_ADMIN_SAVE_BATCH_IMPACT_CHECK_V0_1.md` exists;
- save was not clicked;
- publish was not executed;
- code was not changed;
- UI was not changed;
- `kurgin-data` was not changed;
- Streamlit was not changed;
- Analyzer/formula/scoring were not touched;
- files changed by save are listed;
- `data/stones.csv` impact is described;
- `data/upload_batches.csv` impact is described;
- `data/admin_actions.csv` impact is described;
- `KRG-CLEAN-*` traceability is described;
- rollback options are described;
- save without publish is confirmed as possible;
- verdict is included.

## 15. Closure

Final verdict:

```text
RISK
```

The save batch impact is understood and bounded, but save is not a no-op.

A controlled clean save smoke can be considered only after confirming the pre-save checklist and rollback plan.
