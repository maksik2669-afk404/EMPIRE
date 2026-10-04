---
name: business-model-canvas
description: Create a strong and detailed Business Model Canvas. Describe the segments, value, channels, relationships, revenue streams, cost structure, key resources, and risks. The output — a BMC with a metrics tree and a decision (proceed / narrow / pivot / kill).
argument-hint: [description of idea or business]
allowed-tools: Read, Write
preset: strategy
lifecycle: strategy
business-model: any
domain: generic
stage: idea,mvp,pre-pmf
output-artifact: business-model-canvas
---
# Business Model Canvas

## When to use
- When developing a new idea before creating a full-fledged business case.
- To audit the current business model to find bottlenecks in costs or acquisition channels.
- When you need to decompose a complex business model (marketplace, ecosystem) into understandable blocks.

## When NOT to use
- If a solution is needed for only one small feature.
- When the product is already at a mature stage and does not change its business model.

## Input data
- **Required:** Main idea or current product.
- **Desirable:** Who is the target audience, what exactly will they pay for.
- **If there is no data, what questions to ask:** Who are the key competitors? What is your unfair advantage?

## Process
1. **Fill out 9 blocks of the Business Model Canvas:**
- Customer Segments (customer segments)
- Value Proposition (value proposition)
- Channels (channels of attraction and distribution)
- Customer Relationships (relationships with clients)
- Revenue Streams (revenue streams)
- Key Resources
- Key Activities
- Key Partners (key partners)
- Cost Structure
2. **Explicit Assumptions:** What are we not sure about? What should you check first?
3. **Make a list of Top Risks:** What could kill this model?
4. **Build a Metric Tree:** How the model will be measured at the top level.
5. **Formulate a decision:** proceed / narrow / pivot / kill.
6. **Save the output** in your current working directory as `business-model-canvas-[context].md`.

## Output Format

```md
## Business Model Canvas: [Title]

### 1. 9 BMC blocks
| Block | Description |
|---|---|
| Customer Segments | |
| Value Proposition | |
| Channels | |
| Customer Relationships| |
| Revenue Streams | |
| Key Resources | |
| Key Activities | |
| Key Partners | |
| Cost Structure | |

### 2. Key assumptions
- [assumption 1]
- [assumption 2]

### 3. Top risks
- [risk 1]
- [risk 2]

### 4. Metric tree
- **North Star:** [main metric]
- **Inputs:** [growth drivers]
- **Guardrails:** [restrictions]

### 5. Final decision
**Recommendation:** [proceed / narrow / pivot / kill]
**Why:** [rationale]
```

## Rules
- Avoid common words. Instead of “marketing” write “performance marketing in social networks”, instead of “IT costs” - “development of LLM infrastructure”.
- Value Proposition must respond to a specific pain point of the segment.
- Explicitly link Customer Segments and Revenue Streams.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?