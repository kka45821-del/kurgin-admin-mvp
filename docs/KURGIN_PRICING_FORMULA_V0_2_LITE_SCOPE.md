# KURGIN Pricing Formula v0.2-lite Scope

**Project:** KURGIN  
**Repository:** `kka45821-del/kurgin-admin-mvp`  
**Document:** Pricing Formula v0.2-lite Scope  
**Status:** implementation scope / controlled preview-only pricing logic  
**Source document:** `docs/KURGIN_PRICING_FORMULA_V0_2.md`  

---

## 0. Scope lock

This document defines the minimum safe implementation scope for Pricing Formula v0.2-lite.

It does **not**:

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
calculated price ≠ confirmed public price
preview ≠ publication
request_price ≠ checkout
```

---

## 1. Purpose of v0.2-lite

Pricing Formula v0.2-lite is the minimum safe implementation of Pricing Formula v0.2 for controlled admin preview.

It tests:

- batch economics;
- USD / INR / RUB purchase inputs;
- customs;
- batch fixed expenses;
- KURGIN margin;
- jeweler / specialist margin;
- public extra;
- FX guard;
- after-tax guard;
- Round/non-Round score handling;
- three calculated prices.

v0.2-lite is not a full commercial pricing workflow.

---

## 2. Inputs and controls

v0.2-lite includes:

```text
base_purchase_price_per_ct_supplier_currency
carat
shape
invoice_currency
fx_rate_rub_per_invoice_currency
customs_percent
batch_fixed_expenses_rub
batch_total_supplier_currency
batch_expense_allocation_method = value_share
kurgin_score
section
kurgin_score_coefficient
kurgin_fixed_margin_usd_per_ct
kurgin_variable_margin_percent
tax_on_profit_percent
jeweler_fixed_margin_usd_per_ct
jeweler_variable_margin_percent
public_fixed_extra_rub
public_extra_percent
minimum_net_profit_fixed_rub
minimum_net_profit_percent_by_tier
low_score_jeweler_margin_rub
low_score_public_spread_rub
rounding_to_1000_rub
```

The implementation must keep these fields as controlled inputs, not free-form formula execution.

---

## 3. Three calculated prices

v0.2-lite calculates:

```text
calculated_specialist_purchase_price_rub
calculated_specialist_client_display_price_rub
calculated_public_price_rub
```

Required hierarchy:

```text
specialist_purchase_price_rub
<
specialist_client_display_price_rub
<
public_price_rub
```

---

## 4. Base formula

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
base_cost_per_ct × effective_kurgin_score_coefficient
```

KURGIN margin and tax reserve:

```text
kurgin_net_margin_target_per_ct =
kurgin_fixed_margin_usd_per_ct
+ score_adjusted_cost_per_ct × kurgin_variable_margin_percent / 100

kurgin_tax_reserve_per_ct =
kurgin_net_margin_target_per_ct × tax_on_profit_percent / 100

specialist_purchase_per_ct =
score_adjusted_cost_per_ct
+ kurgin_net_margin_target_per_ct
+ kurgin_tax_reserve_per_ct
```

Normal specialist client layer:

```text
jeweler_margin_per_ct =
jeweler_fixed_margin_usd_per_ct
+ specialist_purchase_per_ct × jeweler_variable_margin_percent / 100

specialist_client_display_per_ct =
specialist_purchase_per_ct + jeweler_margin_per_ct
```

---

## 5. Score handling rules

### A. Round main / large without Score

```text
if section in ["main", "large"]
and shape = Round
and KURGIN Score is missing:
    price_status = blocked
    error = round_score_required
    score_status = round_score_required
```

### B. Non-Round main / large without Score

```text
if section in ["main", "large"]
and shape != Round
and KURGIN Score is missing:
    effective_kurgin_score_coefficient = 1.0
    score_status = non_round_score_not_required
    specialist_client_mode_status = normal_non_round_score_not_required
    not blocked
```

### C. Round main / large with Score < 80

```text
if section in ["main", "large"]
and shape = Round
and KURGIN Score < 80:
    specialist_client_mode_status = low_score_fixed_rule
    specialist_client_display_price_rub = specialist_purchase_price_rub + low_score_jeweler_margin_rub
    public_price_rub = specialist_client_display_price_rub + low_score_public_spread_rub
```

Default values:

```text
low_score_jeweler_margin_rub = 2000
low_score_public_spread_rub = 2000
```

For `Round main/large KURGIN Score < 80`, do **not** apply:

- `jeweler_fixed_margin_usd_per_ct`;
- `jeweler_variable_margin_percent`;
- dynamic specialist margin;
- score margin modifier.

### D. Round main / large with Score >= 80

```text
if section in ["main", "large"]
and shape = Round
and KURGIN Score >= 80:
    specialist_client_mode_status = normal
    use normal v0.2-lite formula
```

`KURGIN Score = 80.00` is normal path, not low-score path.

### E. Out of current scope

```text
if section not in ["main", "large"]:
    price_status = blocked / needs_review
    error_or_warning = section_outside_v02_lite_scope
```

---

## 6. Batch expenses

Batch fixed expenses use value-share allocation:

```text
stone_share =
stone_purchase_total_currency / batch_total_supplier_currency

allocated_batch_expense_rub =
batch_fixed_expenses_rub × stone_share
```

Currency guard:

```text
if batch_total_supplier_currency > 0
and batch_total_currency != invoice_currency:
    price_status = blocked
    error = batch_currency_mismatch
```

---

## 7. Guards

FX guard:

```text
if final_price_rub < fx_protected_purchase_cost_rub:
    price_status = blocked
    error = below_fx_protected_purchase_cost
```

After-tax guard:

```text
if net_profit_after_tax_rub <= 0:
    price_status = blocked
    error = after_tax_profit_negative
```

Minimum profit guard:

```text
if net_profit_after_tax_rub < minimum_net_profit_required_rub:
    price_status = needs_review
    warning = after_tax_profit_below_minimum
```

Price hierarchy guard:

```text
if not specialist_purchase < specialist_client_display < public:
    price_status = blocked
    error = price_hierarchy_invalid
```

---

## 8. Output fields

v0.2-lite result must expose:

```text
calculated_specialist_purchase_price_rub
calculated_specialist_client_display_price_rub
calculated_public_price_rub
base_cost_per_ct
score_adjusted_cost_per_ct
allocated_batch_expense_rub
batch_expense_included_in_final_price
kurgin_tax_reserve_per_ct
net_profit_after_tax_rub
minimum_net_profit_required_rub
price_status
warnings
errors
formula_version
specialist_client_mode_status
low_score_jeweler_margin_rub
low_score_public_spread_rub
effective_kurgin_score_coefficient
score_status
```

---

## 9. Public catalog restrictions

The ordinary public catalog must not show:

- `low_score_fixed_rule`;
- specialist margin;
- specialist client display price;
- specialist purchase price;
- specialist_client_mode_status.

This information is for future specialist cabinet / professional mode only.

---

## 10. What is not included

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

---

## 11. Final control statement

```text
No price confirmed by this document.
No catalog published by this document.
No public site changed by this document.
No checkout enabled by this document.
No role / specialist cabinet / client mode launched by this document.
```
