---
name: okr-writer
description: Translate business goals into structured OKRs with measurable Key Results, associated initiatives, alignment checks and anti-goals. The input is a strategic priority, the output is ready-to-use OKRs.
argument-hint: 
allowed-tools: Read, Write
preset: strategy
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Writing OKRs

Turn vague business goals into clear, measurable OKRs. No vanity metrics, no low goals, no goals that read like tasks.

## Process

1. **Understand the goal.** Understand what the business is trying to achieve and the time horizon (default: quarter).

3. **Define Key Results.** 3-5 measurable results. Everyone must have a specific number. They answer “how will we know when we got there?”
4. **Link to initiatives.** What activities will drive Key Results? These are the actual work items.

6. **Identify anti-goals.** What is clearly outside the scope? This prevents scope expansion and uncoordinated efforts.
7. **Save the output** in the current working directory as `okr-writer-[context].md`.

## Output Format

```
## OKR: [Quarter/Period]

### Objective
[One sentence. Qualitative. Inspiring. Clear direction. Limited time.]

### 

|---|-----------|-----------------|------|-------------|
| KR1 | [Specific measurable outcome] | [current] | [target] | [data source] |

| KR3 | [Specific measurable outcome] | [current] | [target] | [data source] |
| KR4 | [Specific measurable outcome] | [current] | [target] | [data source] |

### Initiatives
| Initiative | Moves KR | Responsible | Effort |
|-----------|----------|--------------|--------|
| [What will we do] | KR1, KR2 | [team/person] | [S/M/L] |
| [What will we do] | KR2 | [team/person] | [S/M/L] |
| [What will we do] | KR3, KR4 | [team/person] | [S/M/L] |

### Alignment

- **How ​​is it connected:** [One sentence - cause-and-effect relationship]

### Anti-targets
- [What this Objective is NOT]
- [What we will definitely NOT be doing this quarter]

```

## Rules


- Key Results must have numbers. “Improve retention” is not KR. “Increase 30-day retention from 45% to 55%” - KR.
- Goals should be ambitious, but not crazy. A good KR has approximately a 70% chance of achievement. If you are 100% sure, the goal is too low.
- Each KR must indicate how it will be measured and where the data comes from. If you can't measure it, it's not KR.
- Maximum 3-5 Key Results. More than 5 means Objective is too wide - strip it.
- Initiatives are NOT Key Results. Initiatives - what you do. Key Results - what happens as a result.
- Anti-goals are required. Every OKR implicitly deprivitizes something - name it explicitly to prevent drift.
- If the input goal is too vague (“grow the business”), ask for specifics: what segment, what metric, what time horizon.
- Do not write OKRs for more than one Objective at a time unless explicitly asked. Focus is more important than breadth.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?