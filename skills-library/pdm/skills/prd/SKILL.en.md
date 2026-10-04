---
name: prd
description: Create a clear, structured PRD from an idea or feature description. Not a 20-page document - 1-2 pages that force decisions (including AI/ML requirements and fallback logic).
argument-hint: [product idea or feature description]
allowed-tools: Read, Write
preset: core
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# 

Create a concise, actionable specification document (PRD) of up to 2 pages. The template forces the product to make tough decisions on goals, scope and metrics, and also supports a special AI/ML mode for artificial intelligence-based features.

## Process


2. **Define the nature of the feature.** If the feature uses AI/ML (for example, automatic generation of estimates, scoring, AI assistant) - turn on the ML section.
3. **Describe ML requirements (for AI mode):**
- *Model metrics vs. Business metrics:* specify target Precision/Recall/F1-score models and link them to business metrics (for example, approval, conversion).
- *Training set:* data sources for training and labeling.

4. **Formulate the MVP scope and boundaries (What is Out of Scope).**
5. **Save the output** in the current working directory as `prd-[feature-name].md`.

## Output Format

```
## Product Requirements Document (PRD): [Feature name]

### 1. Problem and Target Audience
- **What is the problem:** [description of the user's pain with an example]

- **As solved now:** alternative workarounds for users.

### 2. Description of the solution and Scenarios (Scope)
- **What we are building:** [essence of the solution, key value]
- **What we do NOT build (Out of Scope):** [critical scope boundaries that cut off requirements inflation]
- **Custom scenarios:** consistent step-by-step flow of the feature.

### 3. Requirements for AI / ML (ML Requirements)
*(To be completed only for AI features)*
- **Model task:** [for example, classification of estimated items]
- **Model quality metrics:** [minimum accuracy threshold Precision / Recall / F1]

- If model confidence is < 80%: [for example, we do not use auto-fill, but ask the user to fill in manually with the tooltip highlighted].


### 4. Success metrics and KPIs

- **Guardrail metric:** [a metric that should not deteriorate, for example: page loading time no more than 1.5 seconds].

### 5. Risks and Open Questions

- **Technical risks:** [dependencies on external APIs, backend performance].
```

## Rules

- The section “What we DO NOT build” is required. PRD without strict scope boundaries leads to endless development and missed deadlines.
- Fallback logic is required for AI features. You cannot run neural networks on production without a script for how the system will behave in the event of a model error.
- Success metrics should contain measurable goals and numbers, not abstract slogans.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?