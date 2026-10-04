---
name: business-case
description: Prepare a CPO-grade business case for a new initiative, product or business model. The input is a product idea, market or initiative; The output is problem/background, alternatives, selected model, BMC, unit economics, roadmap, risk heat map, stakeholder communications and decision request.
argument-hint: [product or initiative idea]
allowed-tools: Read, Write
preset: strategy
lifecycle: strategy,measure
business-model: any
domain: any
stage: idea,mvp,pre-pmf,pmf,scale
output-artifact: business-case
---

# Business case of the initiative (business case)

Prepare a structured business case at the CPO/CEO/CFO level: not just describe the idea, but show why it is worth doing, what alternatives are considered, how the economics converge, what risks can kill the project and what decision is needed from stakeholders.

## When to use

- Before launching a new product, MVP, domain or business model.
- Before requesting budget, team or investment.
- When you need to choose between several models: subscription, marketplace, D2C, SaaS, enterprise, ads.
- When the idea already sounds convincing, but has not been tested by economics, risks and operational realism.

## When NOT to use

- For a small feature without a separate P&L or strategic bid.
- When there are no at least rough assumptions about the audience, price, channels and costs.
- When a short `decision-doc` is sufficient.

## Process

1. **State the problem and context.** What is happening in the market/product? Why now?
2. **Define the target segment and market.** TAM/SAM/SOM, ICP, solvency, frequency of need.
3. **Compare alternatives.** For example: do nothing, marketplace, D2C, subscription, enterprise sales, partnership.
4. **Choose a business model.** Explain why it is better than alternatives in this particular context.
5. **Compile a Business Model Canvas.** Value, segments, channels, relationships, revenue, costs, resources, activities, partners.
6. **Calculate unit economics.** ARPU/AOV, gross margin, CAC, LTV, LTV/CAC, payback, contribution margin, break-even.
7. **Describe the growth loop and retention loop.** How new users come, receive value, stay and refer others.
8. **Build a risk heat map.** Market, operational, brand/reputation, financial, tech, regulatory risks.
9. **Formulate a roadmap and resources.** Phases, team, budget, dependencies, decision gates.
10. **Give a recommendation and decision request.** What exactly needs to be approved now.
11. **Save the output** in the current working directory as `business-case-[context].md`.

## Output Format

```md
## Business Case: [Initiative Name]

### 1.Executive Summary
- **Recommendation:** [build / pilot / narrow / partner / kill]
- **Requested solution:** [budget, team, MVP launch, pilot]
- **Why now:** [1-2 sentences]
- **Main risk:** [most dangerous risk]
- **Main success metric:** [outcome metric]

### 2. Problem and context
- What has changed in the market/product/user behavior.
- What pain or opportunity has opened up.
- Why the current solution is not enough.

### 3. Segment and market
| Level | Evaluation | Assumptions |
|---|---:|---|
| TAM | [value] | [source/logic] |
| SAM | [value] | [source/logic] |
| SOM | [value] | [conservative achievable share] |

### 4. Alternatives
| Option | Pros | Cons | Why do we choose/don’t choose |
|---|---|---|---|
| Do nothing | | | |
| Option A | | | |
| Option B | | | |
| Recommended option | | | |

### 5. Business Model Canvas
| Block | Solution |
|---|---|
| Customer Segments | |
| Value Proposition | |
| Channels | |
| Customer Relationships | |
| Revenue Streams | |
| Key Resources | |
| Key Activities | |
| Key Partners | |
| Cost Structure | |

### 6. Unit Economics
| Metric | Meaning | Comment |
|---|---:|---|
| ARPU/AOV | | |
| Gross Margin | | |
| CAC | | |
| LTV | | |
| LTV/CAC | | Great usually >= 3, but depends on the model |
| CAC Payback | | |
| Contribution Margin | | |
| Break-even | | |

### 7. Metrics
- **Outcome:** [main metric]
- **Input metrics:** [what moves the outcome]
- **Guardrails:** [which cannot be made worse]
- **Diagnostics:** [what to watch if it fails]
- **Instrumentation:** [what events/data are needed]

### 8. Growth/Retention Loop
1. Acquisition: [channel/trigger]
2. Activation: [first moment of value]
3. Value delivery: [regular value]
4. Retention: [reason to return]
5. Expansion/Referral: [how LTV grows or new users come]

### 9. Risk Heat Map
| Risk | Probability | Influence | Trigger signal | Mitigation | Owner |
|---|---|---|---|---|---|
| | H/M/L | H/M/L | | | |

### 10. Roadmap and resources
| Phase | Deadline | Goal | Team/Resources | Exit criteria |
|---|---|---|---|---|
| Discovery | | | | |
| MVP | | | | |
| Launch | | | | |
| Scale | | | | |

### 11. Tenets
| Principle | Why is it critical | Where is the risk of breaking | How to check | Guardrail |
|---|---|---|---|---|

### 12. Decision Request
**I recommend:** [solution].
**Must be approved by:** [specific request].
**Decision review:** [when and by what metrics].
```

## Rules

- Always compare with alternatives. A business case without alternatives is a sale of an idea, not a management document.
- Mark all key figures as a fact, assumption or benchmark. Don't disguise assumptions as hard data.
- Unit economics must take into account margin, not just revenue.
- If LTV/CAC is good, but it is unclear where retention comes from, clearly mark this as a risk.
- Add trigger signals for risks: the team should know when the risk began to materialize.
- End the document with a specific decision request.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?