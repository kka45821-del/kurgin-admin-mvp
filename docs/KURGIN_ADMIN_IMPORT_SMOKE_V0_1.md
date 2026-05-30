# KURGIN ADMIN IMPORT SMOKE v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: manual Admin import smoke checkpoint.
Status: live import / preview / validation / save smoke completed; no production publish.

This document records manual live Admin import smoke checkpoints for Admin open, controlled Excel import/preview, validation, and save without production publish.

Repositories not changed:

- `kurgin-streamlit-mvp`
- `kurgin-data`
- `kurgin-score-analyzer`
- `kurgin-formula-service`

This checkpoint did not publish to `kurgin-data`, did not intentionally change Streamlit public catalog data, did not change Analyzer, did not change formula/scoring, did not change schema, did not perform cleanup, and did not deploy production.

## 1. Final verdict

```text
PASS for Admin import / preview / validation / save
RISK for publish because publish was not tested
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
- Main + large fixture had no critical errors.
- Warnings were only for `price_rub = 0`.
- Confirmation checkbox was selected.
- `Сохранить партию` was clicked.
- Batch `P-0004` was saved.
- `12` stones were saved.
- Production publish was not executed.
- `kurgin-data` was not intentionally changed.
- Streamlit public catalog was not intentionally changed.
- Analyzer/formula/scoring were not touched.

This confirms the Admin import / diagnostics / preview / validation / save path for the controlled main + large fixture.

The remaining risk is production publish, because publish was intentionally not tested.

## 2. Smoke run summary

| Smoke run | Purpose | Runtime result | Save status | Publish status |
|---|---|---:|---:|---:|
| Run 1 — controlled fixture with critical error | Confirm critical/warning separation and blocked save | PASS for upload / diagnostics / preview / validation | Blocked by critical error | Not executed |
| Run 2 — clean Excel fixture | Confirm clean import / preview / validation with no critical errors | PASS for clean import / preview / validation | Not clicked | Not executed |
| Run 3 — main + large Excel fixture | Confirm main/large sections import, preview and validation | PASS for main + large import / preview / validation | Not clicked | Not executed |
| Run 4 — main + large save smoke | Confirm clean main/large save without publish | PASS for Admin import / preview / validation / save | Clicked; batch `P-0004`, `12` stones saved | Not executed |

## 3. Run 1 — controlled fixture with critical error

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
Price missing / zero remained warning-level.
```

## 5. Run 3 — main + large Excel fixture

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

## 6. Run 4 — main + large save smoke, no publish

### 6.1. Result

```text
PASS for Admin import / preview / validation / save
RISK for publish because publish was not tested
```

Confirmed:

- main + large fixture had no critical errors;
- warnings were only for `price_rub = 0`;
- confirmation checkbox was selected;
- `Сохранить партию` was clicked;
- batch `P-0004` was saved;
- `12` stones were saved;
- production publish was not executed;
- `kurgin-data` was not intentionally changed;
- Streamlit public catalog was not intentionally changed;
- Analyzer/formula/scoring were not touched.

Interpretation:

```text
Admin clean main + large save path is operational for batch P-0004.
Save is confirmed, but production publish remains untested.
```

### 6.2. Save impact boundary

The save action is an Admin-side local data mutation.

Expected Admin-side impact from save:

- local Admin `data/stones.csv` receives the saved fixture rows;
- local Admin `data/upload_batches.csv` receives/updates the batch record for `P-0004`;
- local Admin `data/admin_actions.csv` may record the import action.

Not implied by this save:

- no `kurgin-data` publish;
- no public Streamlit catalog refresh from new data;
- no production deploy;
- no payment/reserve/sold behavior;
- no Analyzer/formula/scoring behavior change.

## 7. Required checks vs actual execution

| Required check | Run 1 | Run 2 | Run 3 | Run 4 | Overall result |
|---|---:|---:|---:|---:|---:|
| Live Admin app opened | PASS | Already confirmed | Already confirmed | Already confirmed | PASS |
| Controlled Excel fixture uploaded | PASS | PASS | PASS | PASS | PASS |
| `KURGIN_Template` detected | PASS | PASS | PASS | PASS | PASS |
| Header row detected | PASS: row `1` | PASS | PASS | PASS | PASS |
| Columns recognized | PASS: `10` / `9` | PASS: `15` / `8` | PASS: `15` / `0` | Existing main/large fixture used | PASS |
| Raw preview shown | PASS | PASS | PASS | PASS | PASS |
| Normalized preview shown | PASS | PASS | PASS | PASS | PASS |
| Main rows present | Not targeted | Not targeted | PASS | PASS | PASS |
| Large rows present | Not targeted | Not targeted | PASS | PASS | PASS |
| Validation worked | PASS | PASS | PASS | PASS | PASS |
| Critical errors | PASS: missing `report_number` critical | PASS: none in clean fixture | PASS: none in main/large | PASS: none in saved main/large | PASS |
| Warning behavior | PASS | PASS: row `3` | PASS: rows `3`, `6`, `9`, `11`, `13` | PASS: warnings only for `price_rub = 0` | PASS |
| Save behavior | PASS: blocked due to critical error | Not clicked | Not clicked | PASS: batch `P-0004`, `12` stones saved | PASS for Admin save |
| Production publish | Not executed | Not executed | Not executed | Not executed | RISK / not tested |
| `kurgin-data` changed | No | No | No | Not intentionally changed | PASS |
| Code/UI/schema changed | No | No | No | No | PASS |

## 8. Production publish boundary

Production publish was not executed in any smoke run.

Explicitly not done:

- no intentional `kurgin-data` publish;
- no intentional `catalog.json` update;
- no intentional `data/catalog.json` update;
- no intentional public `stones.csv` update;
- no intentional public `upload_batches.csv` update;
- no intentional Streamlit public catalog refresh;
- no production deploy.

Publish verdict:

```text
RISK: not tested
```

Reason:

- smoke runs have now confirmed upload, preview, validation and Admin-side save;
- production publish remains a separate flow and must not be inferred as passed.

## 9. Save boundary

Save behavior status:

```text
PASS for Admin-side save
```

Confirmed:

- clean main + large fixture had no critical errors;
- confirmation checkbox was selected;
- save button was clicked;
- batch `P-0004` saved successfully;
- `12` stones saved.

Remaining limitation:

```text
Save result is not a publish result.
```

Admin-side save does not equal public catalog publication.

## 10. Blockers

Runtime blockers for import / preview / validation / Admin-side save path:

```text
None observed.
```

Remaining limitations:

| ID | Limitation | Impact | Required future action |
|---|---|---|---|
| LIM-001 | Publish was not tested | Cannot mark publish flow PASS | Run separate controlled publish smoke only after explicit approval |
| LIM-002 | Public Streamlit refresh after Admin save was not tested | Cannot mark public data update PASS | Requires publish first, then Streamlit smoke |
| LIM-003 | `kurgin-data` was not intentionally changed | Correct for this task, but full flow remains incomplete | Keep full Admin -> Data -> Streamlit flow at RISK until publish smoke |

No source-level code blocker was found.

No fix was made.

## 11. Risk items

| ID | Risk | Severity | Handling |
|---|---|---:|---|
| RISK-001 | Publish remains untested. | Medium | Run controlled publish smoke only after explicit approval. |
| RISK-002 | Admin-side saved smoke rows must not be mistaken for published public data. | Medium | Keep save/publish distinction explicit. |
| RISK-003 | Admin import auto-marks MVP flags and relies on Publication Gate review. | Medium | Continue requiring preview/gate review before publish workflow. |
| RISK-004 | Public catalog still depends on separate `kurgin-data` publish. | Medium | Re-run Streamlit catalog smoke after any approved publish. |
| RISK-005 | Smoke rows must remain traceable for rollback/audit. | Medium | Keep batch `P-0004` and fixture IDs identifiable. |

## 12. Evidence summary

### 12.1. Run 1 evidence

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

### 12.2. Run 2 evidence

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

### 12.3. Run 3 evidence

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

### 12.4. Run 4 evidence

```text
main + large fixture had no critical errors
warnings only for price_rub = 0
checkbox confirmed
Save batch clicked
batch P-0004 saved
12 stones saved
production publish was NOT executed
kurgin-data was NOT intentionally changed
Streamlit public catalog was NOT intentionally changed
Analyzer/formula/scoring were not touched
```

## 13. Allowed next actions

Allowed next actions:

1. Keep this smoke result as live validation evidence for upload / diagnostics / preview / validation / Admin save.
2. Verify local Admin saved batch `P-0004` if needed.
3. Run publish dry-run/manual download validation.
4. Run controlled publish smoke with `GITHUB_TOKEN` only after explicit approval.
5. Run Streamlit current-catalog smoke again after any approved publish.
6. Keep save/publish separation explicit in future docs and tasks.
7. Keep smoke rows/batch traceable for rollback/audit.

## 14. Blocked actions

Blocked by this smoke update task:

- publish to `kurgin-data`;
- intentional update of public `catalog.json`;
- intentional update of public `data/catalog.json`;
- intentional update of public `stones.csv`;
- intentional update of public `upload_batches.csv`;
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

## 15. Acceptance checklist

This document satisfies the save-smoke-result update task if:

- `docs/KURGIN_ADMIN_IMPORT_SMOKE_V0_1.md` is updated;
- main + large fixture no-critical status is recorded;
- warnings-only-for-price-zero status is recorded;
- checkbox confirmation is recorded;
- save click is recorded;
- batch `P-0004` saved is recorded;
- `12` stones saved is recorded;
- production publish not executed is recorded;
- `kurgin-data` not intentionally changed is recorded;
- Streamlit public catalog not intentionally changed is recorded;
- Analyzer/formula/scoring not touched is recorded;
- no code changes are made;
- no UI changes are made;
- no schema changes are made.

## 16. Closure

Final runtime result:

```text
PASS for Admin import / preview / validation / save
RISK for publish because publish was not tested
```

Operational document verdict remains:

```text
RISK
```

The manual live Admin import smoke now confirms:

- blocking-critical fixture behavior;
- clean fixture import / preview / validation behavior;
- main + large fixture import / preview / validation behavior with zero unrecognized columns;
- Admin-side save behavior for batch `P-0004` with `12` stones saved.

Production publish remains a separate untested path and must not be inferred as passed from Admin-side save.
