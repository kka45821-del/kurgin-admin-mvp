# KURGIN ADMIN IMPORT SMOKE v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: manual Admin import smoke checkpoint.
Status: live import / preview / validation / save smoke completed; no production publish.

This document records manual live Admin import smoke checkpoints for Admin open, controlled Excel import/preview, validation, Admin-side save, and Admin catalog visibility without production publish.

Repositories not changed:

- `kurgin-streamlit-mvp`
- `kurgin-data`
- `kurgin-score-analyzer`
- `kurgin-formula-service`

This update does not change code, UI, schema, `kurgin-data`, Streamlit, Analyzer, formula/scoring, or production deployment.

## 1. Final verdict

```text
PASS for rich fixture import / preview / validation / save
RISK because publish was not tested and smoke rows are now saved in Admin
```

Operational verdict:

```text
RISK
```

Interpretation:

- Admin import / preview / validation / save path is working for controlled smoke fixtures.
- Rich fixture was uploaded and saved.
- Batch `P-0004` now has the latest rich smoke-save scope with `32` saved stones.
- Production publish was not executed.
- `kurgin-data` was not intentionally changed.
- Public Streamlit was not intentionally updated from this save.
- Analyzer/formula/scoring were not touched.

Critical boundary:

```text
Admin save ≠ public publish
KRG-RICH-* must not be published to kurgin-data
```

The saved smoke rows must not be published to `kurgin-data` unless a separate approved publish-smoke task explicitly authorizes it.

## 2. Smoke run summary

| Smoke run | Purpose | Runtime result | Save status | Publish status |
|---|---|---:|---:|---:|
| Run 1 — controlled fixture with critical error | Confirm critical/warning separation and blocked save | PASS for upload / diagnostics / preview / validation | Blocked by critical error | Not executed |
| Run 2 — clean Excel fixture | Confirm clean import / preview / validation with no critical errors | PASS for clean import / preview / validation | Not clicked | Not executed |
| Run 3 — main + large Excel fixture | Confirm main/large sections import, preview and validation | PASS for main + large import / preview / validation | Not clicked | Not executed |
| Run 4 — main + large save smoke | Confirm clean main/large save without publish | PASS for Admin import / preview / validation / save | Clicked; batch `P-0004`, `12` stones saved | Not executed |
| Run 5 — Admin catalog visibility smoke | Confirm saved smoke rows are visible and old rows remain | PASS for Admin catalog visibility | No additional save | Not executed |
| Run 6 — rich fixture save smoke | Confirm rich fixture import / preview / validation / save | PASS for rich fixture import / preview / validation / save | Clicked; batch `P-0004`, `32` stones saved | Not executed |

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

## 6. Run 4 — main + large save smoke, no publish

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

## 7. Run 5 — Admin catalog visibility smoke

Confirmed:

- saved `KRG-ML-*` rows were visible in Admin catalog;
- old catalog rows did not disappear;
- batch save was confirmed;
- production publish was not executed;
- `kurgin-data` was not changed intentionally;
- public Streamlit was not updated from this save;
- `Save catalog` was not clicked;
- `Publish` was not clicked.

Boundary:

```text
Admin catalog visibility ≠ public catalog publication
```

## 8. Run 6 — rich fixture save smoke, no publish

### 8.1. Result

```text
PASS for rich fixture import / preview / validation / save
RISK because publish was not tested and smoke rows are now saved in Admin
```

Confirmed:

- rich fixture uploaded;
- `KURGIN_Template` selected;
- critical errors not found;
- warnings appeared for `price_rub = 0` and missing `karo_score` on some non-main/non-large rows;
- `Save batch` clicked;
- batch `P-0004` saved;
- `32` stones saved;
- production publish was not executed;
- `kurgin-data` was not intentionally changed;
- public Streamlit was not intentionally changed;
- Analyzer/formula/scoring were not touched.

Interpretation:

```text
Rich fixture import / preview / validation / Admin-side save path is operational.
Batch P-0004 now has a richer smoke-save scope and must be treated as smoke-only before any publish.
```

### 8.2. Warning boundary

Warnings observed:

- `price_rub = 0`;
- `karo_score` missing on some non-main/non-large rows.

Warnings did not block the rich fixture save. Warnings must not be treated as public-ready approval.

### 8.3. Public publish boundary

```text
KRG-RICH-* must not be published to kurgin-data
Admin save ≠ public publish
```

The saved rich smoke rows are Admin-side smoke data only until a separate approved publish-smoke task explicitly permits publication.

## 9. Required checks vs actual execution

| Required check | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Run 6 | Overall result |
|---|---:|---:|---:|---:|---:|---:|---:|
| Live Admin app opened | PASS | Already confirmed | Already confirmed | Already confirmed | Already confirmed | Already confirmed | PASS |
| Controlled Excel fixture uploaded | PASS | PASS | PASS | PASS | Already saved | PASS | PASS |
| `KURGIN_Template` detected/selected | PASS | PASS | PASS | PASS | Not applicable | PASS | PASS |
| Raw/normalized preview shown | PASS | PASS | PASS | PASS | Not applicable | PASS | PASS |
| Validation worked | PASS | PASS | PASS | PASS | Not applicable | PASS | PASS |
| Critical errors | PASS: expected critical | PASS: none | PASS: none | PASS: none | Not applicable | PASS: none | PASS |
| Warning behavior | PASS | PASS | PASS | PASS | Not applicable | PASS: expected warnings only | PASS |
| Save behavior | Blocked by critical error | Not clicked | Not clicked | PASS: 12 saved | Confirmed visible | PASS: 32 saved | PASS for Admin save |
| Admin catalog visibility | Not targeted | Not targeted | Not targeted | Not targeted | PASS | Not separately checked after Run 6 | PASS for previous saved rows |
| Production publish | Not executed | Not executed | Not executed | Not executed | Not executed | Not executed | RISK / not tested |
| `kurgin-data` changed | No | No | No | Not intentionally changed | Not intentionally changed | Not intentionally changed | PASS |
| Public Streamlit updated | No | No | No | Not intentionally changed | Not intentionally updated from save | Not intentionally changed | PASS |
| Code/UI/schema changed | No | No | No | No | No | No | PASS |

## 10. Production publish boundary

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

Production publish remains a separate flow and must not be inferred as passed from Admin-side save.

## 11. Save boundary

Save behavior status:

```text
PASS for Admin-side save
```

Confirmed:

- Run 4 saved batch `P-0004` with `12` stones;
- Run 6 saved batch `P-0004` with `32` stones;
- confirmation and save controls worked;
- warnings did not block save where no critical errors existed.

Remaining limitation:

```text
Save result is not a publish result.
```

Admin-side save does not equal public catalog publication.

## 12. Blockers

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
| LIM-004 | Rich smoke rows are now saved in Admin | They must not be published accidentally | Roll back or isolate smoke rows before any publish |

No source-level code blocker was found.

No fix was made.

## 13. Risk items

| ID | Risk | Severity | Handling |
|---|---|---:|---|
| RISK-001 | Publish remains untested. | Medium | Run controlled publish smoke only after explicit approval. |
| RISK-002 | Admin-side saved smoke rows could be mistaken for publish-ready public data. | High | Roll back or isolate `KRG-RICH-*` before any publish. |
| RISK-003 | Admin import auto-marks MVP flags and relies on Publication Gate review. | Medium | Continue requiring preview/gate review before publish workflow. |
| RISK-004 | Public catalog still depends on separate `kurgin-data` publish. | Medium | Re-run Streamlit catalog smoke after any approved publish. |
| RISK-005 | Smoke rows must remain traceable for rollback/audit. | Medium | Keep batch `P-0004`, `KRG-ML-*`, and `KRG-RICH-*` fixture IDs identifiable. |

## 14. Evidence summary

### 14.1. Run 1 evidence

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

### 14.2. Run 2 evidence

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

### 14.3. Run 3 evidence

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

### 14.4. Run 4 evidence

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

### 14.5. Run 5 evidence

```text
saved KRG-ML-* rows are visible in Admin catalog
old catalog rows did not disappear
batch save is confirmed
publish was not executed
kurgin-data was not changed intentionally
public Streamlit was not updated from this save
Save catalog / Publish were not clicked
```

### 14.6. Run 6 evidence

```text
rich fixture uploaded
KURGIN_Template selected
critical errors not found
warnings for price_rub = 0 and karo_score missing on some non-main/non-large rows
Save batch clicked
batch P-0004 saved
32 stones saved
publish was not executed
kurgin-data was not intentionally changed
```

## 15. Allowed next actions

Allowed next actions:

1. Keep this smoke result as live validation evidence for upload / diagnostics / preview / validation / Admin save.
2. Update rollback scope for batch `P-0004` to include both `KRG-ML-*` and `KRG-RICH-*` rows.
3. Roll back or isolate smoke rows before any publish.
4. Run publish dry-run/manual download validation only after smoke rows are removed or isolated.
5. Run controlled publish smoke with `GITHUB_TOKEN` only after explicit approval.
6. Run Streamlit current-catalog smoke again after any approved publish.
7. Keep save/publish separation explicit in future docs and tasks.

## 16. Blocked actions

Blocked by this smoke update task:

- publish to `kurgin-data`;
- publishing `KRG-RICH-*` rows;
- publishing `KRG-ML-*` rows unless separately approved;
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
- rollback execution;
- cleanup deletion/move;
- file deletion;
- file moving.

## 17. Acceptance checklist

This document satisfies the rich-smoke-save-result update task if:

- `docs/KURGIN_ADMIN_IMPORT_SMOKE_V0_1.md` is updated;
- Run 6 is recorded;
- rich fixture upload is recorded;
- `KURGIN_Template` selected is recorded;
- no critical errors is recorded;
- warnings for `price_rub = 0` and missing `karo_score` on some non-main/non-large rows are recorded;
- save click is recorded;
- batch `P-0004` saved is recorded;
- `32` stones saved is recorded;
- production publish not executed is recorded;
- `kurgin-data` not intentionally changed is recorded;
- Admin save ≠ public publish is recorded;
- `KRG-RICH-*` must not be published is recorded;
- no code changes are made;
- no UI changes are made;
- no schema changes are made;
- no rollback is performed;
- no publish is performed.

## 18. Closure

Final runtime result:

```text
PASS for rich fixture import / preview / validation / save
RISK because publish was not tested and smoke rows are now saved in Admin
```

Operational document verdict remains:

```text
RISK
```

The manual live Admin import smoke now confirms:

- blocking-critical fixture behavior;
- clean fixture import / preview / validation behavior;
- main + large fixture import / preview / validation behavior with zero unrecognized columns;
- Admin-side save behavior for batch `P-0004`;
- rich fixture Admin-side save with `32` stones.

Production publish remains a separate untested path and must not be inferred as passed from Admin-side save.

Smoke rows, especially `KRG-RICH-*`, must be rolled back or isolated before any publish.
