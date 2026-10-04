---
name: service-desk-metrics
description: Develop a dashboard of internal technical support and Service Desk quality metrics.
argument-hint: [description of IT support processes for employees]
allowed-tools: Read, Write
preset: internal-products
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Service Desk Metrics (service-desk-metrics)

Design a system of indicators and SLAs to assess the quality of work of the company's internal technical support (Service Desk, Helpdesk) staff.

## Process
1. **Determine the support levels (L1, L2, L3).**
2. **Design metrics for satisfaction and speed:**
- **CES (Employee Effort Score):** how easy it was for the employee to solve their problem.
- **FCR (First Contact Resolution):** the share of tickets resolved on the first contact (goal > 70%).
- **SLA compliance:** % of incidents resolved within the regulatory deadlines.
3. **Save the output** in the current working directory as `service-desk-metrics-[context].md`.

## Output Format
```
## IT Support Service Desk Metrics
- **Uptime of critical systems:** SLA 99.9%.
- **FCR Metric (First Contact):** target value > 75% for L1 support.
- **CES survey:** "How easy was it to resolve your issue on a scale from 1 to 5?".
```

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**

## Rules

- Write in English.