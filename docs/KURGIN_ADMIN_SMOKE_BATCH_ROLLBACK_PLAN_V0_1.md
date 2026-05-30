# KURGIN ADMIN SMOKE BATCH ROLLBACK PLAN v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: rollback planning document.
Status: pre-rollback plan / no rollback executed.

This document defines a safe rollback plan for the saved Admin smoke batch before any production publish.

Smoke batch context:

- batch: `P-0004`
- rows: `KRG-ML-001` ... `KRG-ML-012`
- saved stones: `12`
- visible in Admin catalog
- old rows did not disappear
- production publish was not executed

This task does not publish, does not update `kurgin-data`, does not change Streamlit, does not change Analyzer, does not change formula/scoring, does not change schema, does not delete real data, and does not deploy production.

## 1. Final verdict

```text
SAFE_TO_ROLLBACK
```

Interpretation:

- The smoke batch is traceable by both `batch_number = P-0004` and `stone_id` prefix `KRG-ML-`.
- A targeted rollback is possible without touching non-smoke rows.
- The safest rollback is to remove only the smoke rows from local Admin `data/stones.csv` and remove only batch `P-0004` from local Admin `data/upload_batches.csv`.
- `data/admin_actions.csv` should preferably be preserved as audit history, or a rollback action should be appended in a separate approved task.
- Production `kurgin-data` and public Streamlit should remain unchanged because publish was not executed.

This verdict does not execute the rollback. It only confirms that a targeted rollback plan is available.

## 2. Where saved rows are stored

The Admin save path writes to local Admin data files, not to `kurgin-data`.

| File | Expected smoke impact | Rollback handling |
|---|---|---|
| `data/stones.csv` | Contains `12` saved smoke rows with `stone_id` `KRG-ML-001` ... `KRG-ML-012` and batch `P-0004` | Remove only rows where `stone_id` starts with `KRG-ML-` and/or `batch_number == P-0004`. |
| `data/upload_batches.csv` | Contains batch metadata row for `P-0004` | Remove only row where `batch_number == P-0004`. |
| `data/admin_actions.csv` | May contain an `import_excel_batch` action for `P-0004` | Prefer preserving as audit log, or append a rollback action in a separate approved rollback task. |

## 3. Can only `KRG-ML-*` rows be safely deleted?

Answer:

```text
Yes, if rollback filters are strict.
```

Allowed target condition:

```text
stone_id starts with `KRG-ML-`
```

Additional safety condition:

```text
batch_number == `P-0004`
```

Recommended combined filter for rollback planning:

```text
remove rows where stone_id starts with `KRG-ML-` AND batch_number == `P-0004`
```

Reason:

- `KRG-ML-*` was the smoke fixture prefix;
- `P-0004` was the smoke batch number;
- using both conditions reduces the risk of accidentally deleting non-smoke rows.

Do not delete rows that do not match both smoke identifiers unless a separate review proves they are part of the smoke batch.

## 4. Can batch `P-0004` be removed from `data/upload_batches.csv`?

Answer:

```text
Yes.
```

Safe target condition:

```text
batch_number == `P-0004`
```

Expected effect:

- removes only the smoke batch record;
- does not affect older batches;
- does not affect public `kurgin-data` unless a separate publish happens later.

Important:

- rollback of `data/upload_batches.csv` should happen in the same rollback task as removal of `KRG-ML-*` rows from `data/stones.csv`.
- Do not remove unrelated batch rows.

## 5. What to do with `data/admin_actions.csv`

Recommended default:

```text
preserve admin_actions.csv as audit log
```

Reason:

- the action log records that a smoke import happened;
- deleting audit history can reduce traceability;
- preserving the action log is safer than editing history.

Alternative if strict cleanup is required:

- append a new rollback action entry describing removal of smoke batch `P-0004`;
- do not delete the original action row unless a separate approved cleanup task explicitly requires it.

Possible rollback action wording:

```text
action = rollback_smoke_batch
entity = P-0004
source = admin_rollback
result = success
details = Removed KRG-ML-* smoke rows from local Admin data before publish; kurgin-data unchanged.
```

This document does not implement that action.

## 6. UI rollback options

### 6.1. Existing UI option: remove from publication

`admin_batches.py` includes a UI option:

```text
Снять партию с публикации
```

Source behavior:

- selects the chosen batch;
- sets `show_in_catalog = False`;
- sets `current_status = internal_review`;
- saves local Admin `data/stones.csv`.

Usefulness:

- this can isolate the smoke batch from future publication preview;
- it does not delete the smoke rows;
- it still mutates local Admin data;
- it does not clean `data/upload_batches.csv`.

This is an isolation option, not a full rollback.

### 6.2. Existing UI option: edit selected batch

The batch editor uses a dynamic table and saves the selected batch back to `data/stones.csv`.

Potential use:

- in theory, rows could be removed from the selected batch through the editor if the UI supports row deletion correctly.

Risk:

- manual UI row deletion can be error-prone;
- it may upsert batch metadata again;
- it is less controlled than a targeted file rollback.

Recommendation:

```text
Do not rely on UI deletion as the primary rollback method.
Use a targeted file rollback plan instead.
```

## 7. Safe manual rollback through files

A safe manual rollback is possible through local Admin files if done as a separate approved rollback task.

Required file operations:

1. Open local Admin `data/stones.csv`.
2. Remove only rows where:

```text
stone_id starts with `KRG-ML-`
AND batch_number == `P-0004`
```

3. Open local Admin `data/upload_batches.csv`.
4. Remove only the row where:

```text
batch_number == `P-0004`
```

5. Preserve `data/admin_actions.csv` as audit log, or append a rollback action in a separate approved task.
6. Do not change any schema or column order.
7. Do not edit `kurgin-data`.
8. Do not publish.

Manual rollback must be reviewed before commit.

## 8. Post-rollback checks

After rollback, verify:

- `KRG-ML-*` rows are no longer visible in Admin catalog;
- batch `P-0004` is no longer listed in Admin batches if `upload_batches.csv` was cleaned;
- old catalog rows are still present;
- no non-smoke rows were removed;
- `data/stones.csv` schema/columns are unchanged;
- `data/upload_batches.csv` schema/columns are unchanged;
- `kurgin-data` remains unchanged;
- public Streamlit remains unchanged;
- no publish occurred;
- Analyzer/formula/scoring remain untouched.

## 9. Public boundary

Rollback of the Admin smoke batch must remain local to `kurgin-admin-mvp`.

It must not touch:

- `kurgin-data/catalog.json`;
- `kurgin-data/data/catalog.json`;
- `kurgin-data/stones.csv`;
- `kurgin-data/upload_batches.csv`;
- public Streamlit repo/code/data;
- Analyzer;
- Formula Service;
- formula/scoring.

Because production publish was not executed, public catalog rollback should not be needed.

## 10. Recommended rollback method

Recommended method:

```text
targeted file rollback in kurgin-admin-mvp only
```

Precise actions for a future approved rollback task:

1. Remove `KRG-ML-*` rows with `batch_number == P-0004` from local Admin `data/stones.csv`.
2. Remove `P-0004` row from local Admin `data/upload_batches.csv`.
3. Preserve `data/admin_actions.csv` as audit log.
4. Verify old catalog rows remain.
5. Verify Admin catalog no longer shows `KRG-ML-*` rows.
6. Do not publish.
7. Do not touch `kurgin-data`.

## 11. Blocked actions

Blocked by this rollback plan task:

- publish;
- update `kurgin-data`;
- change Streamlit;
- delete non-smoke rows;
- change schema;
- change code unless separately approved;
- change Analyzer;
- change formula/scoring;
- production deploy;
- broad cleanup deletion/move;
- deleting or editing real catalog rows;
- removing unrelated batches;
- treating Admin rollback as public catalog rollback.

## 12. Acceptance checklist

This rollback plan satisfies the task if:

- `docs/KURGIN_ADMIN_SMOKE_BATCH_ROLLBACK_PLAN_V0_1.md` exists;
- saved-row storage locations are documented;
- `data/stones.csv` rollback target is documented;
- `data/upload_batches.csv` rollback target is documented;
- `data/admin_actions.csv` audit recommendation is documented;
- UI isolation/deletion options are documented;
- safe manual rollback through files is documented;
- post-rollback checks are documented;
- `kurgin-data` no-change boundary is documented;
- Streamlit no-change boundary is documented;
- Analyzer/formula/scoring no-change boundary is documented;
- verdict is included.

## 13. Closure

Final verdict:

```text
SAFE_TO_ROLLBACK
```

The smoke batch is identifiable and can be rolled back safely with a targeted local Admin data rollback.

The rollback should remove only `KRG-ML-*` rows from batch `P-0004`, remove only the `P-0004` upload batch row, preserve or separately annotate the admin action log, and avoid any `kurgin-data` or public Streamlit change.
