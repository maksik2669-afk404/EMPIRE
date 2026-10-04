---
name: risk-heatmap
description: Build a risk heat map for a product, initiative, or business model: market, operational, financial, tech, regulatory, brand risks; probability × impact; trigger signals; mitigations; owners.
argument-hint: [description of the initiative, product, or launch]
allowed-tools: Read, Write
preset: fintech
lifecycle: strategy,operations,measure
business-model: any
domain: any
stage: idea,mvp,pre-pmf,pmf,scale
output-artifact: risk-heatmap
---

# Risk Heat Map

Systematically break down the product risks and turn them into manageable trigger signals, mitigations, and owners.

## Output Format

```md
## Risk Heat Map: [Initiative]

### 1. Summary
- Red zone:
- Orange zone:
- The main early warning signal:

### 2. Risk Register
| Risk | Category | Probability | Impact | Trigger signal | Mitigation | Owner |
|---|---|---|---|---|---|---|

### 3. Priority Actions
1. Critical:
2. High:
3. Watch:

### 4. Review Cadence
```

## Rules

- Don't limit yourself to the list of risks. Be sure to also add the trigger signal and owner.
- Risk without mitigation is just anxiety.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?