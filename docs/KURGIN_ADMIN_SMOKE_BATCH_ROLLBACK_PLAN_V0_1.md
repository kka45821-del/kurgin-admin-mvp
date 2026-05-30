# KURGIN ADMIN SMOKE BATCH ROLLBACK PLAN v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: rollback planning + execution result document.
Status: rollback check executed against repository files / no production publish.

This document records the rollback plan and the executed repository-level rollback check for saved Admin smoke rows before any production publish.

Smoke batch context:

- batch: `P-0004`
- previous smoke rows: `KRG-ML-*`
- rich smoke rows: `KRG-RICH-*`
- latest saved rich fixture count reported from live Admin: `32` stones
- production publish was not executed

Execution boundary:

- no publish;
- no `kurgin-data` update;
- no Streamlit change;
- no Analyzer/formula/scoring change;
- no schema change;
- no code change;
- no production deploy.

## 1. Final verdict

```text
PASS
```

Interpretation:

- Repository-level Admin data check found no `KRG-ML-*` or `KRG-RICH-*` rows in `data/stones.csv` at the time of this rollback task.
- Repository-level Admin data check found no `P-0004` row in `data/upload_batches.csv`.
- Therefore no data-row deletion was needed in the repository.
- `data/admin_actions.csv` was not modified; in this repository snapshot it is not present as a tracked file.
- Old real catalog rows remain present in `data/stones.csv`.
- `kurgin-data` was not changed.
- Public Streamlit was not changed.

This result means the repository state is clean with respect to the requested smoke rollback filter.

Important distinction:

```text
live Admin runtime save ≠ committed repository data
Admin save ≠ public publish
```

The live Admin app previously reported saved smoke rows, but the tracked repository files inspected for this rollback did not contain those smoke rows.

## 2. Rollback filter

Requested rollback filter:

```text
batch_number == P-0004
AND (
  stone_id starts with KRG-ML-
  OR stone_id starts with KRG-RICH-
)
```

Repository result:

```text
No matching rows found in data/stones.csv.
No P-0004 row found in data/upload_batches.csv.
```

## 3. Files checked

| File | Check | Result | Action |
|---|---|---|---|
| `data/stones.csv` | Search/remove rows where `batch_number == P-0004` and `stone_id` starts with `KRG-ML-` or `KRG-RICH-` | No matching tracked rows found | No data edit required |
| `data/upload_batches.csv` | Remove batch row `P-0004` if present and smoke-only | `P-0004` not present; existing rows are `P-0001`, `P-0002`, `P-0003` | No data edit required |
| `data/admin_actions.csv` | Preserve as audit log | File is not present as a tracked file in repository snapshot | No action |
| `docs/KURGIN_ADMIN_SMOKE_BATCH_ROLLBACK_PLAN_V0_1.md` | Record rollback execution result | Updated | Docs-only update |

## 4. `data/stones.csv` result

Result:

```text
PASS
```

Confirmed at repository level:

- no tracked `KRG-ML-*` rows found in `data/stones.csv`;
- no tracked `KRG-RICH-*` rows found in `data/stones.csv`;
- no tracked smoke rows matching the requested `P-0004` + smoke-prefix filter needed deletion;
- old real catalog rows remain present;
- schema/columns were not changed.

No `data/stones.csv` update was made.

## 5. `data/upload_batches.csv` result

Result:

```text
PASS
```

Confirmed at repository level:

- `data/upload_batches.csv` exists;
- `P-0004` is not present;
- existing tracked batch rows remain:
  - `P-0001`
  - `P-0002`
  - `P-0003`
- no upload-batch row needed deletion;
- schema/columns were not changed.

No `data/upload_batches.csv` update was made.

## 6. `data/admin_actions.csv` result

Result:

```text
PASS / NOT TRACKED
```

Confirmed at repository level:

- `data/admin_actions.csv` was not modified;
- file was not present as a tracked file in the repository snapshot used for this rollback task;
- audit-log preservation rule remains active.

Recommended rule remains:

```text
preserve admin_actions.csv as audit log if present in a runtime/local environment
```

## 7. Why no data-file update was required

The live Admin smoke reported that batch `P-0004` was saved, but the repository files available through GitHub did not contain the smoke rows or `P-0004` batch metadata.

Likely implication:

```text
live Admin runtime/local data and committed repository data are not the same state
```

Therefore, the safe repository-level rollback action is:

- do not fabricate data edits;
- do not delete real rows;
- do not change schema;
- document that no matching tracked rows were found;
- preserve no-publish boundary.

## 8. Public boundary

Rollback task did not touch:

- `kurgin-data/catalog.json`;
- `kurgin-data/data/catalog.json`;
- `kurgin-data/stones.csv`;
- `kurgin-data/upload_batches.csv`;
- public Streamlit repo/code/data;
- Analyzer;
- Formula Service;
- formula/scoring.

Because production publish was not executed, public catalog rollback was not needed.

## 9. Post-rollback checks

Repository-level checks:

| Check | Result |
|---|---:|
| `KRG-ML-*` absent from tracked `data/stones.csv` | PASS |
| `KRG-RICH-*` absent from tracked `data/stones.csv` | PASS |
| batch `P-0004` absent from tracked `data/upload_batches.csv` | PASS |
| old real rows still present in `data/stones.csv` | PASS |
| `data/stones.csv` schema unchanged | PASS |
| `data/upload_batches.csv` schema unchanged | PASS |
| `admin_actions.csv` preserved / not modified | PASS |
| `kurgin-data` unchanged | PASS |
| public Streamlit unchanged | PASS |
| Analyzer/formula/scoring untouched | PASS |
| publish not executed | PASS |

Live Admin runtime check still recommended if the deployed Admin app stores data outside the committed repository state.

## 10. If live Admin still shows smoke rows

If the live Admin app still displays `KRG-ML-*` or `KRG-RICH-*`, that means the smoke rows are in runtime/local storage rather than tracked repository files.

Required next handling:

1. Do not publish.
2. Do not click `Save catalog` / `Publish`.
3. Use live Admin UI isolation if needed:
   - `Снять партию с публикации` for batch `P-0004`, if visible.
4. Or export/download current Admin data and perform a separate approved runtime-data rollback.
5. Re-check that `KRG-ML-*` and `KRG-RICH-*` are no longer visible before any publish.

## 11. Blocked actions

Blocked by this rollback execution task:

- publish;
- update `kurgin-data`;
- change Streamlit;
- delete non-smoke rows;
- change schema;
- change code;
- change Analyzer;
- change formula/scoring;
- production deploy;
- broad cleanup deletion/move;
- deleting or editing real catalog rows;
- removing unrelated batches;
- treating Admin rollback as public catalog rollback;
- publishing `KRG-RICH-*` rows;
- publishing `KRG-ML-*` rows unless separately approved.

## 12. Acceptance checklist

This rollback execution satisfies the task if:

- `KRG-ML-*` are absent from tracked `data/stones.csv`;
- `KRG-RICH-*` are absent from tracked `data/stones.csv`;
- old real stones remain present;
- batch `P-0004` is absent from tracked `data/upload_batches.csv`;
- `admin_actions.csv` is preserved / not modified;
- `kurgin-data` is not changed;
- Streamlit is not changed;
- Analyzer/formula/scoring are untouched;
- schema is unchanged;
- rollback plan result is updated with `PASS`.

## 13. Closure

Final rollback result:

```text
PASS
```

The tracked repository state is clean for the requested smoke rollback filter.

No `data/stones.csv` or `data/upload_batches.csv` edit was required because the requested smoke rows and batch `P-0004` were not present in the tracked repository data.

Only this rollback result document was updated.
