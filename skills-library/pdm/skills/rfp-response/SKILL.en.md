---
name: rfp-response
description: Develop requirements and a product rationale for participation in tenders and terms of reference (RFP Response).
argument-hint: [description of tender requirements and product]
allowed-tools: Read, Write
preset: b2b
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Participation in tenders and RFP (rfp-response)

Formulate requirements and product proposals for participation in government (44-FZ, 223-FZ) or large corporate procurements (RFP/RFI).

## Process
1. **Do a gap analysis of the requirements in the terms of reference.** Does our product meet the customer's basic requirements?
2. **Formulate Win Themes (Key Advantages).** What makes our product superior to competitors.
3. **Describe the compliance matrix (Compliance Matrix).**
4. **Save the output** in the current working directory as `rfp-response-[context].md`.

## Output Format
```
## Response to RFP/Terms of Reference: [Project Name]
- **Requirements gap analysis:** [which features need to be refined by the project delivery].
- **Compliance Matrix:** a table of our product specification compliance with the customer's requirements.
```


## Rules

- Write in English.
## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?