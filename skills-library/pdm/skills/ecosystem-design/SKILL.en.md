---
name: ecosystem-design
description: Design a product ecosystem and rules for synergy of services (Ecosystem Design).
argument-hint: [list of company services for integration into an ecosystem]
allowed-tools: Read, Write
preset: platforms-tech
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Ecosystem-design

Develop a product strategy for combining disparate company services into a single ecosystem (SuperApp, single subscription, cross-product cashback).

## Process
1. **Design the core of the ecosystem.** Single authorization (Ecosystem ID), single profile and payment data.
2. **Formulate the rules of synergy.** How using service A stimulates conversion to service B (for example: taxi rides give points for food delivery).
3. **Minimize cannibalization.**
4. **Save the output** in the current working directory as `ecosystem-design-[context].md`.

## Output Format
```
## Ecosystem Design: [Title]
- **Core of the ecosystem:** Single authorization ID based on the Unified Identification Number/Phone Number.
- **Loyalty mechanics:** Cross-product cashback with points.
- **Ecosystem subscription bundle:** [description of subscription content].
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