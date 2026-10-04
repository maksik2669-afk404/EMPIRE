---
name: monetization-audit
description: Conduct an audit of the current monetization model and identify lost profits.
argument-hint: 
allowed-tools: Read, Write
preset: saas
lifecycle: any
business-model: any
domain: saas
stage: any
output-artifact: document
---

# Monetization audit (monetization-audit)



## Process

2. **Uncover non-monetizable value.** What valuable features are users actively using but not paying for?

4. **Save the output** in the current working directory as `monetization-audit-[context].md`.

## Output Format
```
## 

- **Zones of value loss:** [where we give away for free what we are willing to pay for]
- **Hypotheses for LTV growth:** [new add-ons, transaction fees].
```

## Metrics (SaaS)

### Outcome metric


### Input metrics
**activation rate, time-to-value, feature adoption, seats used, integrations connected.** Controlled outcome levers.

### 
**GRR, logo churn, support load, gross margin, implementation time.** What cannot be worsened.

### Diagnostic metrics
**cohort retention by segment, churn reasons, expansion/contraction bridge, account health score.** Where to look for the reason.

### 
**account_id, plan, seats, feature events, billing events, CRM segment.** What data is needed.

### Decision rules
- Ship/Iterate/Kill

### Universal Metric Rule
If you are proposing a metric, answer 5 questions:

2. **How ​​often do we watch it?**
3. **What events count it?**

5. **How ​​can it be spoiled or screwed up?**

## Rules

- Write in English.
