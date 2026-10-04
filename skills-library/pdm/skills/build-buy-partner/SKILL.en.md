---
name: build-buy-partner
description: Develop a structured justification for the decision: build it yourself, buy a ready-made solution or integrate a partner (Build / Buy / Partner).
argument-hint: [issue or function to decide build/buy/partner]
allowed-tools: Read, Write
preset: b2b
lifecycle: any
business-model: any
domain: saas
stage: any
output-artifact: document
---

# Build/Buy/Partner solution (build-buy-partner)

Design and justify the choice of implementation path for a feature or service: in-house development (Build), purchase of a SaaS/ready license (Buy) or partnership/integration (Partner). The skill helps the product calculate total cost of ownership (TCO), assess security risks, Time-to-Market and strategic fit.

## Process
1. **Assess Strategic Fit (Core vs. Context).** Is the feature a key competitive advantage? (If yes -> Build).
2. **Calculate TCO (Total Cost of Ownership) for 3 years.**
- *Build:* PHOT team, support, infrastructure, bugs.
- *Buy:* license cost, customization costs, integration.
- *Partner:* revenue share, API support costs.
3. **Evaluate Time-to-Market and risks.** Speed ​​to market versus vendor lock-in and compliance with 152-FZ.
4. **Present in the form of a table of recommendations.**
5. **Save the output** in the current working directory as `build-buy-partner-[context].md`.

## Output Format
```
## Rationale Build / Buy / Partner: [Feature name]

### 1. Strategic analysis
- **Is the feature the core of the business (Core)?** [Yes/No + Justification]
- **Time-to-Market criticality:** [How quickly you need to start]

### 2. Comparison of options (TCO & Risks)
| Criterion | Build (Build yourself) | Buy (Buy ready) | Partner (Integrate) |
|---|---|---|---|
| **Costs (3 years TCO)** | [FOT + support] | [License costs] | [Revenue share / Costa API] |
| **Launch Deadline** | [N months] | [N weeks] | [N weeks] |
| **Control and flexibility** | Full control | Dependency on vendor backlog | Joint control |
| **Key Risk** | Inflating deadlines | Vendor bankruptcy / sanctions | Weak partner SLA |

### 3. Recommendation and Action Plan
- **Recommended choice:** [Build / Buy / Partner]
- **Justification for choice:** [why this option is optimal in terms of TCO and risks].
```

## Metrics (SaaS)

### Outcome metric
**NRR, retained ARR/MRR, active paying accounts.** Main result and value.

### Input metrics
**activation rate, time-to-value, feature adoption, seats used, integrations connected.** Controlled outcome levers.

### Guardrails
**GRR, logo churn, support load, gross margin, implementation time.** What cannot be worsened.

### Diagnostic metrics
**cohort retention by segment, churn reasons, expansion/contraction bridge, account health score.** Where to look for the reason.

### Instrumentation
**account_id, plan, seats, feature events, billing events, CRM segment.** What data is needed.

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
