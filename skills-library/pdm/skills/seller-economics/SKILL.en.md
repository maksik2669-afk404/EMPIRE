---
name: seller-economics
description: Develop a unit economics and seller profitability calculator (Seller Economics) on the marketplace.
argument-hint: [marketplace commission structure, logistics and advertising]
allowed-tools: Read, Write
preset: marketplace
lifecycle: any
business-model: any
domain: marketplace
stage: any
output-artifact: document
---

# Marketplace Seller Economics (seller-economics)

Design a seller cost and profitability calculator (Seller Economics) to assess its margin taking into account all platform fees.

## Process
1. **Describe the structure of commissions.** Sales commission by category (take rate), storage fee, delivery to customer (last mile), returns processing.
2. **Calculate the seller's net margin.**
3. **Save the output** in the current working directory as `seller-economics-[context].md`.

## Output Format
```
## Seller Economy Calculator: [Product Category]
- **Retail price:** 1000 rub.
- **Platform commission (15%):** 150 RUB.
- **Logistics (delivery + storage):** 120 RUB.
- **Seller's net revenue (Net Payout):** 730 RUB.
```

## Metrics (Marketplace / Classifieds)

### Outcome metric
**successful transactions/matches, GMV with healthy take rate, liquidity.** The main result and value.

### Input metrics
**supply coverage, demand coverage, search success, time-to-first-match, reply rate.** Managed levers of outcome.

### Guardrails
**seller margin, dispute rate, cancellation rate, fraud rate, leakage/disintermediation.** What cannot be worsened.

### Diagnostic metrics
**liquidity by geo/category/price/time, supply quality, buyer conversion, seller activation.** Where to look for the reason.

### Instrumentation
**buyer_id, seller_id, listing_id, category, geo, search_id, contact/match/transaction events.** What data is needed.

### Decision rules
- Ship / Iterate / Kill

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**

## Rules

- Write in English.