---
name: ai-feature-spec
description: Create a PRD/specification for an AI/ML based feature. The input is a description of the AI ​​feature, the output is a structured document with an ML task, model metrics, fallback logic, HITL scripts and acceptance criteria.
argument-hint: [description of an AI feature or ML task]
allowed-tools: Read, Write
preset: platforms-tech
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# AI Feature Specification

Create a structured requirements specification for integrating artificial intelligence or machine learning into the product. The goal is to link the technical parameters of the model with real product value and minimize the risks of AI uncertainty.

## Process

1. **Understand the problem.** Read the description of the feature. Highlight: what user problem does AI solve, why it cannot be solved with heuristics/code, and what is the source of the data.
2. **Translate the product problem into an ML problem.** (For example: classification, regression, ranking, generation).
3. **Define quality metrics.** Divide into ML metrics (Accuracy, F1-score, precision/recall, ROC-AUC) and product metrics (increased conversion, reduced time, CTR).
4. **Design fallback logic.** What does the system do if the model has low confidence, is wrong, or is inaccessible?
5. **Describe the markup script / HITL (Human-in-the-loop).** Is manual validation of answers required, how is feedback collected for additional training of the model?
6. **Save the output** in the current working directory as `ai-spec-[feature-name].md`.

## Output Format

```
## AI Feature Specification: [Name]

### 1. Product and ML formulation
- **What pain does the AI ​​solve:** [specifically]
- **Why ML:** [why the usual algorithm/rules are not suitable]
- **ML task type:** [e.g. binary spam classification / text generation]
- **Inputs:** [what data is supplied to the model input]
- **Outputs:** [what the model returns]

### 2. Success metrics (Model metrics vs. Business metrics)
| Metric | Type | Target value | Measurement method |
|---------|-----|------------------|-----------------|
| [Business metric, e.g. CTR] | Grocery | [eg +15%] | A/B test |
| [ML metric, e.g. Precision] | Model | [eg >= 92%] | Offline validation |
| [ML metric, e.g. Latency] | Productivity | [eg p95 < 200ms] | Load test |

### 3. Fallback & Edge Cases
- **Confidence Threshold:** at what speed value of the model we trust the result (for example, > 0.85).
- **Scenario with low confidence:** [what we show the user is the default answer, we hide the feature, we ask him to enter it manually]
- **Failure scenario (Service Downgrade/Offline):** what happens if the ML service is unavailable (timeout).
- **Model limitations (Guardrails):** filtering of unwanted content, limiting output length, hallucinations.

### 4. Data & Feedback Loop
- **Source of data for training:** [where we get historical data]
- **Data tagging:** [who tags the data and how - vendor, users, taggers]
- **Feedback Loop:** how the product collects implicit (clicks) and explicit (likes/dislikes) signals from the user to improve the model.

### 5. HITL (Human-in-the-loop)
- **Where a person is needed:** [for example, moderating a generated response before sending it to the client]
- **Moderator interface:** [briefly - where a person sees and confirms the actions of the AI]
- **Moderator SLA:** [how much time is available for manual verification]

### 6. Acceptance Criteria
- [ ] The model was tested on an offline dataset, the [name] metric is higher than the target.
- [ ] ML service crash scenarios worked out (the server responds with an error/timeout).
- [ ] Configured sending prediction logs and user feedback to DWH.
- [ ] Moderators are trained to work with the review interface.
```

## Rules

- Don't allow specifications to be written without fallback logic. AI always makes mistakes - the PM is obliged to design the behavior of the product in the event of an error.
- Require a distinction between ML metrics and business metrics. A model with 100% accuracy is useless if it slows down the interface for 5 seconds and ruins the UX.
- Eliminate the phrases “the model must work perfectly.” Operate with probabilities and confidence intervals.
- Describe collecting feedback as a mandatory part of the feature. Without feedback, the model cannot be improved.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?