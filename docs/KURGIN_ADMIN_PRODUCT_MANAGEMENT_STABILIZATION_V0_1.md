# KURGIN ADMIN PRODUCT MANAGEMENT STABILIZATION v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: Product Management stabilization audit and regression log.
Status: removed-batch visibility source fix completed / live runtime recheck required.

This document records stabilization after Product Management workflow implementation, package split, navigation/session-state fix, soft-remove runtime fix, and removed-batch visibility fix.

This task did not add large Product Management features, did not change public Streamlit, did not change `kurgin-data`, did not change Analyzer/formula/scoring, did not add pricing engine, client payment, checkout, reserve/sold automation, cleanup/delete, physical deletion, or production deploy.

## 1. Checked head

Checked source head after removed-batch visibility fix:

```text
4dcfbd0def9fe0e5c8093571341252b380fc65b8
```

Documentation update commit message:

```text
Fix removed batch visibility
```

## 2. Final verdict

```text
RISK
```

Reason:

- Source-level removed-batch visibility fix is `PASS`.
- Runtime verdict remains `RISK` until live Admin is rechecked after the fix.
- `py_compile` was not executed from this tool context.

This is not a known source blocker. It is a runtime-verification gap.

## 3. Source-level verdict

```text
PASS
```

Source-level result:

- `app.py` remains a router/composition layer.
- Product Management is imported through:

```python
from admin_product_management import render_product_management_page
```

- Product Management is in package `admin_product_management/`.
- `render_upload_tab()` is reused; upload flow was not rewritten from scratch.
- `render_publish_tab()` is reused; publish logic was not rewritten.
- `admin_io.py` remains the storage/schema layer.
- Step navigation uses `product_management_next_menu` instead of mutating widget-bound `product_management_menu` after `st.radio()` creation.
- Soft remove now uses robust dataframe/index handling.
- Removed batches now receive batch-level archived state in `upload_batches.csv`.
- Active batch list now excludes `removed_from_sale` / `archived` batches.
- Archived batches are shown separately under `Снятые с продажи / Архив`.
- No forbidden repository was touched.

## 4. Runtime verdict

```text
RISK
```

Expected runtime result after latest fix:

- `Снять партию с продажи` should not crash.
- Non-sold active rows in the batch should receive:
  - `show_in_catalog = false`
  - `is_mvp_eligible = false`
  - `current_status = removed_from_sale`
  - `removed_from_sale_at = today`
- Sold rows should remain untouched.
- The batch row should receive:
  - `batch_status = removed_from_sale`
  - `removed_from_sale_at = today`
  - `removed_from_sale_note = removed from sale in admin`
- If no active rows exist, UI should show:

```text
Нет активных камней для снятия с продажи.
```

- The batch should disappear from the ordinary active `Загруженные партии` list.
- The batch should appear under `Снятые с продажи / Архив`.
- Public site should not change until a separate publish.

## 5. Checked files / modules

Checked Product Management active path:

```text
app.py
admin_upload.py
admin_io.py
admin_product_management/__init__.py
admin_product_management/page.py
admin_product_management/navigation.py
admin_product_management/upload_flow.py
admin_product_management/pricing_flow.py
admin_product_management/publish_flow.py
admin_product_management/batches_view.py
admin_product_management/state_view.py
admin_product_management/detail_view.py
admin_product_management/payments.py
admin_product_management/exports.py
admin_product_management/helpers.py
```

Files changed by this removed-batch visibility fix:

```text
admin_io.py
admin_product_management/detail_view.py
admin_product_management/batches_view.py
```

## 6. Source-level checklist

| Check | Result |
|---|---:|
| `app.py` remains router/composition layer | PASS |
| Product Management imported from package entrypoint | PASS |
| Old monolith `admin_product_management.py` absent / not used | PASS |
| Package `admin_product_management/` exists | PASS |
| `product_management_next_menu` request key used for step navigation | PASS |
| Direct next-button mutation of widget-bound `product_management_menu` removed | PASS |
| Existing `render_upload_tab()` reused | PASS |
| Existing `render_publish_tab()` reused | PASS |
| `admin_io.py` remains storage/schema layer | PASS |
| Batch schema has `batch_status` | PASS |
| Batch schema has `removed_from_sale_at` | PASS |
| Batch schema has `removed_from_sale_note` | PASS |
| Old batches without `batch_status` remain active by default | PASS |
| Soft remove updates stones, not physical delete | PASS |
| Soft remove updates batch row if present | PASS |
| Active batch list excludes `removed_from_sale` / `archived` | PASS |
| Archive block shows `removed_from_sale` / `archived` batches | PASS |
| No public Streamlit changes | PASS |
| No direct `kurgin-data` changes | PASS |
| No Analyzer/formula/scoring changes | PASS |

## 7. Runtime checklist status

| Runtime check | Status |
|---|---:|
| Admin opens | NEEDS LIVE RECHECK |
| `Управление товаром` opens | NEEDS LIVE RECHECK |
| `Загруженные партии` opens | SOURCE PASS / NEEDS LIVE RECHECK |
| Active list hides removed batches | SOURCE PASS / NEEDS LIVE RECHECK |
| Archive block shows removed batches | SOURCE PASS / NEEDS LIVE RECHECK |
| `Состояние` opens | NEEDS LIVE RECHECK |
| `Подробнее` opens as separate internal page | NEEDS LIVE RECHECK |
| `Снять партию с продажи` no longer crashes | SOURCE FIXED / NEEDS LIVE RECHECK |
| Batch row gets `batch_status = removed_from_sale` | SOURCE FIXED / NEEDS LIVE RECHECK |
| Public site remains unchanged until publish | SOURCE PASS / NEEDS LIVE RECHECK |
| Existing import flow opens | SOURCE PASS / NEEDS LIVE RECHECK |
| Existing publish flow opens | SOURCE PASS / NEEDS LIVE RECHECK |
| No client payment / checkout / reserve / sold automation added | SOURCE PASS |

## 8. Found bugs

### BUG-001 — Streamlit widget session_state mutation

Status:

```text
FIXED SOURCE-LEVEL
```

### BUG-002 — Back-to-state path used widget-bound menu key

Status:

```text
FIXED SOURCE-LEVEL
```

### BUG-003 — Soft remove TypeError

Observed in live Admin:

```text
TypeError in admin_product_management/detail_view.py render_soft_remove() when pressing Снять партию с продажи
```

Status:

```text
FIXED SOURCE-LEVEL / NEEDS LIVE RECHECK
```

### BUG-004 — Removed batch stayed visible as active loaded batch

Observed/identified:

```text
Soft remove updated stones but not upload_batches.csv batch row, so the removed batch continued to appear in the ordinary Загруженные партии list.
```

Cause:

```text
load_batches() returned all batch rows and there was no batch_status / archive distinction.
```

Status:

```text
FIXED SOURCE-LEVEL / NEEDS LIVE RECHECK
```

## 9. Fixed bugs

### FIX-001 — Safe next-menu request key

Step navigation writes to:

```python
st.session_state["product_management_next_menu"]
```

### FIX-002 — Detail back navigation stabilized

`← Назад к состоянию` uses:

```python
st.session_state["product_management_next_menu"] = "Состояние"
```

### FIX-003 — Robust soft remove dataframe update

Implemented in `admin_product_management/detail_view.py`:

- required stone columns are guaranteed before update;
- active mask is aligned with `stones.index`;
- updates use explicit `active_indexes`;
- `affected == 0` shows warning and returns without crash;
- sold rows are excluded;
- successful update calls `save_stones(stones)` and logs action.

### FIX-004 — Batch-level removed/archive visibility

Implemented:

- `admin_io.py` extends `BATCH_COLS` backward-compatibly with:
  - `batch_status`
  - `removed_from_sale_at`
  - `removed_from_sale_note`
- new uploads are marked with:
  - `batch_status = uploaded`
- soft remove updates the batch row if present:
  - `batch_status = removed_from_sale`
  - `removed_from_sale_at = today`
  - `removed_from_sale_note = removed from sale in admin`
- ordinary `Загруженные партии` active list shows only:
  - empty status
  - `uploaded`
  - `active`
  - `draft`
- `removed_from_sale` and `archived` are shown below in:

```text
Снятые с продажи / Архив
```

Archive actions remain:

- `Подробнее`
- `Скачать Excel`

## 10. py_compile status

```text
NOT EXECUTED FROM THIS TOOL CONTEXT
```

Required local/CI command:

```bash
python -m py_compile app.py admin_upload.py admin_io.py admin_product_management/*.py
```

## 11. Active path

Active Product Management path:

```text
app.py
  -> from admin_product_management import render_product_management_page
  -> admin_product_management/__init__.py
  -> admin_product_management/page.py
  -> split section modules
```

## 12. Legacy / fallback path

Legacy/fallback retained intentionally:

```text
Каталог fallback in app.py
```

Do not hide or remove it in Product Management stabilization tasks.

## 13. Remaining risks after fix

| Risk | Level | Handling |
|---|---:|---|
| Live runtime not rechecked after removed-batch visibility fix | Medium | Re-run live Admin soft remove and batch list check. |
| `py_compile` not executed here | Medium | Run local/CI compile command. |
| Soft remove is Admin-side only until publish | Medium | Keep publish boundary explicit. |
| Legacy Catalog fallback overlaps Product Management paths | Low-medium | Keep fallback until separate cleanup task. |

## 14. Future / blocked without separate task

Do not do without separate approval:

- new Product Management features;
- pricing engine;
- client payment;
- checkout;
- reserve/sold automation;
- public Streamlit changes;
- direct `kurgin-data` changes;
- Analyzer/formula/scoring changes;
- cleanup/delete;
- physical delete;
- production deploy;
- hiding legacy Catalog fallback.

## 15. Final smoke summary

```text
FINAL VERDICT: RISK
SOURCE-LEVEL VERDICT: PASS
RUNTIME VERDICT: RISK UNTIL LIVE REMOVED-BATCH VISIBILITY RECHECK
PY_COMPILE: NOT EXECUTED FROM THIS TOOL CONTEXT
```

Required manual/runtime check:

```text
Admin -> Управление товаром -> Состояние -> Подробнее -> Снять партию с продажи -> verify active stones removed_from_sale -> verify sold rows untouched -> Загруженные партии -> verify batch hidden from active list -> verify batch visible under Снятые с продажи / Архив -> verify public site unchanged until publish
```
