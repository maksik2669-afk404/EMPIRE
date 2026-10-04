---
name: decision-doc
description: Structure the product solution with options, trade-offs, and a clear recommendation. The input is a decision that needs to be made, the output is a short document about the decision, ready for review by stakeholders.
argument-hint: [decision to be made]
allowed-tools: Read, Write
preset: core
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Decision Document

Turn uncertainty into a structured solution. One page, clear options, clear trade-offs, and a defensible recommendation.

## Process

1. **Formulate a solution.** What exactly are we solving? Why now? What happens if you do nothing?
2. **Identify constraints.** Time, budget, technical limitations, dependencies, organizational factors.
3. **Generate options.** 2-4 realistic options. Always include "do nothing" if it's viable. Each option should be truly different, and not a variation of one idea.
4. **Evaluate each option.** Pros, cons, effort rating, level of risk and reversibility.
5. **Give a recommendation.** Choose one. Tell me why. Be explicit about what you are giving up.
6. **Decide next steps.** If approved - what happens on Day 1?
7. **Save the output** in the current working directory as `decision-doc-[context].md`.

## Output Format

```
## Solution: [Formulation of the solution in one line]

### Context
[2-3 sentences. Why is this decision important now? What caused it? What happens if there is a delay.]

### Restrictions
- [Limitation 1]
- [Limitation 2]
- [Limitation 3]

### Options

#### Option A: [Title]
[1-2 sentences description]
- **Pros:** [list]
- **Cons:** [list]
- **Effort:** [T-shirt size + calendar time]
- **Risk:** [Low/Medium/High - one sentence why]

#### Option B: [Title]
[1-2 sentences description]
- **Pros:** [list]
- **Cons:** [list]
- **Effort:** [T-shirt size + calendar time]
- **Risk:** [Low/Medium/High - one sentence why]

#### Option C: [Title] (if applicable)
[same structure]

### Comparison
| Criterion | Option A | Option B | Option C |
|----------|-----------|-----------|-----------|
| Speed ​​of getting value | [fast/medium/slow] | ... | ... |
| Impact on the user | [high/medium/low] | ... | ... |
| Effort | [S/M/L/XL] | ... | ... |
| Risk | [low/medium/high] | ... | ... |
| Reversibility | [easy/hard] | ... | ... |

### Recommendation
**Select Option [X].**
[2-3 sentences. Why does this option win? Which specific factor tips the scales.]

### What are we giving up?
[Obviously. Every choice has a price. Name it.]

### Reversibility
[Can we change course later? At what cost? When will this become irreversible?]

### Next steps (if approved)
1. [Action] - [Responsible] - [When]
2. [Action] - [Responsible] - [When]
3. [Action] - [Responsible] - [When]
```

## Rules

- Always give a recommendation. A solution document without a recommendation is just a menu. Take a position.
- “Do nothing” is a valid option. Turn it on when doing nothing is really viable, and be honest about its cost.
- The pros and cons should be specific to this decision, not general. “Quick entry to the market” is a plus only if you explain what is faster and why speed is important here.
- Never present more than 4 options. If there are more of them, the problem is not narrowed down enough.
- Reversibility is required. Irreversible decisions deserve more analysis. Reversible - faster actions.
- The “What We Give Up” section is not optional. Solutions without recognized trade-offs are not real solutions.
- Maximum one page. If the document is longer than 2 pages, there are probably two solutions. Divide.
- If the input data is too vague to generate meaningful options, ask clarifying questions. Don't make up the context.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?