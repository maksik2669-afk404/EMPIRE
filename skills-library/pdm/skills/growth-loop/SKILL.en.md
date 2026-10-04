---
name: growth-loop
description: Design product growth loops: viral, content and paid cycles.
argument-hint: [product description for growth loop design]
allowed-tools: Read, Write
preset: growth
lifecycle: any
business-model: any
domain: saas
stage: any
output-artifact: document
---

# Designing growth loops

Replace linear acquisition channels with cyclical growth loops (Growth Loops), where user actions lead to the attraction of new users.

## Process
1. **Determine the type of loop:**
- *Viral Loop:* the user invites a friend in the process of collaboration (co-authorship, sharing of estimates).
- *Content Loop:* the user generates content -> it is indexed in SEO -> new users find it and register.
2. **Design a reinvestment step.**
3. **Save the output** in the current working directory as `growth-loop-[context].md`.

## Output Format
```
## Growth Loop Specification: [Product]

### 1. Viral loop (B2B Viral Loop)
- **Act of creation:** The developer creates an estimate in his personal account.
- **Action:** He sends a link to the estimate to the contractor for approval.
- **Activation:** The contractor registers in the system to edit the estimate. The cycle is closed (the contractor can create his own project).
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
