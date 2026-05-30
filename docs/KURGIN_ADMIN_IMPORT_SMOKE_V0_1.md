# KURGIN ADMIN IMPORT SMOKE v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: manual Admin import smoke checkpoint.
Status: live import smoke completed / clean fixture smoke completed / no production publish.

This document records manual live Admin import smoke checkpoints for Admin open + controlled Excel import/preview without production publish.

Repositories not changed:

- `kurgin-streamlit-mvp`
- `kurgin-data`
- `kurgin-score-analyzer`
- `kurgin-formula-service`

This checkpoint did not publish to `kurgin-data`, did not change Streamlit, did not change Analyzer, did not change formula/scoring, did not change data schema, did not perform cleanup, and did not deploy production.

## 1. Final verdict

```text
PASS for clean import / preview / validation
RISK for publish because publish was not tested
```

Operational verdict:

```text
RISK
```

Interpretation:

- Live Admin app opened.
- Controlled smoke Excel upload path worked.
- Clean Excel fixture uploaded.
- `KURGIN_Template` was detected.
- Header row was detected.
- Column recognition worked.
- Raw preview and normalized preview were shown.
- Validation worked.
- Clean fixture produced no critical errors.
- `price_rub = 0` produced a warning on row `3`.
- Save was not clicked.
- Production publish was not executed.
- `kurgin-data` was not changed.

This confirms the live Admin import / diagnostics / preview / validation path for both a blocking-critical fixture and a clean fixture.

The remaining risk is publish, because publish was intentionally not tested.

## 2. Smoke run summary

| Smoke run | Purpose | Runtime result | Publish status |
|---|---|---:|---:|
| Run 1 — controlled fixture with critical error | Confirm critical/warning separation and blocked save | PASS for upload / diagnostics / preview / validation | Not executed |
| Run 2 — clean Excel fixture | Confirm clean import / preview / validation with no critical errors | PASS for clean import / preview / validation | Not executed |

## 3. Run 1 — controlled fixture with critical error

### 3.1. Result

```text
PASS for live upload / diagnostics / preview / validation
RISK for publish because publish was not tested
```

Confirmed:

- live Admin app opened;
- smoke Excel uploaded;
- sheet diagnostics worked;
- `KURGIN_Template` detected;
- header row found: `1`;
- `10` columns recognized;
- `9` columns unrecognized;
- raw preview shown;
- normalized preview shown;
- validation worked;
- row missing `report_number` produced a critical error;
- `price_rub = 0` produced a warning;
- save batch remained blocked because a critical error exists;
- production publish was not executed.

Interpretation:

```text
Critical validation blocks save.
Price missing / zero remains warning-level in this smoke.
```

## 4. Run 2 — clean Excel fixture

### 4.1. Result

```text
PASS for clean import / preview / validation
RISK for publish because publish was not tested
```

Confirmed:

- clean Excel fixture uploaded;
- `KURGIN_Template` detected;
- header row detected;
- `15` columns recognized;
- `8` columns unrecognized;
- raw preview shown;
- normalized preview shown;
- critical errors not found;
- `price_rub = 0` produced warning on row `3`;
- save was not clicked;
- production publish was not executed;
- `kurgin-data` was not changed.

Interpretation:

```text
Clean fixture import / preview / validation path is operational.
No critical validation blocker appeared in the clean fixture.
Price missing / zero still remains warning-level.
```

### 4.2. Save behavior

Save was intentionally not clicked.

This means:

- live clean upload/preview/validation is confirmed;
- clean save path is not confirmed by this smoke;
- no local Admin data mutation is claimed by this document;
- no published data mutation occurred.

## 5. Required checks vs actual execution

| Required check | Run 1 | Run 2 | Overall result |
|---|---:|---:|---:|
| Live Admin app opened | PASS | Already confirmed | PASS |
| Controlled Excel fixture uploaded | PASS | PASS | PASS |
| `KURGIN_Template` detected | PASS | PASS | PASS |
| Header row detected | PASS: row `1` | PASS | PASS |
| Columns recognized | PASS: `10` recognized / `9` unrecognized | PASS: `15` recognized / `8` unrecognized | PASS |
| Raw preview shown | PASS | PASS | PASS |
| Normalized preview shown | PASS | PASS | PASS |
| Validation worked | PASS | PASS | PASS |
| Critical/warning separation visible | PASS | PASS | PASS |
| Critical error behavior | PASS: missing `report_number` critical | PASS: no critical errors found | PASS |
| Warning behavior | PASS: `price_rub = 0` warning | PASS: `price_rub = 0` warning on row `3` | PASS |
| Save behavior | PASS: blocked due to critical error | Not clicked | RISK / not fully tested |
| Production publish | Not executed | Not executed | RISK / not tested |
| `kurgin-data` unchanged | PASS | PASS | PASS |
| Code/UI/schema unchanged | PASS | PASS | PASS |

## 6. Production publish boundary

Production publish was not executed in either smoke run.

Explicitly not done:

- no `kurgin-data` publish;
- no `catalog.json` update;
- no `data/catalog.json` update;
- no `stones.csv` update;
- no `upload_batches.csv` update;
- no Streamlit data refresh;
- no production deploy.

This satisfies the no-publish boundary for the import smoke tests.

Publish verdict:

```text
RISK: not tested
```

Reason:

- these smoke runs were intentionally limited to Admin open + import/diagnostics/preview/validation;
- production publish was out of scope and remains blocked until a separate approved publish-smoke task.

## 7. Blockers

### 7.1. Runtime blockers

```text
None for live upload / diagnostics / preview / validation path.
```

### 7.2. Remaining limitations

| ID | Limitation | Impact | Required future action |
|---|---|---|---|
| LIM-001 | Publish was not tested | Cannot mark publish flow PASS from these smoke runs | Run separate controlled publish smoke only after explicit approval |
| LIM-002 | Clean fixture save was not clicked | Cannot mark clean save path PASS from Run 2 | Run separate clean-fixture save smoke if needed, still without publish |
| LIM-003 | Unrecognized columns were present | They must remain inactive unless mapped by contract | Do not map them without separate approval/tests |

### 7.3. No source-level code blocker found

No source-level issue was found that justifies code changes under this task.

No fix was made.

## 8. Risk items

| ID | Risk | Severity | Handling |
|---|---|---:|---|
| RISK-001 | Publish remains untested. | Medium | Run controlled publish smoke only after explicit approval. |
| RISK-002 | Admin import auto-marks MVP flags and relies on Publication Gate review. | Medium | Continue requiring preview/gate review before save/publish workflow. |
| RISK-003 | Unknown/unrecognized columns were present in both runs. | Low-medium | Keep them inactive unless explicitly mapped by a separate contract/task. |
| RISK-004 | Clean fixture save was not clicked. | Low-medium | Run a separate clean-fixture save smoke if needed, still without publish. |
| RISK-005 | Production data must remain untouched during import-only smoke. | High | Keep publish blocked unless a separate publish-smoke task is approved. |

## 9. Evidence summary

### 9.1. Run 1 evidence

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

### 9.2. Run 2 evidence

```text
clean Excel fixture uploaded
KURGIN_Template detected
header row detected
15 columns recognized
8 columns unrecognized
raw preview shown
normalized preview shown
critical errors not found
price_rub = 0 produced warning on row 3
save was not clicked
production publish was not executed
kurgin-data was not changed
```

## 10. Allowed next actions

Allowed next actions:

1. Keep this smoke result as live validation evidence for upload / diagnostics / preview / validation.
2. Run a clean-fixture save smoke, if explicitly needed, without production publish.
3. Run publish dry-run/manual download validation.
4. Run controlled publish smoke with `GITHUB_TOKEN` only after explicit approval.
5. Add or document a small smoke fixture path only if separately approved.
6. Keep unrecognized columns inactive unless a separate mapping/contract update is approved.
7. Add fixture-based automated smoke tests only through a separate approved code task.

## 11. Blocked actions

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

## 12. Acceptance checklist

This document satisfies the clean-smoke-result update task if:

- `docs/KURGIN_ADMIN_IMPORT_SMOKE_V0_1.md` is updated;
- clean Excel fixture upload is recorded;
- `KURGIN_Template` detection is recorded;
- header row detection is recorded;
- `15` recognized and `8` unrecognized columns are recorded;
- raw preview is recorded;
- normalized preview is recorded;
- no critical errors found is recorded;
- `price_rub = 0` warning on row `3` is recorded;
- save not clicked is recorded;
- production publish not executed is recorded;
- `kurgin-data` not changed is recorded;
- no code changes are made;
- no UI changes are made;
- no data/schema changes are made;
- no Analyzer/formula/scoring changes are made.

## 13. Closure

Final runtime result:

```text
PASS for clean import / preview / validation
RISK for publish because publish was not tested
```

Operational document verdict remains:

```text
RISK
```

The manual live Admin import smoke now confirms:

- blocking-critical fixture behavior;
- clean fixture import / preview / validation behavior.

Publish remains a separate untested path and must not be inferred as passed from import-only smoke tests.
