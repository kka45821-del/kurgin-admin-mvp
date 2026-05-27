# KURGIN Pricing Formula v0.2-lite Scope

**Project:** KURGIN  
**Repository:** `kka45821-del/kurgin-admin-mvp`  
**Document:** Pricing Formula v0.2-lite Scope  
**Status:** documentation-only scope before code implementation  
**Source document:** `docs/KURGIN_PRICING_FORMULA_V0_2.md`  

---

## 0. Scope lock

This document defines the minimum safe implementation scope for Pricing Formula v0.2-lite.

It does **not**:

- write code;
- confirm prices;
- run mass confirmation;
- publish `catalog.json`;
- change the public site;
- enable checkout;
- enable reserve;
- enable sold;
- create roles;
- create specialist cabinet;
- create client mode.

```text
v0.2-lite scope document ≠ code implementation
calculated price ≠ confirmed public price
preview ≠ publication
```

---

## 1. Purpose of v0.2-lite

Pricing Formula v0.2-lite is the minimum safe implementation of Pricing Formula v0.2 for the first controlled test.

It exists to test the core economics before a full pricing system is implemented.

v0.2-lite should test:

- batch economics;
- USD / INR / RUB purchase inputs;
- customs;
- batch fixed expenses;
- KURGIN margin;
- jeweler / specialist margin;
- public extra;
- FX guard;
- after-tax guard;
- three calculated prices.

v0.2-lite is not a full commercial pricing workflow.

---

## 2. What is included in v0.2-lite

v0.2-lite includes the following inputs and controls:

```text
base_purchase_price_per_ct_supplier_currency
carat
invoice_currency
fx_rate_rub_per_invoice_currency
customs_percent
batch_fixed_expenses_rub
batch_total_supplier_currency
batch_expense_allocation_method = value_share
kurgin_score_coefficient
kurgin_fixed_margin_usd_per_ct
kurgin_variable_margin_percent
tax_on_profit_percent
jeweler_fixed_margin_usd_per_ct
jeweler_variable_margin_percent
public_fixed_extra_rub
public_extra_percent
rounding_to_1000_rub
```

The implementation must keep these fields as controlled inputs, not free-form formula execution.

---

## 3. Three calculated prices

v0.2-lite must calculate three prices:

```text
calculated_specialist_purchase_price_rub
calculated_specialist_client_display_price_rub
calculated_public_price_rub
```

Required price hierarchy:

```text
specialist_purchase_price_rub
<
specialist_client_display_price_rub
<
public_price_rub
```

Meaning:

```text
specialist_purchase_price_rub = price specialist pays KURGIN
specialist_client_display_price_rub = price specialist may show client
public_price_rub = ordinary public-site buyer price
```

In v0.2-lite, all three are calculated values until a separate selected confirmation step is performed.

---

## 4. Formula v0.2-lite

Base cost per carat:

```text
base_cost_per_ct =
base_purchase_price_per_ct
× (1 + customs_percent / 100)
× (1 + freight_percent / 100)
× (1 + unexpected_expenses_percent / 100)
```

Score-adjusted cost:

```text
score_adjusted_cost_per_ct =
base_cost_per_ct × kurgin_score_coefficient
```

KURGIN net margin target:

```text
kurgin_net_margin_target_per_ct =
kurgin_fixed_margin_usd_per_ct
+ score_adjusted_cost_per_ct × kurgin_variable_margin_percent / 100
```

KURGIN tax reserve:

```text
kurgin_tax_reserve_per_ct =
kurgin_net_margin_target_per_ct × tax_on_profit_percent / 100
```

Specialist purchase layer:

```text
specialist_purchase_per_ct =
score_adjusted_cost_per_ct
+ kurgin_net_margin_target_per_ct
+ kurgin_tax_reserve_per_ct
```

Jeweler / specialist client layer:

```text
jeweler_margin_per_ct =
jeweler_fixed_margin_usd_per_ct
+ specialist_purchase_per_ct × jeweler_variable_margin_percent / 100

specialist_client_display_per_ct =
specialist_purchase_per_ct + jeweler_margin_per_ct
```

RUB calculated prices:

```text
specialist_purchase_price_rub =
ceil_to_1000(specialist_purchase_per_ct × carat × fx_rate)

specialist_client_display_price_rub =
ceil_to_1000(specialist_client_display_per_ct × carat × fx_rate)
```

Public extra:

```text
public_extra_rub =
max(
  public_fixed_extra_rub,
  specialist_client_display_price_rub × public_extra_percent / 100
)
```

Public price:

```text
public_price_rub =
ceil_to_1000(specialist_client_display_price_rub + public_extra_rub)
```

Control rule:

```text
KURGIN Score coefficient applies to the cost layer,
not to the final public price.
```

---

## 5. Batch expenses in v0.2-lite

Batch fixed expenses must use value-share allocation.

Formula:

```text
stone_share =
stone_purchase_total_currency / batch_total_supplier_currency

allocated_batch_expense_rub =
batch_fixed_expenses_rub × stone_share
```

Required allocation method:

```text
batch_expense_allocation_method = value_share
```

Limitation for v0.2-lite:

```text
If the first code package calculates batch fixed expenses separately from the per-carat formula,
this must be explicitly shown in preview output.
```

The preview must not hide whether batch expenses were included in:

- cost layer;
- separate allocated cost;
- guard calculations;
- final calculated public price.

---

## 6. Guards in v0.2-lite

v0.2-lite must include four mandatory guards.

### A. FX no-loss guard

```text
if final_price_rub < fx_protected_purchase_cost_rub:
    price_status = blocked
    error = below_fx_protected_purchase_cost
```

### B. After-tax no-loss guard

```text
if net_profit_after_tax_rub <= 0:
    price_status = blocked
    error = after_tax_profit_negative
```

### C. Minimum net profit guard

```text
if net_profit_after_tax_rub < minimum_net_profit_required_rub:
    price_status = needs_review
    warning = after_tax_profit_below_minimum
```

### D. Price hierarchy guard

```text
if not specialist_purchase < specialist_client_display < public:
    price_status = blocked
    error = price_hierarchy_invalid
```

All guards must run before selected confirmation.

No confirmed public price may bypass these guards.

---

## 7. What is not included in v0.2-lite

v0.2-lite does not include:

- roles;
- specialist cabinet;
- client mode implementation;
- checkout;
- payment;
- reserve;
- sold;
- automatic publish;
- CRM;
- backend requests;
- full supplement invoice recalculation;
- full actual_paid_rub reconciliation;
- manual override.

Manual override is excluded from v0.2-lite because it can bypass the purpose of the first controlled test.

---

## 8. What may be confirmed after v0.2-lite

For the first controlled test, do **not** confirm all three prices as public prices.

After selected confirmation, only the public price fields may be written:

```text
confirmed_public_price_rub = calculated_public_price_rub
price_rub = calculated_public_price_rub
price_confirmed = True
price_status = confirmed
formula_version = pricing_formula_v0_2_lite
pricing_run_timestamp
```

Specialist prices must remain calculated-only until roles and specialist cabinet exist.

Do not write specialist price fields into public buyer display.

---

## 9. What must not be done

Do not:

- confirm `pending_invoice_same_shipment` stones;
- write `specialist_purchase_price_rub` as public price;
- show `specialist_client_display_price_rub` on the public site;
- enable checkout;
- enable reserve;
- publish priced catalog without guard status `ok`;
- bypass FX guard;
- bypass after-tax guard;
- bypass minimum profit guard;
- treat calculated preview as commercial approval.

---

## 10. Future code micro-packages after this document

Implementation must be split into small packages.

### A. Pure formula module

```text
admin_pricing_formula_v02_lite.py
```

Purpose:

- deterministic formula functions;
- no Streamlit UI;
- no file writes;
- no catalog publication;
- no confirmation;
- no checkout.

### B. Preview UI

```text
admin_pricing.py shows v0.2-lite preview
```

Purpose:

- show calculated values;
- show guards;
- show blocked / needs_review / ok statuses;
- show price hierarchy;
- show after-tax result;
- no confirmation yet unless separately approved.

### C. Selected confirmation

```text
selected confirmation for public price rows only
```

Purpose:

- confirm only selected rows;
- write only public confirmed price fields;
- require guard status ok;
- write audit log;
- no specialist pricing publication;
- no checkout enablement.

---

## 11. Final control statement

Pricing Formula v0.2-lite is a controlled bridge between documentation and code.

```text
Full v0.2 is too large for one code package.
v0.2-lite is the first safe testable subset.
```

This document allows future implementation planning only.

```text
No code changed by this document.
No price confirmed by this document.
No catalog published by this document.
No public site changed by this document.
```
