# KURGIN ADMIN IMPORT SMOKE v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: manual Admin import smoke checkpoint.
Status: live import smoke completed / no production publish.

This document records the manual live Admin import smoke checkpoint for live Admin open + controlled Excel import/preview without production publish.

Repositories not changed:

- `kurgin-streamlit-mvp`
- `kurgin-data`
- `kurgin-score-analyzer`
- `kurgin-formula-service`

This checkpoint did not publish to `kurgin-data`, did not change Streamlit, did not change Analyzer, did not change formula/scoring, did not change data schema, did not perform cleanup, and did not deploy production.

## 1. Final verdict

```text
PASS for live upload / diagnostics / preview / validation
RISK for publish because publish was not tested
```

Operational verdict:

```text
RISK
```

Interpretation:

- Live Admin app opened.
- Controlled smoke Excel uploaded.
- Admin import UI accepted the file.
- Sheet diagnostics worked.
- `KURGIN_Template` was detected.
- Header row was found at row `1`.
- Column recognition worked with `10` recognized columns and `9` unrecognized columns.
- Raw preview and normalized preview were shown.
- Validation worked.
- Missing `report_number` produced a critical error.
- `price_rub = 0` produced a warning.
- Save batch remained blocked because a critical error exists.
- Production publish was not executed.

This confirms the live upload / diagnostics / preview / validation path.

The remaining risk is publish, because publish was intentionally not tested in this smoke.

## 2. Required task vs actual execution

| Required check | Execution status | Result |
|---|---|---|
| Open live Admin app | Executed | PASS |
| Use small controlled Excel fixture/template | Executed | PASS |
| Upload through Admin upload | Executed | PASS |
| Confirm file accepted | Confirmed | PASS |
| Confirm sheet diagnostics works | Confirmed | PASS |
| Confirm `KURGIN_Template` detected | Confirmed | PASS |
| Confirm header row found | Confirmed: row `1` | PASS |
| Confirm columns recognized | Confirmed: `10` recognized, `9` unrecognized | PASS |
| Confirm raw preview shown | Confirmed | PASS |
| Confirm normalized preview shown | Confirmed | PASS |
| Confirm validation works | Confirmed | PASS |
| Confirm missing `report_number` critical error | Confirmed | PASS |
| Confirm `price_rub = 0` warning | Confirmed | PASS |
| Confirm save blocked when critical error exists | Confirmed | PASS |
| Avoid production publish | Confirmed | PASS |
| Avoid code/UI/data/CI changes | Confirmed by task behavior | PASS |

## 3. Live smoke result

### 3.1. Admin app entry

Runtime status:

```text
PASS
```

Confirmed:

- live Admin app opened;
- Admin import path was reachable;
- no production publish was needed for this smoke.

### 3.2. Excel upload / import flow

Runtime status:

```text
PASS
```

Confirmed:

- controlled smoke Excel was uploaded;
- file was accepted by the Admin upload UI;
- sheet diagnostics worked;
- `KURGIN_Template` was detected;
- header row was found at row `1`;
- column recognition worked:
  - recognized columns: `10`;
  - unrecognized columns: `9`.

Interpretation:

```text
Admin upload accepts the controlled fixture and exposes diagnostics/mapping feedback.
```

### 3.3. Raw / normalized preview

Runtime status:

```text
PASS
```

Confirmed:

- raw preview was shown;
- normalized preview was shown;
- the UI allowed checking the imported rows before save/publish.

Interpretation:

```text
Preview path is operational for the controlled smoke fixture.
```

### 3.4. Validation / critical-warning separation

Runtime status:

```text
PASS
```

Confirmed:

- validation worked;
- row missing `report_number` produced a critical error;
- `price_rub = 0` produced a warning;
- critical/warning separation was visible;
- save batch remained blocked because a critical error exists.

Interpretation:

```text
Critical validation blocks save.
Price missing / zero remains warning-level in this smoke.
```

## 4. Production publish boundary

Production publish was not executed.

Explicitly not done:

- no `kurgin-data` publish;
- no `catalog.json` update;
- no `data/catalog.json` update;
- no `stones.csv` update;
- no `upload_batches.csv` update;
- no Streamlit data refresh;
- no production deploy.

This satisfies the no-publish boundary for this smoke.

Publish verdict:

```text
RISK: not tested
```

Reason:

- this smoke was intentionally limited to live Admin open + import/diagnostics/preview/validation;
- production publish was out of scope and blocked.

## 5. Blockers

### 5.1. Runtime blockers

```text
None for live upload / diagnostics / preview / validation path.
```

### 5.2. Remaining non-blocking limitation

| ID | Limitation | Impact | Required future action |
|---|---|---|---|
| LIM-001 | Publish was not tested | Cannot mark publish flow PASS from this smoke | Run separate controlled publish smoke only after explicit approval |

### 5.3. No source-level code blocker found

No source-level issue was found that justifies code changes under this task.

No fix was made.

## 6. Risk items

| ID | Risk | Severity | Handling |
|---|---|---:|---|
| RISK-001 | Publish remains untested. | Medium | Run controlled publish smoke only after explicit approval. |
| RISK-002 | Admin import auto-marks MVP flags and relies on Publication Gate review. | Medium | Continue requiring preview/gate review before any save/publish workflow. |
| RISK-003 | Unknown/unrecognized columns were present. | Low-medium | Keep them inactive unless explicitly mapped by a separate contract/task. |
| RISK-004 | Save was blocked by critical error as expected, so save path with a clean fixture is not yet confirmed here. | Low-medium | Run a separate clean-fixture save smoke if needed, still without publish. |
| RISK-005 | Production data must remain untouched during import-only smoke. | High | Keep publish blocked unless a separate publish-smoke task is approved. |

## 7. Evidence summary

Manual live test evidence reported:

```text
live Admin app opened
smoke Excel uploaded
sheet diagnostics worked
KURGIN_Template detected
header row found: 1
10 columns recognized
9 columns unrecognized
raw/normalized preview shown
validation worked
row missing report_number produced critical error
price_rub = 0 produced warning
Save batch remained blocked because critical error exists
production publish was NOT executed
```

## 8. Allowed next actions

Allowed next actions:

1. Keep this smoke result as live validation evidence for upload / diagnostics / preview / validation.
2. Run a clean-fixture save smoke, if explicitly needed, without production publish.
3. Run publish dry-run/manual download validation.
4. Run controlled publish smoke with `GITHUB_TOKEN` only after explicit approval.
5. Add or document a small smoke fixture path only if separately approved.
6. Keep unrecognized columns inactive unless a separate mapping/contract update is approved.

## 9. Blocked actions

Blocked by this smoke task:

- publish to `kurgin-data`;
- update `catalog.json`;
- update `data/catalog.json`;
- update `stones.csv`;
- update `upload_batches.csv`;
- data schema changes;
- code changes without separate approval;
- UI changes;
- Streamlit changes;
- Analyzer changes;
- formula/scoring changes;
- production deploy;
- payment/reserve/sold;
- auth/pro roles;
- PDF/report/Verify;
- cleanup deletion/move;
- file deletion;
- file moving.

## 10. Acceptance checklist

This document satisfies the smoke-result update task if:

- `docs/KURGIN_ADMIN_IMPORT_SMOKE_V0_1.md` is updated;
- live Admin open is recorded;
- smoke Excel upload is recorded;
- sheet diagnostics result is recorded;
- `KURGIN_Template` detection is recorded;
- header row `1` is recorded;
- `10` recognized and `9` unrecognized columns are recorded;
- raw/normalized preview is recorded;
- validation result is recorded;
- missing `report_number` critical error is recorded;
- `price_rub = 0` warning is recorded;
- save blocked by critical error is recorded;
- production publish not executed is recorded;
- no code changes are made;
- no UI changes are made;
- no data/schema changes are made;
- no Analyzer/formula/scoring changes are made.

## 11. Closure

Final runtime result:

```text
PASS for live upload / diagnostics / preview / validation
RISK for publish because publish was not tested
```

Operational document verdict remains:

```text
RISK
```

The manual live Admin import smoke confirms the upload, diagnostics, preview and validation path.

Publish remains a separate untested path and must not be inferred as passed from this import-only smoke.
