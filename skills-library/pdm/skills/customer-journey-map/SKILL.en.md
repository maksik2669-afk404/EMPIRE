---
name: customer-journey-map
description: Develop a comprehensive Customer Journey Map (CJM) for the product.
argument-hint: [description of product and target user cohort for CJM]
allowed-tools: Read, Write
preset: discovery
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Designing CJM (customer-journey-map)

Develop a detailed user journey map (Customer Journey Map), recording all points of contact, barriers, thoughts and emotions at every step of interaction with the product.

## Process
1. **Define the target person and scenario.** (For example: a private housing developer wants to be accredited with a bank).
2. **Describe the stages of the journey.** Awareness -> Search -> Registration -> First deal -> Retention.
3. **Fix for each step:** user actions, communication channels, pain points/barriers, user thoughts and ideas for improvement (product hypotheses).
4. **Save the output** in the current working directory as `customer-journey-map-[context].md`.

## Output Format
```
## Customer Journey Map: [Person - Script]

### 1. Stage 1: Company registration
- **Actions:** filling out a form on the bank’s website.
- **Pains and Barriers:** the form requires 15 file scans of the charter and passports of directors. No draft saving.
- **Client’s thoughts:** “Why is it so difficult? I’d rather go to another bank.”
- **Idea for improvement:** add auto-filling of TIN details and saving a draft application.
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