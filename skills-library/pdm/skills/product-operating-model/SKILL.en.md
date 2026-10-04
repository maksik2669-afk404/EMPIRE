---
name: product-operating-model
description: Design an operating model of a product organization: roles, decision rights, rituals, metrics, cadence, governance and the connection between strategy and delivery. The output is a product management model for the team/direction.
argument-hint: [description of product organization, teams, management problems]
allowed-tools: Read, Write
preset: strategy
lifecycle: operations,strategy
business-model: any
domain: any
stage: scale,mature,turnaround
output-artifact: product-operating-model
---

# Product Operating Model

Design how the product organization makes decisions, connects strategy to the roadmap, manages metrics and escalates trade-offs.

## Output Format

```md
## Product Operating Model: [Organization]

### 
### 2.Product Principles
### 3. Roles and Decision Rights
| Decision | Owner | Contributors | Approver | Cadence |
|---|---|---|---|---|

### 4. Rituals and Cadence
### 5. Metrics Governance
### 6. Portfolio / Roadmap Governance
### 7. Escalation Rules
### 8. Implementation Plan
```

## Rules

- Don't design rituals without decision rights.
- If it is unclear who makes the decision, the operating model does not work.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?