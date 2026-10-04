---
name: product-status-update
description: Create the structure and content of a presentation about the current product - a quarterly Product Review, a strategic update for stakeholders, or a product health report. The input is metrics and context, the output is a storyboard with data, insights and next steps.
argument-hint: [product name, period, key metrics and context]
allowed-tools: Read, Write
preset: core
lifecycle: growth
business-model: any
domain: generic
stage: any
output-artifact: document
---
## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?
## Process

1. **Specify the input data:**

- **Audience:** C-level / Stakeholders / Board of Directors / Team.
- **Period:** For what period is reporting (quarter, half-year, sprint).
- **Key metrics:** What we measure (Revenue, MAU, Retention, NPS, conversion).

2. **Use an 8-slide Product Review Framework:**
- **Slide 1: Brief summary (TL;DR).** 3-4 main points for the period: what has grown, what has not grown, the main conclusion.
- **Slide 2: Context and goals for the period.** OKR / goals for the quarter that were set - for comparison with the result.
- **Slide 3: Key metrics (Dashboard).** North Star Metric + 4-6 key KPIs with dynamics (plan vs fact, trend).
- **Slide 4: What we did (Shipped).** List of launched features/initiatives with a brief description of the impact of each.
- **Slide 5: What worked / Insights.** Top 3 conclusions from the data: what worked, what didn’t and why.

- **Slide 7: Roadmap for the next period.** Priorities and expected impact on metrics (not a list of features, but growth hypotheses).
- **Slide 8: What is needed from stakeholders.** Specific decisions / resources / priorities that are needed from the audience.

3. **For each slide, form:**

- **Data** - specific numbers with a trend and comparison with a target or a previous period.
- **Interpretation** - what does this mean for the product (not just data, but conclusion).


- Read only Action Titles - they should tell the story of the product over the period.

5. **Save the output** in the current working directory as `product-status-update-[context].md`.

## Output Format

```
## 
- **Data / Visualization:** [metrics, graphs, tables]
- **Interpretation:** [what this means]
- **Next step:** [action / conclusion]
```

## Rules and Restrictions
- Priority to data, not pretty words: each point is supported by a figure.
- The slide with metrics must show the trend (growth/decline/plateau) and plan vs actual.
- Blockers and risks are not complaints, but clear formulations with a proposed solution.
- The last slide is not 'conclusions', but 'what we need to decide/approve right now'.
- Style: directive, without emotional evaluations or evasive phrases.

## Difference from presentation-design (Pitch Deck)
This skill is for an **existing product** (Review/Update), while `presentation-design` is for defending a **new concept** from scratch (Discovery/Pitch Deck). Different structures, different audiences, different goals.

## Skill Success Metrics
- The audience understands the state of the product in 5 minutes without additional questions.
- On the slide with metrics, the trend and deviation from the plan are visible.
- The last slide contains a clear call to the audience with a specific deadline.

## Rules


- Write in English.