---
name: product-health-review
description: Conduct a CPO-level product health diagnosis based on users, metrics, economics, delivery, risks, and strategy. The output — a health scorecard, red zones, root causes, and an action plan for 30/60/90 days.
argument-hint: [product description, stage, key metrics and issues]
allowed-tools: Read, Write
preset: strategy
lifecycle: measure,strategy,operations
business-model: any
domain: any
stage: mvp,pre-pmf,pmf,scale,mature,turnaround
output-artifact: product-health-review
---

# Product Health Review

Conduct product diagnostics not by a single metric, but as a system: user value, retention, economics, delivery quality, operational risks, team, and strategic focus.

## Process

1. Determine the stage of the product and the business model.
2. Collect outcome/input/guardrail metrics.
3. Check retention and repeat behavior.
4. Check the unit economics and growth channels.
5. Check the product quality: reliability, support, UX, complaints.
6. Find the root causes of the red zones.
7. Form a 30/60/90 day action plan.
8. **Save the output** in the current working directory as `product-health-review-[context].md`.

## Output Format

```md
## Product Health Review: [Product]

### 1. Executive Summary
- **Overall status:** Healthy / Watch / Critical
- **Main red zone:**
- **Main recommendation:**

### 2. Health Scorecard
| Area | Status | Metrics | Conclusion |
|---|---|---|---|
| User Value | Green/Yellow/Red | | |
| Activation | | | |
| Retention | | | |
| Monetization | | | |
| Unit Economics | | | |
| Growth | | | |
| Reliability/Ops | | | |
| Strategy Fit | | | |

### 3. Root Causes
### 4. Risks
### 5. 30/60/90 Plan
### 6. Decisions Needed from Management
```

## Rules

- Don't declare a product healthy just because of revenue growth. Growth can be bought with CAC if retention is leaky.
- Separate symptoms and root causes.
- If there is no data, explicitly list the missing instrumentation.
- Write in English.

## Metrics

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**