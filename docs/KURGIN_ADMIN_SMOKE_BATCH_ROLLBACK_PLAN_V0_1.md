# KURGIN ADMIN SMOKE BATCH ROLLBACK PLAN v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: rollback planning document.
Status: pre-rollback plan / no rollback executed.

This document defines a safe rollback or isolation plan for saved Admin smoke rows before any production publish.

Smoke batch context:

- batch: `P-0004`
- previous smoke rows: `KRG-ML-*`
- rich smoke rows: `KRG-RICH-*`
- latest saved rich fixture count: `32` stones
- production publish was not executed

This task does not publish, does not update `kurgin-data`, does not change Streamlit, does not change Analyzer, does not change formula/scoring, does not change schema, does not delete real data, does not execute rollback, and does not deploy production.

## 1. Final verdict

```text
SAFE_TO_ROLLBACK
```

Interpretation:

- The current smoke scope is traceable by `batch_number = P-0004` and smoke-specific `stone_id` prefixes.
- The rollback scope must now include both `KRG-ML-*` and `KRG-RICH-*` rows where applicable.
- A targeted rollback is possible without touching non-smoke rows if filters are strict.
- The safest rollback is to remove only smoke rows from local Admin `data/stones.csv` and remove only batch `P-0004` from local Admin `data/upload_batches.csv`.
- `data/admin_actions.csv` should preferably be preserved as audit history, or a rollback action should be appended in a separate approved rollback task.
- Production `kurgin-data` and public Streamlit should remain unchanged because publish was not executed.

This verdict does not execute the rollback. It only confirms that a targeted rollback plan is available.

## 2. Current rollback scope

The rollback scope now includes:

| Scope item | Identifier | Handling |
|---|---|---|
| Previous main/large smoke rows | `stone_id` starts with `KRG-ML-` | Remove or isolate before publish. |
| Rich fixture smoke rows | `stone_id` starts with `KRG-RICH-` | Remove or isolate before publish. |
| Smoke batch metadata | `batch_number == P-0004` | Remove or isolate before publish. |
| Admin action log | `entity == P-0004` where relevant | Preserve as audit log by default. |

Critical rule:

```text
KRG-RICH-* must not be published to kurgin-data
KRG-ML-* must not be published to kurgin-data unless separately approved
Admin save ≠ public publish
```

## 3. Where saved rows are stored

The Admin save path writes to local Admin data files, not to `kurgin-data`.

| File | Expected smoke impact | Rollback handling |
|---|---|---|
| `data/stones.csv` | Contains smoke rows in batch `P-0004`, including `KRG-ML-*` and/or `KRG-RICH-*` rows depending on latest save state | Remove only rows where `batch_number == P-0004` and `stone_id` starts with approved smoke prefixes. |
| `data/upload_batches.csv` | Contains or updates batch metadata row for `P-0004` | Remove only row where `batch_number == P-0004`, or keep only if isolation rather than full rollback is chosen. |
| `data/admin_actions.csv` | May contain `import_excel_batch` actions for `P-0004` | Prefer preserving as audit log, or append a rollback action in a separate approved rollback task. |

## 4. Can only smoke rows be safely deleted?

Answer:

```text
Yes, if rollback filters are strict.
```

Allowed smoke prefixes:

```text
KRG-ML-
KRG-RICH-
```

Additional safety condition:

```text
batch_number == `P-0004`
```

Recommended combined filter for rollback planning:

```text
remove rows where batch_number == `P-0004`
AND (stone_id starts with `KRG-ML-` OR stone_id starts with `KRG-RICH-`)
```

Reason:

- `KRG-ML-*` was the earlier main/large smoke fixture prefix;
- `KRG-RICH-*` is the rich fixture smoke prefix;
- `P-0004` is the current smoke batch number;
- using batch plus prefix reduces the risk of accidentally deleting non-smoke rows.

Do not delete rows that do not match the smoke batch and smoke prefixes unless a separate review proves they are part of the smoke batch.

## 5. Can batch `P-0004` be removed from `data/upload_batches.csv`?

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

- rollback of `data/upload_batches.csv` should happen in the same rollback task as removal of smoke rows from `data/stones.csv`;
- do not remove unrelated batch rows.

## 6. What to do with `data/admin_actions.csv`

Recommended default:

```text
preserve admin_actions.csv as audit log
```

Reason:

- the action log records that smoke imports happened;
- deleting audit history can reduce traceability;
- preserving the action log is safer than editing history.

Alternative if strict cleanup is required:

- append a new rollback action entry describing removal of smoke batch `P-0004`;
- do not delete original action rows unless a separate approved cleanup task explicitly requires it.

Possible rollback action wording:

```text
action = rollback_smoke_batch
entity = P-0004
source = admin_rollback
result = success
details = Removed KRG-ML-* and KRG-RICH-* smoke rows from local Admin data before publish; kurgin-data unchanged.
```

This document does not implement that action.

## 7. UI rollback / isolation options

### 7.1. Existing UI option: remove from publication

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

### 7.2. Existing UI option: edit selected batch

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

## 8. Safe manual rollback through files

A safe manual rollback is possible through local Admin files if done as a separate approved rollback task.

Required file operations:

1. Open local Admin `data/stones.csv`.
2. Remove only rows where:

```text
batch_number == `P-0004`
AND (stone_id starts with `KRG-ML-` OR stone_id starts with `KRG-RICH-`)
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

## 9. Post-rollback checks

After rollback, verify:

- `KRG-ML-*` rows are no longer visible in Admin catalog, if they exist in current saved state;
- `KRG-RICH-*` rows are no longer visible in Admin catalog;
- batch `P-0004` is no longer listed in Admin batches if `upload_batches.csv` was cleaned;
- old catalog rows are still present;
- no non-smoke rows were removed;
- `data/stones.csv` schema/columns are unchanged;
- `data/upload_batches.csv` schema/columns are unchanged;
- `kurgin-data` remains unchanged;
- public Streamlit remains unchanged;
- no publish occurred;
- Analyzer/formula/scoring remain untouched.

## 10. Public boundary

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

## 11. Recommended rollback method

Recommended method:

```text
targeted file rollback in kurgin-admin-mvp only
```

Precise actions for a future approved rollback task:

1. Remove smoke rows with `batch_number == P-0004` and `stone_id` prefix `KRG-ML-` or `KRG-RICH-` from local Admin `data/stones.csv`.
2. Remove `P-0004` row from local Admin `data/upload_batches.csv`.
3. Preserve `data/admin_actions.csv` as audit log.
4. Verify old catalog rows remain.
5. Verify Admin catalog no longer shows `KRG-ML-*` / `KRG-RICH-*` rows.
6. Do not publish.
7. Do not touch `kurgin-data`.

## 12. Blocked actions

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
- treating Admin rollback as public catalog rollback;
- publishing `KRG-RICH-*` rows.

## 13. Acceptance checklist

This rollback plan satisfies the task if:

- `docs/KURGIN_ADMIN_SMOKE_BATCH_ROLLBACK_PLAN_V0_1.md` is updated;
- rollback scope includes `KRG-RICH-*` rows;
- rollback scope includes `KRG-ML-*` rows where applicable;
- rollback scope includes batch `P-0004` / current saved smoke batch;
- `data/admin_actions.csv` audit recommendation is documented;
- `Admin save ≠ public publish` is documented;
- `KRG-RICH-* must not be published to kurgin-data` is documented;
- no rollback is performed;
- no publish is performed;
- no data/code/schema changes are made.

## 14. Closure

Final verdict:

```text
SAFE_TO_ROLLBACK
```

The smoke scope is identifiable and can be rolled back safely with a targeted local Admin data rollback.

The rollback should remove only smoke rows from batch `P-0004` using `KRG-ML-*` and `KRG-RICH-*` prefixes, remove only the `P-0004` upload batch row if full rollback is chosen, preserve or separately annotate the admin action log, and avoid any `kurgin-data` or public Streamlit change.
