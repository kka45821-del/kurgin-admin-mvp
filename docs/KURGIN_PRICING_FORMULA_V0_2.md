# KURGIN Pricing Formula v0.2

**Project:** KURGIN  
**Repository:** `kka45821-del/kurgin-admin-mvp`  
**Document:** Pricing Formula v0.2  
**Status:** documentation-only design package  
**Scope:** batch-based / multi-currency / after-tax protected pricing model  

---

## 0. Scope lock

This document is a pricing-formula design document.

It does **not**:

- write code;
- change Pricing Engine implementation;
- confirm prices;
- publish `catalog.json`;
- change the public site;
- launch mass confirmation;
- enable checkout;
- enable reserve;
- enable sold status;
- create roles;
- create specialist cabinet;
- create client mode.

Current calculated prices must not be treated as final public prices.

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
- low-score fixed specialist mode for `main` / `large` stones below KURGIN Score 80.

This document is a design source for future and current v0.2-lite code packages. It does not approve commercial use by itself.

---

## 2. Universal batch-based pricing model

KURGIN pricing must not be tied to a single supplier shipment or one fixed purchasing pattern.

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

The formula must work for future batches with INR, USD, RUB, different suppliers, different contract dates, different fixed expenses and supplement invoices.

Batch data is a pricing input. It is not public catalog copy.

---

## 3. First real INR batch reference

The first expected real batch may be used as a reference scenario.

```text
contract_date = 2026-05-10
fx_rate_source = CBR RF on contract date
invoice_currency = INR
supplier_settlement_currency = INR
kurgin_payment_currency = RUB
public_display_currency = RUB
customs_percent = 40
batch_fixed_expenses_rub = 80000
batch_fixed_expenses_note = air freight + broker
```

Important distinction:

```text
80000 RUB = air freight + broker only
customs is separate from 80000 RUB
```

Customs must be calculated separately from the invoice / purchase cost.

The 20 extra stones from the USD file are a supplement invoice / pending invoice in the same shipment until purchase cost is locked.

---

## 4. Multi-currency purchase and FX risk guard

Currency layers:

```text
supplier_price_currency
supplier_settlement_currency
kurgin_payment_currency = RUB
public_display_currency = RUB
```

Required stone / purchase-cost fields:

```text
base_purchase_price_per_ct_supplier_currency
base_purchase_total_supplier_currency
fx_rate_rub_per_supplier_currency
fx_rate_source
fx_rate_timestamp
fx_buffer_percent
fx_buffer_rub
projected_purchase_total_rub
actual_purchase_total_rub
fx_protected_purchase_cost_rub
purchase_cost_lock_status
purchase_cost_rub
```

Allowed `purchase_cost_lock_status` values:

```text
projected
locked
paid
pending_invoice_same_shipment
needs_review
```

If the purchase is paid:

```text
purchase_cost_rub = actual_purchase_total_rub
```

If the purchase is not paid:

```text
projected_purchase_total_rub =
base_purchase_total_supplier_currency × fx_rate_rub_per_supplier_currency

fx_buffer_rub =
projected_purchase_total_rub × fx_buffer_percent / 100

fx_protected_purchase_cost_rub =
projected_purchase_total_rub + fx_buffer_rub

purchase_cost_rub =
fx_protected_purchase_cost_rub
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

## 5. Batch fixed expenses allocation

Fixed batch expenses must not be divided equally by the number of stones.

Use value-share allocation:

```text
stone_share =
stone_purchase_total_currency / total_batch_purchase_currency

allocated_batch_expense_rub =
batch_fixed_expenses_rub × stone_share
```

For supplement invoices in the same shipment:

```text
full_shipment_total_currency =
original_invoice_total_currency + supplement_invoice_total_currency

stone_share =
stone_purchase_total_currency / full_shipment_total_currency

allocated_batch_expense_rub =
batch_fixed_expenses_rub × stone_share
```

This keeps batch expense allocation proportional to value, not to item count.

---

## 6. Customs

Customs must be calculated separately from air freight, broker fees, fixed batch expenses, margin and public price.

```text
customs_rub =
purchase_total_rub × customs_percent / 100
```

For the first reference batch:

```text
customs_percent = 40
```

Customs is separate from air freight, broker, batch fixed expenses, margins and public price.

---

## 7. Pending supplement stones

Required status:

```text
purchase_status = pending_invoice_same_shipment
```

Rules for pending supplement stones:

- they may be shown only as `request_price` if otherwise allowed by catalog visibility rules;
- they must not enter a confirmed priced batch;
- public price must not be confirmed;
- checkout / reserve / sold must not be enabled;
- after supplement invoice / purchase cost lock, they may enter full shipment recalculation.

Pending supplement stones cannot bypass FX guard, after-tax guard or minimum profit guard.

---

## 8. Improved per-carat formula

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
base_cost_per_ct × kurgin_score_coefficient
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

Specialist purchase price layer:

```text
specialist_purchase_per_ct =
score_adjusted_cost_per_ct
+ kurgin_net_margin_target_per_ct
+ kurgin_tax_reserve_per_ct
```

Jeweler / specialist client layer for normal path:

```text
jeweler_margin_per_ct =
jeweler_fixed_margin_usd_per_ct
+ specialist_purchase_per_ct × jeweler_variable_margin_percent / 100

specialist_client_display_per_ct =
specialist_purchase_per_ct + jeweler_margin_per_ct
```

RUB prices:

```text
specialist_purchase_price_rub =
ceil_to_1000(specialist_purchase_per_ct × carat × usd_rub_rate)

specialist_client_display_price_rub =
ceil_to_1000(specialist_client_display_per_ct × carat × usd_rub_rate)
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
KURGIN Score coefficient should apply to the cost layer,
not to the final public price.
```

---

## 9. Low-score fixed specialist rule

For low-score stones in active scope, ordinary dynamic jeweler / specialist margin must not apply.

Rule:

```text
if section in ["main", "large"] and KURGIN Score < 80:
    specialist_client_mode_status = low_score_fixed_rule
    specialist_client_display_price_rub = specialist_purchase_price_rub + 2000
    public_price_rub = specialist_client_display_price_rub + 2000
```

Normal path:

```text
if section in ["main", "large"] and KURGIN Score >= 80:
    specialist_client_mode_status = normal
    use normal v0.2-lite formula
```

Out-of-scope path:

```text
if section not in ["main", "large"]:
    v0.2-lite specialist/public pricing is out of current scope
```

For `KURGIN Score < 80`, do **not** apply:

- `jeweler_fixed_margin_usd_per_ct`;
- `jeweler_variable_margin_percent`;
- dynamic specialist margin;
- score margin modifier.

Ordinary public catalog must not show:

- `low_score_fixed_rule`;
- specialist margin;
- specialist client display price;
- specialist purchase price.

This information is for future specialist cabinet / professional mode only.

---

## 10. KURGIN Score logic

KURGIN Score logic in Pricing Formula v0.2:

```text
if KURGIN Score <= 80:
    kurgin_score_coefficient may be 1.0

if KURGIN Score > 80:
    score coefficient may apply
```

The score coefficient affects:

```text
score_adjusted_cost_per_ct
```

It does not run inside public card display.

Invoice / packing list may not contain KURGIN Score.

KURGIN Score may be calculated separately before purchase.

A priced batch requires KURGIN Score to be available in admin data where the pricing model requires it.

Hard rule:

```text
Round main/large without KURGIN Score cannot be confirmed as a priced stone.
```

---

## 11. Three final prices

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

---

## 12. After-tax no-loss guard

No confirmed price can be approved if projected net profit after tax is negative.

```text
gross_margin_rub = final_price_rub - protected_cost_rub

tax_reserve_rub = gross_margin_rub × tax_on_profit_percent / 100

net_profit_after_tax_rub = gross_margin_rub - tax_reserve_rub

tax_on_profit_percent = 15
```

Hard rule:

```text
if net_profit_after_tax_rub <= 0:
    price_status = blocked
    error = after_tax_profit_negative
```

Soft rule:

```text
if net_profit_after_tax_rub < minimum_net_profit_rub:
    price_status = needs_review
    warning = after_tax_profit_below_minimum
```

---

## 13. Minimum net profit guard

```text
minimum_net_profit_required_rub =
max(
  minimum_net_profit_fixed_rub,
  protected_cost_rub × minimum_net_profit_percent_by_tier / 100
)
```

Rule:

```text
if net_profit_after_tax_rub < minimum_net_profit_required_rub:
    price_status = needs_review
    warning = after_tax_profit_below_minimum

if net_profit_after_tax_rub <= 0:
    price_status = blocked
    error = after_tax_profit_negative
```

Minimum profit guard must run after FX protection and after tax reserve calculation.

---

## 14. Legacy score margin modifier

The earlier v0.2 draft fixed a soft dynamic margin concept.

```text
base_specialist_margin_percent = margin percent from cost tier
score_margin_modifier = modifier from KURGIN Score tier
final_specialist_margin_percent = base_specialist_margin_percent × score_margin_modifier
```

Score margin modifier table:

| KURGIN Score tier | score_margin_modifier |
|---:|---:|
| 0–50 | 0.50 |
| 50–70 | 0.65 |
| 70–80 | 0.80 |
| 80–90 | 1.00 |
| 90–95 | 1.10 |
| 95–98.5 | 1.20 |
| 98.5–100 | 1.30 |

This concept remains as historical design input, but the improved v0.2 formula should prefer applying score logic to the cost layer rather than multiplying the final public price.

Control rule:

```text
Score coefficient changes quality-adjusted cost.
Score margin modifier may affect specialist economics only if separately approved.
Do not let both layers inflate price aggressively at the same time.
```

For `KURGIN Score < 80`, low-score fixed specialist rule overrides dynamic specialist margin and score margin modifier.

---

## 15. Universal future fields

```text
air_freight_fixed_rub
insurance_percent
broker_fee_rub
customs_clearance_fee_rub
other_expenses_fixed_rub
batch_expense_allocation_method
formula_version
pricing_run_id
pricing_run_timestamp
contract_date
contract_fx_rate_source
contract_fx_rate_rub_per_invoice_currency
specialist_client_mode_status
```

Additional fields may be added only if they preserve:

- calculated vs confirmed separation;
- FX guard;
- after-tax guard;
- minimum profit guard;
- request_price vs checkout separation;
- public / specialist surface separation.

---

## 16. What not to do

Do not do any of the following from this document:

- write code without separate implementation scope;
- confirm current calculated prices;
- run mass confirmation;
- publish priced catalog;
- enable checkout;
- enable reserve;
- enable sold;
- create roles;
- create specialist cabinet;
- create client mode;
- include `pending_invoice_same_shipment` stones in priced batch before purchase cost lock;
- bypass FX guard;
- bypass after-tax guard;
- bypass minimum profit guard;
- show low-score specialist labels on ordinary public catalog;
- treat current early Pricing Preview as final safe public price.

---

## 17. MVP recommendation

Until Pricing Formula v0.2 or an approved v0.2-lite is implemented and reviewed, current calculated prices must not be treated as final public prices.

Recommended order:

```text
1. Fix Pricing Formula v0.2.
2. Approve v0.2-lite for nearest controlled test.
3. Then change Pricing Engine code.
4. Then run new preview.
5. Then select 5 controlled stones.
6. Then run confirmation review.
7. Then limited mass confirmation if allowed.
8. Then publication.
9. Then public-site priced display check.
```

No step may skip FX guard, after-tax guard, section scope guard, low-score rule or minimum net profit guard.

---

## 18. Final control statement

Pricing Formula v0.2 defines a safer future pricing model.

It does not launch commercial pricing.

```text
No price confirmed by this document.
No catalog published by this document.
No checkout enabled by this document.
No low-score specialist mode shown on public catalog by this document.
```
