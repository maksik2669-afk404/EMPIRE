---
name: roadmap
description: Turn a list of priorities, features, or initiatives into a structured product roadmap. Format Now/Next/Later with dependencies, effort estimation, and strategic justification.
argument-hint: [list of features, priorities, or strategic goals]
allowed-tools: Read, Write
preset: core
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Roadmap Generator

Turn a chaotic list of features, priorities, or goals into a clear product roadmap. Not a Gantt chart — a strategic communication tool that shows what we do, in what order, and why.

## Process

1. **Parse the input data.** Parse the list of features, initiatives, or goals. Accept inline lists, embedded backlogs, or file paths.
2. **Identify strategic themes.** Group related items into 3-5 themes (for example, "Onboarding," "Monetization," "Platform Stability"). Each item should belong to a theme.
3. **Distribute by time horizons.** Place each item in Now (this quarter), Next (next quarter), or Later (future / requires validation). Base it on dependencies, effort, and strategic priority — not just urgency.
4. **Create a dependency map.** Identify elements that block or open others. Mark the elements of the critical path.
5. **Assess efforts.** T-shirt sizing: S (< 2 weeks), M (2-6 weeks), L (6-12 weeks), XL (> 12 weeks).
6. **Write a strategic rationale.** One sentence for each time horizon explaining why this sequence makes sense.
7. **Save the output** in the current working directory as `roadmap-[context].md`.

## Output Format

### Roadmap: [Product/Team/Context]
**Last update:** [date]
**Planning horizon:** [e.g., Q2-Q4 2026]
**Assumption by capacity:** [if known, for example, 1 team of 5 engineers]

---

### Strategic Topics

| Topic | Description | Key Metric |
|------|----------|-----------------|
| [topic] | [one line] | [what will shift if the topic is successful] |

---

### Now (This quarter)
**Justification:** [Why these elements are first — one sentence.]

| Priority | Item | Subject | Size | Dependencies | Status |
|-----------|---------|------|--------|-------------|--------|
| 1 | [element] | [topic] | S/M/L/XL | [blocker or 'No'] | Not started / In progress |

### Next (Next Quarter)
**Justification:** [Why these elements are second — one sentence.]

| Priority | Item | Topic | Size | Dependencies | Confidence |
|-----------|---------|------|--------|-------------|-------------|
| 1 | [item] | [topic] | S/M/L/XL | [what should come out first] | High/Medium/Low |

### Later (Future / Validation needed)
**Justification:** [Why these elements are postponed — one sentence.]

| Element | Topic | Size | Why later |
|---------|------|--------|-------------|
| [element] | [topic] | S/M/L/XL | [specific reason: need data, blocked, low priority, etc.] |

---

### Dependency Map
- [Element A] → blocks [Element B] (must exit before the start of B)
- [Element C] → opens [Element D, Element E]

### Key Compromises
- **[Compromise 1]:** [What was chosen and what was declined. Clearly.]
- **[Compromise 2]:** [What was chosen and what was declined.]

### What is NOT included in the roadmap
- [Element intentionally excluded] — Reason: [why]

## Rules

- Now/Next/Later — the default format. Do not use dates or sprints unless the user explicitly requests them.
- Each element should belong to a theme. If an element does not fit into any theme, question whether it should be on the roadmap.
- 'Later' is not a parking lot. Every item in Later must have a specific reason for postponement — not just 'low priority'.
- Dependencies must be explicit. If Element B cannot start before Element A is finished — say so.
- The section 'What is NOT included in the roadmap' is mandatory. A roadmap that refuses nothing is not a roadmap.
- Size assessments should be consistent. If two elements are both 'M', they should be approximately of the same strength.
- Don't overload Now. If there are more than 5-6 items in Now, challenge it: this is not a plan, it's a wish list.
- If the input list has no strategic context, ask what the 1-2 main goals of the team are before arranging the sequence. Order without strategy is just a list.
- Write in English.

## Metrics

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**