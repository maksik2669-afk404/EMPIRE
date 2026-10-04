---
name: feedback-analyzer
description: Classify and analyze raw user feedback by topic, tone, and actionable insights. The input is the inserted feedback text or the path to a CSV file, the output is structured patterns and recommendations.
argument-hint: [insert feedback or CSV path]
allowed-tools: Read, Write, Bash, Glob, Grep
preset: discovery
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Feedback Analyzer

Take raw, chaotic user feedback and turn it into structured, actionable insights. Works with pasted text, CSV files, or any text feedback dump.

## Process

1. **Download feedback** - If the path to the file is specified, read it. If CSV, parse it using Bash (csvtool, awk or python). If the inserted text is divided into logical entries (one per line or per paragraph).
2. **Classify each entry** - For each feedback entry, assign:
- **Topic** (e.g. Onboarding, Pricing, Performance, Missing Feature)
- **Tone** (Positive / Neutral / Negative)
- **Urgency** (High / Medium / Low - based on language intensity and frequency)
- **Type** (Bug report / Feature request / Complaint / Praise / Question)
3. **Aggregate patterns** - Count topics, calculate sentiment distribution, determine top recurring problems.
4. **Uncover Insights** - Look for non-obvious patterns: correlating themes, changes in tone, churn risk signals or expansion opportunities.
5. **Write Recommendations** - Translate patterns into specific next steps for the PM.
6. **Save the output** in the current working directory as `feedback-analyzer-[context].md`.

## Output Format

### Summary statistics
- Total feedback entries: X
- Sentiment distribution: X% positive, X% neutral, X% negative
- Top topic: [topic] (X mentions)
- Date range (if available): [range]

### Topic table

| Topic | Qty | Key (avg) | Urgency | Sample Quote |
|------|--------|-----------------|------|--------------|
| ... | ... | ... | ... | "..." |

### Top 3 patterns
Numbered list. Each pattern includes: what it is, why it's important, and how confident you are (based on volume).

### Recommended Actions

| Priority | Action | Base | Expected effect |
|-----------|----------|-----------|-----------------|
| P0 | ... | ... | ... |
| P1 | ... | ... | ... |
| P2 | ... | ... | ... |

### Classified raw data
If there are less than 50 records, include a full table with the classification of each record. If more than 50, save it to a file and specify the path.

## Rules

- Don’t add your own opinions. Classify what users said, not what you think they meant.
- If the feedback post concerns several topics, assign the dominant one, but mark the secondary one.
- Urgency is based on the intensity of the language ("broken", "can't use", "blocking" = High) and frequency, not on your opinion of importance.

- Always include at least one verbatim quote about the topic. Real words are more important than summaries.

- Be opinionated in recommendations: tell the PM what to do first and why, rather than just listing options.
- If the amount of feedback is too small for conclusions (less than 5 records), say so explicitly and note which patterns are weak signals.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?