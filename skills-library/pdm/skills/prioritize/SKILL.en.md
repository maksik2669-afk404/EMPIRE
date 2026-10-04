---
name: prioritize
description: Evaluate and prioritize a list of features or initiatives according to RICE, ICE, MoSCoW or WSJF. The input is a list of features, the output is a ranked table with justification, Regulatory Override and a recommended cutoff line.
argument-hint: 
allowed-tools: Read, Write
preset: core
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Backlog prioritization (Prioritize)

Transform a chaotic backlog into a ranked, defensible list of priorities. The skill supports classic frameworks (RICE, ICE, MoSCoW), as well as WSJF (for Agile/SAFe) and banking compliance mode (Regulatory Override).

## Process

1. **Gather a list of features.** Parse the input data (list or file path).
2. **Choose a framework.**
- *RICE (default):* Reach × Impact × Confidence / Effort.

   - *MoSCoW:* Must have, Should have, Could have, Won't have.
- *WSJF (Weighted Shortest Job First):* `CoD / Job Size`, where `CoD` (Cost of Delay) = User Value + Time Criticality + Risk Reduction/Opportunity Enablement.
3. **Apply Regulatory Override.** Highlight the features that are mandatory by law, Central Bank of Russia regulations, or safety/compliance requirements (Federal Laws 152-FZ, 115-FZ). These features are automatically moved to the P0 category (Must Have / Doing now) bypassing any mathematical scoring, with the note 'Regulatory Requirement.'
4. **Rank the features.** Sort in descending order of the score, taking into account the P0 pass.
5. **Draw a cutoff line.** Sort into: Do now (this sprint/quarter), Do next, Postpone.
6. **Save the output** in the current working directory as `prioritized-backlog-[context].md`.

## Output Format

```
## Backlog Prioritization: [Context]
- **Framework:** [RICE / ICE / WSJF / MoSCoW]
- **Regulatory compliance:** Enabled (features with regulatory requirements have P0 priority).

### 1. Prioritization Table
| Rank | Feature | Scoring Metrics (Reach/Impact/CoD...) | Rating / Category | Status | Reason for Priority / Note |
|------|------|----------------------------------------|--------------------|--------|---------------------------------|
| P0 (1) | [Feature 1] | — | **Regulatory Override** | Doing now | Requirement of Federal Law 152-FZ on the storage of personal data in the Russian Federation |
| 2 | [Feature 2] | [Reach=10k, Impact=2, Conf=80%, Eff=2] | 8000 (RICE) | Doing now | High reach with low effort |
| ... | ... | ... | ... | ... | ... |

### 2. Breakdown by Categories (Cut-off Point)
- **Doing now (this quarter):** [List of features ranked 1-N]
- **We do the following:** [List of features]
- **Postponed:** [List of features]

### 3. Justification of assessments and compromises
- **Top priorities:** why these features ended up at the top of the backlog.
- **Low priorities:** why these features are postponed (for example, high complexity with dubious effect).
- **Controversial points:** features with a close score (difference < 10%), where the choice between them requires additional qualitative arguments.
```

## Rules

- Features marked as Regulatory Override (compliance with the Central Bank of Russia, Russian laws) should go to the very top of the backlog (P0/Must Have) without any mathematical calculation. Business security and legal compliance are more important than product features.
- Require a consistent scale for estimating effort (person-months or Story Points) for all features within a single calculation.
- Do not allow subjective inflation of Confidence. If there is no research or test data — set Confidence = 50% and first require conducting Discovery.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?