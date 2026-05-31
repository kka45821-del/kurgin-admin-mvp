# KURGIN ADMIN LEGACY CATALOG BOUNDARY v0.1

Repo: `kka45821-del/kurgin-admin-mvp`  
Scope: admin stabilization boundary.  
Status: legacy catalog read-only boundary / product workflow lock.

This document fixes the boundary between the old Catalog fallback view and the active Product Management workflow.

It does not change public Streamlit, `kurgin-data`, Analyzer, formula, scoring, pricing engine, checkout, payment, reserve, sold automation or production deployment.

---

## 1. Problem

The old Admin Catalog fallback path previously allowed direct mass editing and saving of `data/stones.csv` through:

```text
render_catalog_page()
→ catalog_all
→ st.data_editor(df)
→ save_stones(edited)
```

That created a second product-management path outside the stabilized Product Management workflow.

Risk:

```text
old Catalog direct save
≠ controlled Product Management workflow
```

This can cause Admin Product Management and old Catalog fallback to diverge.

---

## 2. Primary workflow lock

Locked principle:

```text
Product Management is the primary product workflow.
```

Primary Admin product work must happen through:

```text
Управление товаром
```

This includes:

- upload;
- price setup;
- publication;
- uploaded batches;
- archive;
- editing placeholders / controlled future work;
- state view;
- all stones view;
- active Product Management publication route.

---

## 3. Legacy Catalog boundary

The old Catalog area remains allowed only as:

```text
legacy / fallback / read-only diagnostic view
```

It may be used to:

- inspect current catalog rows;
- diagnose status fields;
- inspect publication preview;
- access reused upload / publication engines through existing Admin routes;
- support transition while Product Management remains the main workflow.

It must not become:

- a second product-management path;
- a direct mass-edit path;
- an alternative publication authority;
- a bypass around Product Management archive / batch logic;
- a bypass around publication rules.

---

## 4. Direct save disabled

The old `catalog_all` view must not expose active direct save to `stones.csv`.

Disabled path:

```text
st.data_editor(df)
→ save_stones(edited)
```

Replacement behavior:

```text
read-only dataframe
+ warning that Product Management is the active workflow
```

Required warning text:

```text
Legacy / fallback view. Основной рабочий контур: Управление товаром. Ручное массовое сохранение через старый Каталог отключено.
```

---

## 5. Reused engines remain valid

This boundary does not remove shared engines.

The following may remain reused by Product Management and legacy Admin routes until later cleanup:

- upload engine;
- publish engine;
- preview logic;
- publication rules;
- status diagnostics.

Reusing engines is acceptable.

Creating a second editable workflow is not acceptable.

---

## 6. Not in this task

Do not:

- hide the full Catalog menu yet;
- delete legacy Catalog code;
- remove upload / publish routes;
- rewrite Product Management;
- rewrite Admin publication logic;
- change public Streamlit;
- change `kurgin-data`;
- change Analyzer / formula / scoring;
- add pricing engine;
- add checkout / payment / reserve / sold automation;
- physically delete data;
- do production deploy.

Full hiding or removal of the old Catalog area is a future step after live smoke.

---

## 7. Acceptance lock

This boundary is satisfied when:

1. Product Management remains primary product workflow.
2. Old Catalog all view is read-only or save-disabled.
3. Direct `data_editor + save_stones` path is not active in old Catalog all view.
4. Old Catalog is visibly marked as legacy / fallback.
5. Existing import / publish flow remains available.
6. Public Streamlit is not changed by Admin stabilization.
7. `kurgin-data` is not changed.
8. Analyzer / formula / scoring are not changed.

---

## 8. Final lock statement

```text
Product Management controls product operations.
Old Catalog is a legacy / fallback / diagnostic surface.
Old Catalog must not become a second product-management workflow.
```
