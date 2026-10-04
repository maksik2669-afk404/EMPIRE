---
name: funnel-analysis
description: Diagnose the decline in conversion rates along the funnel (Funnel Analysis) and prepare hypotheses for A/B tests.
argument-hint: [funnel steps and conversion data at each step]
allowed-tools: Read, Write
preset: growth
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Conversion funnel analysis (funnel-analysis)

Conduct a detailed diagnosis of the funnel (from the first visit to the target action), identify bottlenecks and propose hypotheses for optimizing conversion.

## Process
1. **Map the funnel.** Write down the conversion between each step (absolute and relative).
2. **Define the step with the maximum loss (Drop-off).**
3. **Formulate 3 UX/product hypotheses for the fall.**
4. **Suggest a plan for experiments.**
5. **Save the output** in the current working directory as `funnel-analysis-[context].md`.

## Output Format
```
## Product funnel analysis: [Context]

### 1. Funnel metrics
| Step | Action | Abs. conversion | Rel. conversion |
|---|---|---|---|
| 1 | Landing page visit | 100% | — |
| 2 | Click on registration | 45% | 45% |
| 3 | Filling in the fields | 12% | 26.6% (Critical drop) |
| 4 | Successful activation | 10% | 83.3% |

### 2. Hypotheses for the reasons for the fall at Step [X]
- **Hypothesis 1:** Card binding is required at the registration stage (high fear barrier).
- **Test plan:** Transfer the card binding to the stage of making the first transaction.
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