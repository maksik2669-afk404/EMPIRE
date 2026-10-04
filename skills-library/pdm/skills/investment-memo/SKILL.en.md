---
name: investment-memo
description: Prepare an investment case for a product initiative for the CEO/CFO/board: rate size, expected effect, economics, risks, milestones and conditions for continued financing.
argument-hint: [initiative, budget, expected effect and deadline]
allowed-tools: Read, Write
preset: strategy
lifecycle: strategy,measure
business-model: any
domain: any
stage: mvp,pre-pmf,pmf,scale
output-artifact: investment-memo
---

# Investment Memo

Prepare a short document for deciding whether to invest in a product initiative, how much resources to allocate, what milestones should confirm the bid and when to stop funding.

## Output Format

```md
## Investment Memo: [Initiative]

### 1. Recommendation
- **Solution:** Invest / Pilot / Defer / Kill
- **Request:** [budget, people, deadline]
- **Expected effect:** [metric, money, term]

### 2. Strategic Fit
### 
### 4. Economics
| Metric | Meaning | Assumption |
|---|---:|---|

### 5. Milestones and Funding Gates
| Gate | Deadline | What must be proven | Solution |
|---|---|---|---|

### 6. Risks and Mitigations
### 7. Alternatives
### 
```

## Rules

- Always show funding gates. Money should be released as uncertainty decreases.

- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?