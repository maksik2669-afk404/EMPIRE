---
name: fulfillment-model
description: Develop a marketplace logistics strategy: comparison and selection of FBO, FBS, DBS models.
argument-hint: [product parameters, delivery restrictions and marketplace goals]
allowed-tools: Read, Write
preset: marketplace
lifecycle: any
business-model: any
domain: marketplace
stage: any
output-artifact: document
---

# Marketplace logistics models (fulfillment-model)

Compare and design the optimal mix of logistics models (FBO - sales from the marketplace warehouse, FBS - seller's warehouse + marketplace delivery, DBS - delivery by the seller).

## Process
1. **Analyze product categories.** Weight, dimensions, turnover, temperature conditions.
2. **Make a financial comparison of the models.** The impact of delivery speed on product card conversion.
3. **Formulate the rules for choosing a model for sellers.**
4. **Save the output** in the current working directory as `fulfillment-model-[context].md`.

## Output Format
```
## Logistics Model Specification: [Product]
- **FBO (platform warehouse) model:** for high-turnover goods (top 20% SKU).
- **FBS model (seller's warehouse):** for low-volume and large-size goods.
- **Impact on conversion:** delivery from a platform warehouse (FBO) increases card conversion by 15-20% due to fast delivery.
```

## Metrics (Marketplace / Classifieds)

### Outcome metric
**successful transactions/matches, GMV with healthy take rate, liquidity.** Main result and value.

### Input metrics
**supply coverage, demand coverage, search success, time-to-first-match, reply rate.** Controlled outcome levers.

### Guardrails
**seller margin, dispute rate, cancellation rate, fraud rate, leakage/disintermediation.** What cannot be worsened.

### Diagnostic metrics
**liquidity by geo/category/price/time, supply quality, buyer conversion, seller activation.** Where to look for the reason.

### Instrumentation
**buyer_id, seller_id, listing_id, category, geo, search_id, contact/match/transaction events.** What data is needed.

### Decision rules
- Ship/Iterate/Kill

### Universal Metric Rule
If you are proposing a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How ​​often do we watch it?**
3. **What events count it?**
4. **What is the decision threshold?**
5. **How ​​can it be spoiled or screwed up?**

## Rules

- Write in English.
