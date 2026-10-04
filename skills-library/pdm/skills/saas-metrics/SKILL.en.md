---
name: saas-metrics
description: Analyze and diagnose the metrics of a B2B SaaS product. Input — revenue and churn indicators, output — a structured audit: MRR/ARR, NRR/GRR, LTV/CAC, Logo Churn vs. Revenue Churn, and an action plan to improve the metrics.
argument-hint: [SaaS revenue, churn, or unit economics metrics]
allowed-tools: Read, Write
preset: saas
lifecycle: any
business-model: any
domain: saas
stage: any
output-artifact: document
---

# Diagnostics of SaaS Metrics (saas-metrics)

Conduct a comprehensive health audit of a B2B/B2C SaaS product based on financial and cohort metrics. The skill helps the product manager calculate key subscription metrics, break down churn by revenue and customers, evaluate the effectiveness of expansion (upgrades), and suggest specific product levers for growing NRR (Net Revenue Retention).

## Process

1. **Collect financial indicators.**
   - *MRR (Monthly Recurring Revenue) & ARR (Annual Recurring Revenue).*
- *New MRR* (revenue from new customers), *Expansion MRR* (revenue from upgrades of current customers), *Contraction MRR* (revenue from downgrades), *Churned MRR* (losses from lost customers).
2. **Calculate the key revenue retention metrics.**
- **Net Revenue Retention (NRR):** `(Starting MRR + Expansion - Contraction - Churn) / Starting MRR`. Shows whether revenue is growing on the current base without taking new acquisitions into account (target value > 110-120%).
- **Gross Revenue Retention (GRR):** `(Starting MRR - Contraction - Churn) / Starting MRR`. Shows the stability of the base without taking upgrades into account (cannot exceed 100%, target > 85-90%).
3. **Divide attrition into qualitative and quantitative.**
- *Logo Churn (customer churn):* % of companies that canceled their subscription.
- *Revenue Churn:* % of lost money. If Logo Churn is high but Revenue Churn is low — the product loses small customers but retains large ones (Enterprise).
4. **Formulate product growth levers.** How to fix downturns (change onboarding logic, review pricing limits, dunning processes in case of card failures).
5. **Save the output** in the current working directory as `saas-metrics-audit-[product-name].md`.

## Output Format

```
## SaaS Product Audit: [Product Name]

### 1. Health map of SaaS metrics
| Metric | Value | Assessment (Healthy / Risk / Critical) | Industry Benchmark |
|---------|----------|-----------------------------------|---------------------|
| **ARR (Annual Recurring Revenue)** | [X] RUB | — | — |
| **Net Revenue Retention (NRR)** | [Y%] | [Assessment] | > 110% (SME) / > 120% (Enterprise) |
| **Gross Revenue Retention (GRR)** | [Z%] | [Assessment] | > 85-90% |
| **LTV / CAC Ratio** | [Ratio] | [Assessment] | > 3 (normal) / > 5 (excellent) |
| **Logo Churn (Cohort)** | [Churn%] | [Assessment] | < 1-2% per month (Enterprise) |

### 2. MRR Change Structure (MRR Waterfall / Bridge)
Analysis of dynamics for the last period:
- **New MRR (New clients):** [+/-X] RUB.
- **Expansion MRR (Upgrades/Add-ons):** [+/-Y] rub.
- **Contraction MRR (Downgrades):** [+/-Z] RUB.
- **Churned MRR (Lost Customers):** [+/-W] rub.
- **Net MRR Growth Rate (Net Growth Rate):** [Growth%]

### 3. Churn Diagnosis: Logos vs. Money
- **Metrics behavior:** [for example, Logo Churn = 15%, Revenue Churn = 2%. This indicates high churn in the small segment (Self-serve/SME) with high stability of Enterprise accounts. The product is moving towards an Enterprise model].
- **Key churn factors (Churn Drivers):** [manual payment failures (involuntary churn), not using features in the first 30 days].

### 4. Action Plan for Improving Metrics
- **To increase NRR (Expansion):** [for example, introduce a fee for additional integrations or limit the number of projects in the basic plan].
- **To reduce Churn:** [setting up trigger instruction emails when activity drops, optimizing bank dunning scenarios for card overdue].
```

## Rules

- Do not forbid evaluating the quality of SaaS solely based on overall revenue growth. If growth occurs exclusively due to insane acquisition of new traffic through marketing while NRR < 80% — the product is a 'leaky bucket' and will quickly deflate once the channel capacity is exhausted.
- Always clearly distinguish between Logo Churn and Revenue Churn.
- Write in English.

## Metrics (SaaS)

### Outcome metric
**NRR, retained ARR/MRR, active paying accounts.** Main result and value.

### Input metrics
**activation rate, time-to-value, feature adoption, seats used, integrations connected.** Managed levers of outcome.

### Guardrails
**GRR, logo churn, support load, gross margin, implementation time.** What must not be worsened.

### Diagnostic metrics
**cohort retention by segment, churn reasons, expansion/contraction bridge, account health score.** Where to look for the reason.

### Instrumentation
**account_id, plan, seats, feature events, billing events, CRM segment.** What data is needed.

### Decision rules
- Ship / Iterate / Kill

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**