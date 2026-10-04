---
name: data-product-spec
description: Develop a Data Product Specification.
argument-hint: [description of the data set or data mart for the specification]
allowed-tools: Read, Write
preset: platforms-tech
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Data products (data-product-spec)

Design a specification for an internal or external Data Product (data marts, analytical pipelines, data APIs).

## Process
1. **Identify Data Consumers** (Analysts, ML models, business stakeholders).
2. **Write down the Data Quality SLA.** Allowable update delay (freshness), completeness, uniqueness of rows.
3. **Design Data Lineage.** Data sources -> Processing pipeline -> Final showcase.
4. **Save the output** in the current working directory as `data-product-spec-[context].md`.

## Output Format
```
## Data Product Specification: [Showcase Name]
- **Consumers:** Scoring ML model of the bank.
- **SLA for data quality:** Freshness < 15 minutes, null values ​​in key fields < 0.01%.
- **Data Lineage:** [source diagram].
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