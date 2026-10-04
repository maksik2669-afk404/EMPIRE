---
name: product-strategy
description: Formulate a product strategy: target market, ICP, user value, strategic bids, metrics, trade-offs and rejection criteria. The output is a short strategy doc that links the user problem, business model, roadmap and measurable results.
argument-hint: 
allowed-tools: Read, Write
preset: strategy
lifecycle: strategy
business-model: any
domain: any
stage: idea,mvp,pre-pmf,pmf,scale,mature,turnaround
output-artifact: product-strategy-doc
---

# 

Formulate a product strategy as a set of conscious choices: where to play, for whom to create value, how to win, how to measure progress, and what to abandon.

## Process




4. **Describe business model fit.** How value turns into money and why economics can converge.
5. **Create 3-5 strategic bets.** Not a list of features, but bets with hypotheses.



9. **Save the output** in the current working directory as `product-strategy-[context].md`.

## Output Format

```md
## 

### 1. Strategy on a Page
- **Where we play:** [market/segment/geo]
- **For whom:** [ICP]

- **Business model:** [how we earn]
- **Main bet:** [the most important hypothesis]
- **North Star:** [value metric]

### 2. Context and constraints
### 3. Target Segment and Wedge
### 4. Value Proposition
### 5. Business Model Fit
### 6. Strategic Bets
| Bet | Hypothesis | Metric | Evidence | Kill criteria |
|---|---|---|---|---|

### 7. Metrics Tree
- **North Star:**
- **Input metrics:**
- **Guardrails:**
- **Diagnostics:**

### 8. Trade-offs
- Let's do:
- We do not do:
- Why:

### 9. Roadmap Themes
### 10. Review Cadence
```

## Rules

- Strategy is a choice. If a document is compatible with all segments and all features, it is not a strategy.
- Don't call a roadmap a strategy. The roadmap should flow from strategic bets.
- Each bid must have a kill criteria.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?