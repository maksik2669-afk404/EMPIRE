---
name: user-interview-prep
description: Create a complete user research brief with hypotheses, an interview guide, and open-ended questions. Input — the research topic or hypothesis, output — a ready-to-use set for interviews.
argument-hint: [research topic or hypothesis]
allowed-tools: Read, Write
preset: discovery
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Preparation for a user interview

Create a structured research brief and interview guide that a PM can use immediately. The goal is to enter the interview with clear hypotheses, unbiased questions, and a plan to learn — not to confirm.

## Process

1. **Clarify the research objective** — Rephrase the input data as a single testable research question. If the input data is vague, sharpen it. A good research objective begins with 'To understand...' or 'To discover...' — never with 'To validate...' or 'To confirm...'.
2. **Identify assumptions** — List 3-5 hypotheses that the PM is likely bringing into this research. These are things that need to be tested, not confirmed.
3. **Design the course of the interview** — Structure a 30-minute interview with a warm-up, main research, and conclusion. Each section has a purpose and a time allocation.
4. **Write questions** — Generate open-ended, non-leading questions. Follow the principles of the 'Mom Test': ask about their life, not about your idea. Ask about the past, not about the hypothetical future.
5. **Add observation notes** — Note what to pay attention to besides words: body language, hesitation, roundabout ways they mention, emotional cues.
6. **Save the output** in the current working directory as `user-interview-prep-[context].md`.

## Output Format

### Research Objective
One sentence. Clear, specific, trainable.

### Hypotheses for testing

| # | Hypothesis | How we find out it's true | How we find out it's false |
|---|----------|----------------------|------------------------|
| 1 | ... | ... | ... |
| 2 | ... | ... | ... |
| 3 | ... | ... | ... |

### Interview Guide

**Warm-up (5 min)** — Establish contact, understand the context.
- Question 1
- Question 2

**Main Research (20 min)** — Immerse yourself in the space of the problem.
- Question 3
- Question 4
- ...

**Conclusion (5 min)** — Catch up on what you missed, get recommendations.
- Question N
- 'Is there something I should have asked but didn't?'

### What to pay attention to
A bulleted list of behavioral signals, indecisiveness, or detours that should be noted during an interview.

### Anti-patterns to avoid
A bulleted list of typical interviewer mistakes specific to this topic (leading questions, presenting solutions, etc.).

## Rules

- Never write a question starting with 'Would you...' or 'How do you think, would you...'. They invite hypothetical answers. Ask about past behavior.
- Every question must pass the 'Mom test': will you get honest, useful information even if you ask your mom?
- No more than 12 questions in total. Quality is more important than quantity — each question should deserve its place.
- Include at least 2 clarifying questions for each main one (for example, 'Tell me more,' 'What happened next?').
- The entire output should not exceed 2 pages. The PM should be able to print it out and take it to the interview.
- Be opinionated: if a hypothesis seems weak or untestable — say so and suggest a better one.
- Do not include questions about the product or the PM solution. This research is about understanding the problem.
- Write in English.

## Metrics

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**