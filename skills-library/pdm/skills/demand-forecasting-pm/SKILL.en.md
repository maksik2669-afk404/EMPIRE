---
name: demand-forecasting-pm
description: Develop product requirements for a Demand Forecasting system in retail.
argument-hint: [product categories and retailer data structure for demand forecasting]
allowed-tools: Read, Write
preset: retail-ops
lifecycle: any
business-model: any
domain: ecom-retail
stage: any
output-artifact: document
---

# Retail demand forecasting (demand-forecasting-pm)

Generate requirements for an ML demand forecasting system to optimize inventory in warehouses and prevent shortages (out-of-stock) or excess (overstock).

## Process
1. **Define input Features for the model.** Sales history, promotions, seasonality, holidays, weather.
2. **Set Forecast Accuracy metrics.** MAPE (Mean Absolute Percentage Error), WAPE.
3. **Describe the logic of automatic ordering (Replenishment).** How the demand forecast is transformed into an automatic order to suppliers.
4. **Save the output** in the current working directory as `demand-forecasting-pm-[context].md`.

## Output Format
```
## Demand Forecasting System Specification
- **Model input data:** sales for 3 years by day, promotional mechanic calendar, product balances.
- **Target Accuracy Metric (WAPE):** < 15% for dry grocery, < 25% for fresh category (perishable goods).
- **Fallback scenario:** if the ML model fails, the order is formed based on average sales over the last 4 weeks.
```

## Metrics (E-commerce / Retail)

### Outcome metric
**contribution margin per order, repeat purchase, paid orders.** Main result and value.

### Input metrics
**checkout conversion, add-to-cart, availability, delivery promise accuracy, promo conversion.** Managed outcome levers.

### Guardrails
**gross margin after returns, refund rate, return abuse, stockout, payment failure.** What cannot be worsened.

### Diagnostic metrics
**funnel drop-off, category, device, payment method, delivery slot, promo dependency.** Where to look for the reason.

### Instrumentation
**cart_id, order_id, SKU, inventory, payment events, return/refund reason.** What data is needed.

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
