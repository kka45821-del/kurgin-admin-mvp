# KURGIN ADMIN IMPORT SMOKE v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: manual Admin import smoke checkpoint.
Status: live import / preview / validation / save / Admin catalog visibility smoke completed; no production publish.

This document records manual live Admin import smoke checkpoints for Admin open, controlled Excel import/preview, validation, save, and Admin catalog visibility without production publish.

Repositories not changed:

- `kurgin-streamlit-mvp`
- `kurgin-data`
- `kurgin-score-analyzer`
- `kurgin-formula-service`

This checkpoint did not publish to `kurgin-data`, did not intentionally change Streamlit public catalog data, did not change Analyzer, did not change formula/scoring, did not change schema, did not perform cleanup, and did not deploy production.

## 1. Final verdict

```text
PASS for Admin import / preview / validation / save / Admin catalog visibility
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
- Saved `KRG-ML-*` rows are visible in Admin catalog.
- Old catalog rows did not disappear.
- Batch save is confirmed.
- `Save catalog` was not clicked.
- Production publish was not executed.
- `kurgin-data` was not intentionally changed.
- Streamlit public catalog was not intentionally updated from this save.
- Analyzer/formula/scoring were not touched.

This confirms the Admin import / diagnostics / preview / validation / save / Admin catalog visibility path for the controlled main + large fixture.

The remaining risk is production publish, because publish was intentionally not tested.

## 2. Smoke run summary

| Smoke run | Purpose | Runtime result | Save status | Publish status |
|---|---|---:|---:|---:|
| Run 1 — controlled fixture with critical error | Confirm critical/warning separation and blocked save | PASS for upload / diagnostics / preview / validation | Blocked by critical error | Not executed |
| Run 2 — clean Excel fixture | Confirm clean import / preview / validation with no critical errors | PASS for clean import / preview / validation | Not clicked | Not executed |
| Run 3 — main + large Excel fixture | Confirm main/large sections import, preview and validation | PASS for main + large import / preview / validation | Not clicked | Not executed |
| Run 4 — main + large save smoke | Confirm clean main/large save without publish | PASS for Admin import / preview / validation / save | Clicked; batch `P-0004`, `12` stones saved | Not executed |
| Run 5 — Admin catalog visibility smoke | Confirm saved smoke rows are visible and old rows remain | PASS for Admin catalog visibility | No additional save | Not executed |

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

## 7. Run 5 — Admin catalog visibility smoke

### 7.1. Result

```text
PASS for Admin catalog visibility after save
RISK for publish because publish was not tested
```

Confirmed:

- saved `KRG-ML-*` rows are visible in Admin catalog;
- old catalog rows did not disappear;
- batch save is confirmed;
- production publish was not executed;
- `kurgin-data` was not changed intentionally;
- public Streamlit was not updated from this save;
- `Save catalog` was not clicked;
- `Publish` was not clicked.

Interpretation:

```text
Admin-side saved rows are visible in the Admin catalog.
The save did not replace or remove the old Admin catalog rows.
Admin catalog visibility is confirmed, but public publication remains untested.
```

### 7.2. Public boundary

Admin catalog visibility does not equal public catalog publication.

The following remain true:

- Admin local catalog contains saved smoke rows;
- public `kurgin-data` was not intentionally changed;
- public Streamlit was not updated from this save;
- production publish remains untested.

## 8. Required checks vs actual execution

| Required check | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Overall result |
|---|---:|---:|---:|---:|---:|---:|
| Live Admin app opened | PASS | Already confirmed | Already confirmed | Already confirmed | Already confirmed | PASS |
| Controlled Excel fixture uploaded | PASS | PASS | PASS | PASS | Already saved | PASS |
| `KURGIN_Template` detected | PASS | PASS | PASS | PASS | Not applicable | PASS |
| Header row detected | PASS: row `1` | PASS | PASS | PASS | Not applicable | PASS |
| Columns recognized | PASS: `10` / `9` | PASS: `15` / `8` | PASS: `15` / `0` | Existing main/large fixture used | Not applicable | PASS |
| Raw preview shown | PASS | PASS | PASS | PASS | Not applicable | PASS |
| Normalized preview shown | PASS | PASS | PASS | PASS | Not applicable | PASS |
| Main rows present | Not targeted | Not targeted | PASS | PASS | PASS | PASS |
| Large rows present | Not targeted | Not targeted | PASS | PASS | PASS | PASS |
| Validation worked | PASS | PASS | PASS | PASS | Not applicable | PASS |
| Critical errors | PASS: missing `report_number` critical | PASS: none in clean fixture | PASS: none in main/large | PASS: none in saved main/large | Not applicable | PASS |
| Warning behavior | PASS | PASS: row `3` | PASS: rows `3`, `6`, `9`, `11`, `13` | PASS: warnings only for `price_rub = 0` | Not applicable | PASS |
| Save behavior | PASS: blocked due to critical error | Not clicked | Not clicked | PASS: batch `P-0004`, `12` stones saved | Confirmed visible | PASS for Admin save/visibility |
| Old Admin rows retained | Not targeted | Not targeted | Not targeted | Not targeted | PASS | PASS |
| Production publish | Not executed | Not executed | Not executed | Not executed | Not executed | RISK / not tested |
| `kurgin-data` changed | No | No | No | Not intentionally changed | Not intentionally changed | PASS |
| Public Streamlit updated | No | No | No | Not intentionally changed | Not intentionally updated from save | PASS |
| Code/UI/schema changed | No | No | No | No | No | PASS |

## 9. Production publish boundary

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

- smoke runs have now confirmed upload, preview, validation, Admin-side save and Admin catalog visibility;
- production publish remains a separate flow and must not be inferred as passed.

## 10. Save / catalog visibility boundary

Save behavior status:

```text
PASS for Admin-side save and Admin catalog visibility
```

Confirmed:

- clean main + large fixture had no critical errors;
- confirmation checkbox was selected;
- save button was clicked;
- batch `P-0004` saved successfully;
- `12` stones saved;
- saved `KRG-ML-*` rows are visible in Admin catalog;
- old catalog rows did not disappear.

Remaining limitation:

```text
Save result is not a publish result.
```

Admin-side save and Admin catalog visibility do not equal public catalog publication.

## 11. Blockers

Runtime blockers for import / preview / validation / Admin-side save / Admin catalog visibility path:

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

## 12. Risk items

| ID | Risk | Severity | Handling |
|---|---|---:|---|
| RISK-001 | Publish remains untested. | Medium | Run controlled publish smoke only after explicit approval. |
| RISK-002 | Admin-side saved smoke rows must not be mistaken for published public data. | Medium | Keep save/publish distinction explicit. |
| RISK-003 | Admin import auto-marks MVP flags and relies on Publication Gate review. | Medium | Continue requiring preview/gate review before publish workflow. |
| RISK-004 | Public catalog still depends on separate `kurgin-data` publish. | Medium | Re-run Streamlit catalog smoke after any approved publish. |
| RISK-005 | Smoke rows must remain traceable for rollback/audit. | Medium | Keep batch `P-0004` and `KRG-ML-*` fixture IDs identifiable. |

## 13. Evidence summary

### 13.1. Run 1 evidence

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

### 13.2. Run 2 evidence

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

### 13.3. Run 3 evidence

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

### 13.4. Run 4 evidence

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

### 13.5. Run 5 evidence

```text
saved KRG-ML-* rows are visible in Admin catalog
old catalog rows did not disappear
batch save is confirmed
publish was not executed
kurgin-data was not changed intentionally
public Streamlit was not updated from this save
Save catalog / Publish were not clicked
```

## 14. Allowed next actions

Allowed next actions:

1. Keep this smoke result as live validation evidence for upload / diagnostics / preview / validation / Admin save / Admin catalog visibility.
2. Verify local Admin saved batch `P-0004` if needed.
3. Run publish dry-run/manual download validation.
4. Run controlled publish smoke with `GITHUB_TOKEN` only after explicit approval.
5. Run Streamlit current-catalog smoke again after any approved publish.
6. Keep save/publish separation explicit in future docs and tasks.
7. Keep smoke rows/batch traceable for rollback/audit.
8. Do not infer public catalog update from Admin catalog visibility.

## 15. Blocked actions

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

## 16. Acceptance checklist

This document satisfies the save-visibility-smoke-result update task if:

- `docs/KURGIN_ADMIN_IMPORT_SMOKE_V0_1.md` is updated;
- saved `KRG-ML-*` rows visible in Admin catalog is recorded;
- old catalog rows did not disappear is recorded;
- batch save confirmed is recorded;
- production publish not executed is recorded;
- `kurgin-data` not intentionally changed is recorded;
- public Streamlit not updated from save is recorded;
- `Save catalog` not clicked is recorded;
- `Publish` not clicked is recorded;
- no code changes are made;
- no UI changes are made;
- no schema changes are made;
- no Analyzer/formula/scoring changes are made.

## 17. Closure

Final runtime result:

```text
PASS for Admin import / preview / validation / save / Admin catalog visibility
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
- Admin-side save behavior for batch `P-0004` with `12` stones saved;
- Admin catalog visibility for saved `KRG-ML-*` rows while old catalog rows remained present.

Production publish remains a separate untested path and must not be inferred as passed from Admin-side save or Admin catalog visibility.
