---
name: hypothesis-tree
description: Build a tree of product hypotheses (Hypothesis Tree) to achieve a business goal.
argument-hint: [the main business goal of the company or product]
allowed-tools: Read, Write
preset: discovery
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Hypothesis-tree

Build a structured Hypothesis Tree to decompose a global business goal into specific product bets and experiments.

## Process
1. **Fix a business goal (KPI/OKR).** (For example: increase revenue by 20% for the quarter).
2. **Decompose into mathematical drivers.** `Revenue = Traffic × Conversion × Average Receipt`.
3. **Formulate product bets (Bets) for each driver.**
4. **Describe hypotheses and tests.**
5. **Save the output** in the current working directory as `hypothesis-tree-[context].md`.

## Output Format
```
## Hypothesis tree: [Business goal]

### 1. Business goal (Core Goal)
- **Revenue growth in the individual housing construction sector by +25% for Q3.**

### 2. Decomposition by drivers
- **Driver 1: Increase in conversion from application to escrow issue (CR)**
- *Rate:* Automation of Rosreestr verification.
- **Hypothesis 1.1:** If we connect SMEV for automatic transaction verification, the approval time will decrease from 5 days to 1 day, which will increase CR by 4%.
```


## Rules

- Write in English.
## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?