# KURGIN ADMIN IMPORT SMOKE v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: manual Admin import smoke checkpoint.
Status: blocked manual runtime smoke / no implementation approval.

This document records the attempted Admin import smoke checkpoint for live Admin open + controlled Excel import/preview without production publish.

Repositories not changed:

- `kurgin-streamlit-mvp`
- `kurgin-data`
- `kurgin-score-analyzer`
- `kurgin-formula-service`

This checkpoint does not publish to `kurgin-data`, does not change Streamlit, does not change Analyzer, does not change formula/scoring, does not change data schema, does not perform cleanup, and does not deploy production.

## 1. Final verdict

```text
BLOCKED
```

Reason:

- Live Admin app URL was not available in this task context.
- Admin credentials / login session were not available in this task context.
- An interactive browser upload session could not be completed from this checkpoint.
- A controlled Excel fixture was not uploaded through the live Admin UI.
- Production publish was intentionally not executed.

This is not a source-level code blocker.

It is a runtime/manual-smoke blocker:

```text
manual smoke requires live URL + credentials/session + controlled fixture + explicit operator action
```

## 2. Required task vs actual execution

| Required check | Execution status | Result |
|---|---|---|
| Open live Admin app | Not executed | BLOCKED |
| Use small controlled Excel fixture/template | Not executed in live UI | BLOCKED |
| Upload through Admin upload | Not executed | BLOCKED |
| Confirm file accepted | Not confirmed | BLOCKED |
| Confirm sheet diagnostics works | Source-level available, runtime not confirmed | RISK |
| Confirm columns recognized | Source-level available, runtime not confirmed | RISK |
| Confirm validation/preview works | Source-level available, runtime not confirmed | RISK |
| Confirm critical/warning separation visible | Source-level available, runtime not confirmed | RISK |
| Avoid production publish | Confirmed by task behavior | PASS |
| Avoid code/UI/data/CI changes | Confirmed by task behavior | PASS |

## 3. Source-level precheck

Although the live smoke could not be completed, the Admin source still contains the expected import and preview components.

### 3.1. Admin app entry

Source-level status:

```text
AVAILABLE
```

Observed source-level behavior:

- `app.py` is the Streamlit Admin entrypoint.
- It sets page config for `KURGIN Admin MVP`.
- It imports Admin modules for auth, IO, batches, logs, upload, validation, pricing and publish.
- It requires admin login before rendering the main app.
- It routes catalog import to `render_upload_tab()`.

Runtime status:

```text
NOT VERIFIED
```

Reason:

- no live Admin URL / login session was available for this checkpoint.

### 3.2. Excel upload / import flow

Source-level status:

```text
AVAILABLE
```

Observed source-level behavior:

- `admin_upload.py` provides a downloadable Excel template.
- It accepts `.xlsx` files.
- It reads Excel sheets.
- It performs sheet diagnostics.
- It attempts header-row detection.
- It detects recognized and unrecognized columns.
- It renders raw Excel preview.
- It normalizes rows into the Admin stone schema.
- It renders normalized preview.
- It runs validation before saving.
- It requires explicit confirmation before saving the batch.

Runtime status:

```text
NOT VERIFIED
```

Reason:

- no controlled fixture was uploaded through live Admin UI in this checkpoint.

### 3.3. Validation / preview

Source-level status:

```text
AVAILABLE
```

Observed source-level behavior:

- critical fields are validated;
- empty/wrong sheet can become critical error;
- missing required fields become critical errors;
- duplicate `stone_id` becomes critical error;
- optional pricing and score issues are warnings in base validation;
- upload flow adds stricter KURGIN Score gate for Round main/large stones;
- critical errors block batch save;
- warnings can be displayed without blocking all current-stage import paths.

Runtime status:

```text
NOT VERIFIED
```

Reason:

- no live fixture upload and preview interaction was completed.

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

This satisfies the no-publish boundary for this smoke attempt.

## 5. Blockers

### 5.1. Runtime blockers

| ID | Blocker | Impact | Required resolution |
|---|---|---|---|
| BLK-001 | Live Admin app URL not available in task context | Cannot open Admin app | Provide URL or run smoke manually by operator |
| BLK-002 | Admin login/session not available in task context | Cannot access Admin upload UI | Provide credentials/session through approved secure process or run manually |
| BLK-003 | Interactive upload could not be completed here | Cannot confirm file acceptance, diagnostics, mapping or preview at runtime | Run controlled live smoke with operator/browser |
| BLK-004 | Controlled fixture was not uploaded live | Cannot mark import smoke PASS | Use a small approved `.xlsx` fixture in a separate smoke run |

### 5.2. No source-level code blocker found

No source-level issue was found that justifies automatic code changes under this task.

No fix was made.

## 6. Risk items

| ID | Risk | Severity | Handling |
|---|---|---:|---|
| RISK-001 | Source-level import path exists, but runtime upload remains unverified. | Medium | Run live Admin upload smoke. |
| RISK-002 | Admin import auto-marks MVP flags and relies on Publication Gate review. | Medium | Use controlled fixture and verify preview/gate before any save/publish workflow. |
| RISK-003 | Critical/warning separation is source-visible but not runtime-confirmed. | Medium | Use fixture with one valid row and one controlled warning/critical row. |
| RISK-004 | Publish must remain untouched during import smoke. | High | Do not enter Publication Gate publish action during this smoke. |
| RISK-005 | Any later fixture creation must not alter production data. | Medium | Keep fixture local or in a separate approved test fixture path. |

## 7. Controlled fixture recommendation for next manual run

A minimal future fixture should contain no production data and should be clearly marked as smoke-only.

Recommended rows:

1. Valid Round row with all required fields and price omitted or zero.
2. Row missing one critical field, such as `Report #`, to confirm critical error behavior.
3. Row missing price only, to confirm warning/request-price behavior.
4. Optional unknown column, to confirm it is visible as unrecognized and does not become active logic.

Recommended fixture columns:

- `stone_id`
- `shape`
- `carat`
- `color`
- `clarity`
- `lab`
- `report_number`
- `price_rub`
- `karo_score`
- `measurements`
- `current_status`
- `show_in_catalog`
- `is_mvp_eligible`
- `has_lab_document`
- `physically_received`
- `checked_by_kurgin`
- `upload_confirmed`

The fixture should not be published to `kurgin-data` during this smoke.

## 8. Allowed next actions

Allowed next actions:

1. Provide or confirm live Admin app URL.
2. Run manual Admin login/open check.
3. Prepare a small local `.xlsx` smoke fixture.
4. Upload fixture through Admin upload UI.
5. Verify sheet diagnostics.
6. Verify recognized/unrecognized column table.
7. Verify raw preview and normalized preview.
8. Verify critical vs warning separation.
9. Stop before publish.
10. Update this document with runtime evidence and verdict.

## 9. Blocked actions

Blocked by this smoke task:

- publish to `kurgin-data`;
- update `catalog.json`;
- update `data/catalog.json`;
- update `stones.csv`;
- update `upload_batches.csv`;
- data schema changes;
- code changes without separate approval;
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

This document satisfies the checkpoint documentation task if:

- `docs/KURGIN_ADMIN_IMPORT_SMOKE_V0_1.md` exists;
- verdict is included: `BLOCKED`;
- no production publish is performed;
- no Streamlit changes are made;
- no Analyzer changes are made;
- no formula/scoring changes are made;
- no data changes are made;
- no production deploy is performed;
- blockers are listed;
- next manual actions are listed.

## 11. Closure

Final verdict:

```text
BLOCKED
```

The manual live Admin import smoke could not be completed in this checkpoint because live Admin URL, login/session and interactive upload execution were not available.

The current source-level import path remains available, but runtime PASS requires a separate manual smoke run with the live Admin app and a controlled `.xlsx` fixture.
