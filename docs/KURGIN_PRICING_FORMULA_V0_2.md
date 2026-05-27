# KURGIN Pricing Formula v0.2

**Project:** KURGIN  
**Repository:** `kka45821-del/kurgin-admin-mvp`  
**Document:** Pricing Formula v0.2  
**Status:** documentation-only design package  
**Scope:** batch-based / multi-currency / after-tax protected pricing model  

---

## 0. Scope lock

This document defines pricing logic. It does not confirm prices, publish `catalog.json`, change the public site, enable checkout, create roles, create specialist cabinet or create client mode.

```text
calculated_price_rub ≠ confirmed_public_price_rub
pricing preview ≠ safe public price
request_price ≠ checkout
```

---

## 1. Purpose

Pricing Formula v0.2 defines a safer future pricing model for KURGIN.

It supports:

- batch-based purchasing;
- multi-currency supplier invoices;
- INR / USD / RUB future supply flows;
- FX risk protection;
- customs;
- batch fixed expense allocation;
- pending supplement invoices;
- specialist and public price separation;
- after-tax no-loss protection;
- minimum net profit protection;
- Round/non-Round score handling;
- low-score fixed specialist mode for `main` / `large` Round stones below KURGIN Score 80.

---

## 2. Universal batch-based pricing model

Each batch / supply shipment must have its own parameters:

```text
batch_id
supplier_name
contract_date
invoice_number
invoice_currency
supplier_settlement_currency
kurgin_payment_currency = RUB
public_display_currency = RUB
invoice_total_currency
actual_paid_total_rub
fx_rate_source
fx_rate_rub_per_invoice_currency
customs_percent
batch_fixed_expenses_rub
batch_fixed_expenses_note
batch_expense_allocation_method
purchase_status
```

Batch data is a pricing input. It is not public catalog copy.

---

## 3. Multi-currency purchase and FX risk guard

Currency layers:

```text
supplier_price_currency
supplier_settlement_currency
kurgin_payment_currency = RUB
public_display_currency = RUB
```

FX no-loss guard:

```text
if final_price_rub < fx_protected_purchase_cost_rub:
    price_status = blocked
    error = below_fx_protected_purchase_cost

if final_price_rub < fx_protected_purchase_cost_rub + minimum_net_profit_rub:
    price_status = needs_review
    warning = price_too_close_to_purchase_cost
```

This guard must not be bypassed by manual confirmation.

---

## 4. Batch fixed expenses allocation

Fixed batch expenses must not be divided equally by the number of stones.

Use value-share allocation:

```text
stone_share =
stone_purchase_total_currency / total_batch_purchase_currency

allocated_batch_expense_rub =
batch_fixed_expenses_rub × stone_share
```

The batch total currency must match the purchase / invoice currency used for stone purchase prices. Do not mix USD stone prices with INR batch totals.

---

## 5. Customs

Customs is separate from air freight, broker, batch fixed expenses, margins and public price.

```text
customs_rub =
purchase_total_rub × customs_percent / 100
```

---

## 6. Pending supplement stones

Required pending status:

```text
purchase_status = pending_invoice_same_shipment
```

Pending supplement stones must not enter confirmed priced batch, public price confirmation, checkout, reserve or sold status.

---

## 7. Base v0.2-lite formula

Base cost:

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

KURGIN net margin target:

```text
kurgin_net_margin_target_per_ct =
kurgin_fixed_margin_usd_per_ct
+ score_adjusted_cost_per_ct × kurgin_variable_margin_percent / 100
```

Tax reserve on KURGIN profit:

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

Normal specialist client layer:

```text
jeweler_margin_per_ct =
jeweler_fixed_margin_usd_per_ct
+ specialist_purchase_per_ct × jeweler_variable_margin_percent / 100

specialist_client_display_per_ct =
specialist_purchase_per_ct + jeweler_margin_per_ct
```

---

## 8. Score handling rules: Index coefficient layer vs Sale pricing layer

KURGIN Score is used in two different layers. These rules do not conflict because they do not control the same part of the price.

### A. Index / score coefficient layer

This layer controls quality-adjusted cost / index uplift through `effective_kurgin_score_coefficient`.

```text
if KURGIN Score <= 80:
    effective_kurgin_score_coefficient may be 1.0
    no premium index uplift may apply

if KURGIN Score > 80:
    score coefficient / index uplift may apply
```

This layer affects:

```text
score_adjusted_cost_per_ct = base_cost_per_ct × effective_kurgin_score_coefficient
```

It does not directly define specialist sale spread, client display spread, public spread, checkout status or public catalog labels.

### B. Sale price specialist / client / public layer

This layer controls how the three sale prices are separated after specialist purchase price is calculated.

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

For this low-score fixed sale rule, do not apply:

- `jeweler_fixed_margin_usd_per_ct`;
- `jeweler_variable_margin_percent`;
- dynamic specialist margin;
- score margin modifier.

### C. Layer separation rule

```text
Index coefficient layer controls effective_kurgin_score_coefficient.
Sale pricing layer controls specialist/client/public spread.
```

Therefore:

```text
KURGIN Score <= 80 may mean no premium index uplift.
KURGIN Score < 80 may also trigger fixed specialist sale spread for Round main/large stones.
```

These are separate rules. The first rule controls index / quality coefficient. The second rule controls sale price spread.

### D. Round main / large without Score

```text
if section in ["main", "large"]
and shape = Round
and KURGIN Score is missing:
    price_status = blocked
    error = round_score_required
    score_status = round_score_required
```

### E. Non-Round main / large without Score

```text
if section in ["main", "large"]
and shape != Round
and KURGIN Score is missing:
    effective_kurgin_score_coefficient = 1.0
    score_status = non_round_score_not_required
    specialist_client_mode_status = normal_non_round_score_not_required
    not blocked
```

### F. Round main / large with Score >= 80

```text
if section in ["main", "large"]
and shape = Round
and KURGIN Score >= 80:
    specialist_client_mode_status = normal
    use normal v0.2-lite formula
```

`KURGIN Score = 80.00` is normal sale pricing path, not low-score fixed sale path.

### G. Out of current v0.2-lite scope

```text
if section not in ["main", "large"]:
    price_status = blocked / needs_review
    error_or_warning = section_outside_v02_lite_scope
```

---

## 9. Three final prices

```text
specialist_purchase_price_rub
<
specialist_client_display_price_rub
<
public_price_rub
```

Definitions:

```text
specialist_purchase_price_rub = price that the verified specialist pays KURGIN
specialist_client_display_price_rub = price that the specialist may show to their client
public_price_rub = price for an ordinary public-site buyer
```

These prices must remain separate fields.

Ordinary public catalog must not show:

- `low_score_fixed_rule`;
- specialist margin;
- specialist client display price;
- specialist purchase price.

This information is for future specialist cabinet / professional mode only.

---

## 10. After-tax no-loss guard

```text
gross_margin_rub = final_price_rub - protected_cost_rub

tax_reserve_rub = gross_margin_rub × tax_on_profit_percent / 100

net_profit_after_tax_rub = gross_margin_rub - tax_reserve_rub
```

```text
if net_profit_after_tax_rub <= 0:
    price_status = blocked
    error = after_tax_profit_negative
```

---

## 11. Minimum net profit guard

```text
minimum_net_profit_required_rub =
max(
  minimum_net_profit_fixed_rub,
  protected_cost_rub × minimum_net_profit_percent_by_tier / 100
)
```

```text
if net_profit_after_tax_rub < minimum_net_profit_required_rub:
    price_status = needs_review
    warning = after_tax_profit_below_minimum
```

---

## 12. Legacy score margin modifier

Legacy score margin modifier is historical design input only. It must not override the low-score fixed sale rule.

For `Round main/large KURGIN Score < 80`, low-score fixed specialist sale rule overrides dynamic specialist margin and score margin modifier.

---

## 13. Future fields

```text
formula_version
pricing_run_id
pricing_run_timestamp
contract_date
contract_fx_rate_source
contract_fx_rate_rub_per_invoice_currency
specialist_client_mode_status
low_score_jeweler_margin_rub
low_score_public_spread_rub
effective_kurgin_score_coefficient
score_status
```

---

## 14. What not to do

Do not:

- confirm current calculated prices;
- run mass confirmation;
- publish priced catalog;
- enable checkout;
- create roles;
- create specialist cabinet;
- create client mode;
- bypass FX guard;
- bypass after-tax guard;
- bypass minimum profit guard;
- show low-score specialist labels on ordinary public catalog;
- treat Pricing Preview as final safe public price.

---

## 15. Final control statement

```text
No price confirmed by this document.
No catalog published by this document.
No checkout enabled by this document.
No low-score specialist mode shown on public catalog by this document.
```
