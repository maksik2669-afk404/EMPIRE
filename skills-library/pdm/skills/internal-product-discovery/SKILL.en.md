---
name: internal-product-discovery
description: Conduct a needs study (Discovery) for an internal IT product (for employees).
argument-hint: [description of the company’s internal product and the target role of employees]
allowed-tools: Read, Write
preset: internal-products
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Discovery of internal products (internal-product-discovery)

Conduct qualitative research (Discovery) for automation systems of the company’s internal processes (HR portals, CRM, ERP, support systems).

## Process
1. **Describe the target employee.** Work context, tools used, pain points.
2. **Solve the Forced Adoption problem.** Employees are required to use your product according to regulations, so NPS is often underestimated. Focus on saving time (Efficiency) and CES (Customer Effort Score).
3. **Develop process efficiency metrics.** Saving man-hours per month, reducing the number of manual errors.
4. **Save the output** in the current working directory as `internal-product-discovery-[context].md`.

## Output Format
```
## Internal Discovery: [Name of internal system]
- **Target role:** [for example, bank surveyors]
- **Main pain:** spending 40 minutes copying data from Excel to the old banking system.
- **Business effect of automation:** saving 450 man-hours per month for a department of 50 people.
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