# KURGIN ADMIN PRODUCT MANAGEMENT STABILIZATION v0.1

Repo: `kka45821-del/kurgin-admin-mvp`
Scope: Product Management stabilization audit and regression log.
Status: source-level soft-remove fix completed / live runtime recheck required.

This document records stabilization after Product Management workflow implementation, package split, navigation/session-state fix, and soft-remove runtime fix.

This task did not add Product Management features, did not change business logic, did not redesign UI, did not change public Streamlit, did not change `kurgin-data`, did not change Analyzer/formula/scoring, did not add pricing engine, client payment, checkout, reserve/sold automation, cleanup/delete, or production deploy.

## 1. Checked head

Checked source head after soft-remove fix:

```text
ed2cecca7f482c2a347a3416cdbdb22fc6fd77e7
```

Documentation update commit message:

```text
Fix product management soft remove
```

## 2. Final verdict

```text
RISK
```

Reason:

- Source-level regression fix is `PASS`.
- Runtime verdict remains `RISK` because the live Admin soft-remove path was not re-tested from this tool context after the fix.
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

- The old monolith `admin_product_management.py` is absent from the current source path and is no longer used.
- Product Management is in package `admin_product_management/`.
- `render_upload_tab()` is reused; upload flow was not rewritten from scratch.
- `render_publish_tab()` is reused; publish logic was not rewritten.
- `admin_io.py` remains the storage/schema layer.
- Step navigation uses `product_management_next_menu` instead of mutating widget-bound `product_management_menu` after `st.radio()` creation.
- Soft remove now uses robust dataframe/index handling.
- No forbidden repository was touched.

## 4. Runtime verdict

```text
RISK
```

Reason:

- Live Admin runtime previously exposed a `TypeError` when pressing `Снять партию с продажи`.
- The source-level fix has been applied.
- Live Admin was not re-tested after the fix from this tool context.

Expected runtime result after fix:

- `Снять партию с продажи` should not crash.
- Non-sold active rows in the batch should receive:
  - `show_in_catalog = false`
  - `is_mvp_eligible = false`
  - `current_status = removed_from_sale`
  - `removed_from_sale_at = today`
- Sold rows should remain untouched.
- If no active rows exist, UI should show:

```text
Нет активных камней для снятия с продажи.
```

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

Primary file changed by this soft-remove fix:

```text
admin_product_management/detail_view.py
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
| Soft remove guarantees required columns before update | PASS |
| Soft remove uses boolean mask aligned with `stones.index` | PASS |
| Soft remove uses explicit `active_indexes` for `.loc` updates | PASS |
| Soft remove handles `affected == 0` without crash | PASS |
| Sold rows excluded from active remove mask | PASS |
| No public Streamlit changes | PASS |
| No direct `kurgin-data` changes | PASS |
| No Analyzer/formula/scoring changes | PASS |

## 7. Runtime checklist status

| Runtime check | Status |
|---|---:|
| Admin opens | NEEDS LIVE RECHECK |
| `Управление товаром` opens | NEEDS LIVE RECHECK |
| `Состояние` opens | NEEDS LIVE RECHECK |
| `Подробнее` opens as separate internal page | NEEDS LIVE RECHECK |
| `← Назад к состоянию` works through `product_management_next_menu` | SOURCE PASS / NEEDS LIVE RECHECK |
| Financial block visible | SOURCE PASS / NEEDS LIVE RECHECK |
| Supplier payments visible | SOURCE PASS / NEEDS LIVE RECHECK |
| 3 tables visible | SOURCE PASS / NEEDS LIVE RECHECK |
| Excel downloads still available | SOURCE PASS / NEEDS LIVE RECHECK |
| `Снять партию с продажи` no longer crashes | SOURCE FIXED / NEEDS LIVE RECHECK |
| No active rows case shows warning instead of crash | SOURCE FIXED / NEEDS LIVE RECHECK |
| Existing import flow opens | SOURCE PASS / NEEDS LIVE RECHECK |
| Existing publish flow opens | SOURCE PASS / NEEDS LIVE RECHECK |
| No client payment / checkout / reserve / sold automation added | SOURCE PASS |

## 8. Found bugs

### BUG-001 — Streamlit widget session_state mutation

Observed earlier:

```text
StreamlitAPIException after pressing Далее after Save batch
```

Cause:

```text
The code attempted to assign st.session_state["product_management_menu"] after the st.radio widget with key="product_management_menu" had already been created.
```

Status:

```text
FIXED SOURCE-LEVEL
```

### BUG-002 — Back-to-state path used widget-bound menu key

Found during source-level stabilization:

```text
Подробнее -> ← Назад к состоянию used product_management_menu directly
```

Status:

```text
FIXED SOURCE-LEVEL
```

### BUG-003 — Soft remove TypeError

Observed in live Admin:

```text
TypeError in admin_product_management/detail_view.py render_soft_remove() when pressing Снять партию с продажи
```

Likely cause class:

```text
dataframe/schema/dtype/index alignment issue during boolean mask or .loc assignment
```

Status:

```text
FIXED SOURCE-LEVEL / NEEDS LIVE RECHECK
```

## 9. Fixed bugs

### FIX-001 — Safe next-menu request key

Step navigation now writes to:

```python
st.session_state["product_management_next_menu"]
```

`render_product_management_page()` consumes it before rendering `st.radio()`.

### FIX-002 — Detail back navigation stabilized

`← Назад к состоянию` now uses:

```python
st.session_state["product_management_next_menu"] = "Состояние"
```

### FIX-003 — Robust soft remove dataframe update

Implemented in `admin_product_management/detail_view.py`:

1. Required columns are guaranteed before update:

```text
show_in_catalog
is_mvp_eligible
current_status
removed_from_sale_at
```

2. The active mask is aligned with `stones.index`:

```python
active_mask = (batch_mask & ~sold_mask).reindex(stones.index, fill_value=False).fillna(False).astype(bool)
active_indexes = stones.index[active_mask]
```

3. Updates use explicit indexes:

```python
stones.loc[active_indexes, "show_in_catalog"] = False
stones.loc[active_indexes, "is_mvp_eligible"] = False
stones.loc[active_indexes, "current_status"] = "removed_from_sale"
stones.loc[active_indexes, "removed_from_sale_at"] = today
```

4. If no active rows exist:

```text
Нет активных камней для снятия с продажи.
```

and the function returns without saving or crashing.

5. Sold rows are excluded from the active remove mask.

6. After successful update:

- `save_stones(stones)` is called;
- `write_admin_action(...)` is called;
- success message is shown;
- `st.rerun()` is called.

## 10. py_compile status

```text
NOT EXECUTED FROM THIS TOOL CONTEXT
```

Reason:

- This context can edit and inspect GitHub files but does not run the deployed Admin or a checked-out repository runtime.

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

Active modules:

- `admin_product_management/page.py`
- `admin_product_management/navigation.py`
- `admin_product_management/upload_flow.py`
- `admin_product_management/pricing_flow.py`
- `admin_product_management/publish_flow.py`
- `admin_product_management/batches_view.py`
- `admin_product_management/state_view.py`
- `admin_product_management/detail_view.py`
- `admin_product_management/payments.py`
- `admin_product_management/exports.py`
- `admin_product_management/helpers.py`

## 12. Legacy / fallback path

Legacy/fallback retained intentionally:

```text
Каталог fallback in app.py
```

Fallback includes existing catalog/import/batches/preview/publication/sections/statuses/prices routes.

Do not hide or remove it in Product Management stabilization tasks.

## 13. Remaining risks after fix

| Risk | Level | Handling |
|---|---:|---|
| Live runtime not rechecked after soft-remove fix | Medium | Re-run live Admin `Снять партию с продажи`. |
| `py_compile` not executed here | Medium | Run local/CI compile command. |
| Soft remove is Admin-side only until publish | Medium | Keep publish boundary explicit. |
| Supplier payments are internal only | Medium | Do not confuse with client checkout/payment. |
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
- production deploy;
- hiding legacy Catalog fallback.

## 15. Final smoke summary

```text
FINAL VERDICT: RISK
SOURCE-LEVEL VERDICT: PASS
RUNTIME VERDICT: RISK UNTIL LIVE SOFT REMOVE RECHECK
PY_COMPILE: NOT EXECUTED FROM THIS TOOL CONTEXT
```

Required manual/runtime check:

```text
Admin -> Управление товаром -> Состояние -> Подробнее -> Снять партию с продажи -> confirm no TypeError -> verify active/non-sold rows removed_from_sale -> verify sold rows untouched -> verify public site unchanged until publish
```
