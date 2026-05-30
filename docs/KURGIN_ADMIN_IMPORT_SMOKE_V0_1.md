# KURGIN ADMIN IMPORT SMOKE v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: manual Admin import smoke checkpoint.
Status: live import smoke completed / clean fixture smoke completed / main-large fixture smoke completed / no save / no production publish.

This document records manual live Admin import smoke checkpoints for Admin open + controlled Excel import/preview without save or production publish.

Repositories not changed:

- `kurgin-streamlit-mvp`
- `kurgin-data`
- `kurgin-score-analyzer`
- `kurgin-formula-service`

This checkpoint did not save batch data, did not publish to `kurgin-data`, did not change Streamlit, did not change Analyzer, did not change formula/scoring, did not change data schema, did not perform cleanup, and did not deploy production.

## 1. Final verdict

```text
PASS for main + large import / preview / validation
RISK for save/publish because they were not tested
```

Operational verdict:

```text
RISK
```

Interpretation:

- Live Admin app opened.
- Controlled smoke Excel upload path worked.
- Clean Excel fixture import / preview / validation worked.
- Main + large Excel fixture import / preview / validation worked.
- `KURGIN_Template` was detected in all recorded runtime runs.
- Header row detection worked.
- Column recognition worked, including a main + large fixture with `15` recognized and `0` unrecognized columns.
- Raw preview and normalized preview were shown.
- Validation worked.
- Main rows and large rows were present in preview.
- Main + large fixture produced no critical errors.
- `price_rub = 0` produced warnings on rows `3`, `6`, `9`, `11`, `13`.
- Save was not clicked.
- Production publish was not executed.
- `kurgin-data` was not changed.

This confirms the live Admin import / diagnostics / preview / validation path for:

- a blocking-critical fixture;
- a clean fixture;
- a main + large fixture.

The remaining risk is save/publish, because they were intentionally not tested.

## 2. Smoke run summary

| Smoke run | Purpose | Runtime result | Save status | Publish status |
|---|---|---:|---:|---:|
| Run 1 — controlled fixture with critical error | Confirm critical/warning separation and blocked save | PASS for upload / diagnostics / preview / validation | Blocked by critical error | Not executed |
| Run 2 — clean Excel fixture | Confirm clean import / preview / validation with no critical errors | PASS for clean import / preview / validation | Not clicked | Not executed |
| Run 3 — main + large Excel fixture | Confirm main/large sections import, preview and validation | PASS for main + large import / preview / validation | Not clicked | Not executed |

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

## 5. Run 3 — main + large Excel fixture

### 5.1. Result

```text
PASS for main + large import / preview / validation
RISK for save/publish because they were not tested
```

Confirmed:

- main + large Excel fixture uploaded;
- `KURGIN_Template` detected;
- header row detected;
- `15` columns recognized;
- `0` columns unrecognized;
- raw preview shown;
- normalized preview shown;
- main rows present;
- large rows present;
- critical errors not found;
- `price_rub = 0` produced warnings on rows `3`, `6`, `9`, `11`, `13`;
- save was not clicked;
- production publish was not executed;
- `kurgin-data` was not changed.

Interpretation:

```text
Main + large fixture import / preview / validation path is operational.
No critical validation blocker appeared in the main + large fixture.
Zero unrecognized columns indicates the fixture matches the recognized Admin import contract for this smoke.
Price missing / zero remains warning-level on the listed rows.
```

### 5.2. Main / large coverage

The fixture confirmed that both section types were present in preview:

- main rows present;
- large rows present.

This is important because main and large rows are the current controlled public MVP catalog sections where Round KURGIN Score requirements and price-warning behavior matter.

### 5.3. Save behavior

Save was intentionally not clicked.

This means:

- live main + large upload/preview/validation is confirmed;
- save path is not confirmed by this run;
- no local Admin data mutation is claimed by this document;
- no published data mutation occurred.

## 6. Required checks vs actual execution

| Required check | Run 1 | Run 2 | Run 3 | Overall result |
|---|---:|---:|---:|---:|
| Live Admin app opened | PASS | Already confirmed | Already confirmed | PASS |
| Controlled Excel fixture uploaded | PASS | PASS | PASS | PASS |
| `KURGIN_Template` detected | PASS | PASS | PASS | PASS |
| Header row detected | PASS: row `1` | PASS | PASS | PASS |
| Columns recognized | PASS: `10` recognized / `9` unrecognized | PASS: `15` recognized / `8` unrecognized | PASS: `15` recognized / `0` unrecognized | PASS |
| Raw preview shown | PASS | PASS | PASS | PASS |
| Normalized preview shown | PASS | PASS | PASS | PASS |
| Main rows present | Not targeted | Not targeted | PASS | PASS for Run 3 |
| Large rows present | Not targeted | Not targeted | PASS | PASS for Run 3 |
| Validation worked | PASS | PASS | PASS | PASS |
| Critical/warning separation visible | PASS | PASS | PASS | PASS |
| Critical error behavior | PASS: missing `report_number` critical | PASS: no critical errors found | PASS: no critical errors found | PASS |
| Warning behavior | PASS: `price_rub = 0` warning | PASS: `price_rub = 0` warning on row `3` | PASS: `price_rub = 0` warnings on rows `3`, `6`, `9`, `11`, `13` | PASS |
| Save behavior | PASS: blocked due to critical error | Not clicked | Not clicked | RISK / not fully tested |
| Production publish | Not executed | Not executed | Not executed | RISK / not tested |
| `kurgin-data` unchanged | PASS | PASS | PASS | PASS |
| Code/UI/schema unchanged | PASS | PASS | PASS | PASS |

## 7. Production publish boundary

Production publish was not executed in any smoke run.

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

## 8. Save boundary

Save was not clicked in Run 2 or Run 3.

Save behavior status:

```text
RISK: not fully tested
```

Reason:

- Run 1 confirmed save blocking when a critical error exists;
- Run 2 and Run 3 confirmed clean validation but did not execute save;
- therefore clean save path is still unconfirmed.

Save should only be tested under a separate approved clean save smoke with rollback plan and no production publish.

## 9. Blockers

### 9.1. Runtime blockers

```text
None for live upload / diagnostics / preview / validation path.
```

### 9.2. Remaining limitations

| ID | Limitation | Impact | Required future action |
|---|---|---|---|
| LIM-001 | Publish was not tested | Cannot mark publish flow PASS from these smoke runs | Run separate controlled publish smoke only after explicit approval |
| LIM-002 | Clean fixture save was not clicked | Cannot mark clean save path PASS from Run 2 or Run 3 | Run separate clean-fixture save smoke if needed, still without publish |
| LIM-003 | Run 1 and Run 2 had unrecognized columns | They must remain inactive unless mapped by contract | Do not map them without separate approval/tests |
| LIM-004 | Run 3 had zero unrecognized columns but still did not test save | Import contract alignment does not imply save/publish readiness | Keep save/publish as separate smoke tasks |

### 9.3. No source-level code blocker found

No source-level issue was found that justifies code changes under this task.

No fix was made.

## 10. Risk items

| ID | Risk | Severity | Handling |
|---|---|---:|---|
| RISK-001 | Publish remains untested. | Medium | Run controlled publish smoke only after explicit approval. |
| RISK-002 | Clean save path remains untested. | Medium | Run separate clean save smoke only with rollback plan and no publish. |
| RISK-003 | Admin import auto-marks MVP flags and relies on Publication Gate review. | Medium | Continue requiring preview/gate review before save/publish workflow. |
| RISK-004 | Unknown/unrecognized columns were present in Run 1 and Run 2. | Low-medium | Keep them inactive unless explicitly mapped by a separate contract/task. |
| RISK-005 | Production data must remain untouched during import-only smoke. | High | Keep publish blocked unless a separate publish-smoke task is approved. |

## 11. Evidence summary

### 11.1. Run 1 evidence

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

### 11.2. Run 2 evidence

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

### 11.3. Run 3 evidence

```text
main + large Excel fixture uploaded
KURGIN_Template detected
header row detected
15 columns recognized
0 columns unrecognized
raw preview shown
normalized preview shown
main rows present
large rows present
critical errors not found
price_rub = 0 produced warnings on rows 3, 6, 9, 11, 13
save was not clicked
production publish was not executed
kurgin-data was not changed
```

## 12. Allowed next actions

Allowed next actions:

1. Keep this smoke result as live validation evidence for upload / diagnostics / preview / validation.
2. Run a clean-fixture save smoke, if explicitly needed, only after confirming rollback plan and still without production publish.
3. Run publish dry-run/manual download validation.
4. Run controlled publish smoke with `GITHUB_TOKEN` only after explicit approval.
5. Add or document a small smoke fixture path only if separately approved.
6. Keep unrecognized columns inactive unless a separate mapping/contract update is approved.
7. Add fixture-based automated smoke tests only through a separate approved code task.
8. Use the main + large fixture as the current best manual fixture pattern for import validation because it produced zero unrecognized columns.

## 13. Blocked actions

Blocked by this smoke task:

- save batch now;
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

## 14. Acceptance checklist

This document satisfies the main-large smoke-result update task if:

- `docs/KURGIN_ADMIN_IMPORT_SMOKE_V0_1.md` is updated;
- main + large Excel fixture upload is recorded;
- `KURGIN_Template` detection is recorded;
- header row detection is recorded;
- `15` recognized and `0` unrecognized columns are recorded;
- raw preview is recorded;
- normalized preview is recorded;
- main rows present is recorded;
- large rows present is recorded;
- no critical errors found is recorded;
- `price_rub = 0` warnings on rows `3`, `6`, `9`, `11`, `13` are recorded;
- save not clicked is recorded;
- production publish not executed is recorded;
- `kurgin-data` not changed is recorded;
- no code changes are made;
- no UI changes are made;
- no data/schema changes are made;
- no Analyzer/formula/scoring changes are made.

## 15. Closure

Final runtime result:

```text
PASS for main + large import / preview / validation
RISK for save/publish because they were not tested
```

Operational document verdict remains:

```text
RISK
```

The manual live Admin import smoke now confirms:

- blocking-critical fixture behavior;
- clean fixture import / preview / validation behavior;
- main + large fixture import / preview / validation behavior with zero unrecognized columns.

Save and publish remain separate untested paths and must not be inferred as passed from import-only smoke tests.
