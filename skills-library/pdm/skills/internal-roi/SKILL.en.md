---
name: internal-roi
description: Calculate the business case (ROI, TCO, savings) for an internal product or platform. The input is a description of automation or a replacement tool, the output is a structured justification of the cost of ownership, payback and savings on payroll.
argument-hint: [description of internal product or automation]
allowed-tools: Read, Write
preset: fintech
lifecycle: any
business-model: any
domain: fintech
stage: any
output-artifact: document
---

# Calculation of ROI of internal product

Create a business case and financial justification for developing an internal tool, platform or process automation. Helps the product prove the feasibility of development to the CIO/CFO, in terms of numbers, payroll savings and cost of ownership (TCO).

## Process

1. **Determine the current state (As-Is).** How many people are performing the task manually? How long does it take? How much does a third party tool cost if used?
2. **Define the target state (To-Be).** What part of the process will the new product automate? How much employee time will it save?
3. **Calculate development and support costs (TCO).** What are the development costs (team x time) and how much will support cost per year (infrastructure, licenses, maintenance).
4. **Compare Make vs. Buy.** What is more profitable - writing your own solution or buying a ready-made external one?
5. **Calculate financial metrics.** Annual savings (Cost Savings), Payback Period (Payback Period), ROI (Return on Investment).
6. **Save the output** in the current working directory as `internal-roi-[product-name].md`.

## Output Format

```
## Financial justification: [Name of internal product]

### 1. Problem and Replaceable Process (As-Is)
- **What we automate:** [description of a manual process or a replaceable external system]
- **Current payroll costs:** [number of employees] × [average rate per hour] × [hours per month per task] = **[X] rub./month**
- **Direct costs (licenses/support):** [if we buy external software] = **[Y] rub./month**
- **Total current costs:** **[Z] rub./year**

### 2. Goal State and Time Saving (To-Be)
- **How ​​the process will change:** [automation description]
- **Reduction in manual labor:** from [X] hours to [Y] hours per operation (reduction by **[Z]%**).
- **Resource released:** [how many FTE (Full-Time Equivalent) is released]
- **Annual savings on payroll:** **[Amount] rub./year** (including taxes and overhead costs ~30-40%).

### 3. Calculation of cost of ownership (TCO - Total Cost of Ownership)
- **Capital costs (CAPEX - development):**

- Infrastructure for development/testing: **[Amount] rub.**
- **Operating costs (OPEX - support per year):**
- Support and administration: **[Amount] rub./year**
- Hosting and licenses: **[Amount] rub./year**
- **Total TCO (over a 3-year horizon):** CAPEX + (OPEX × 3) = **[Amount] rub.**

### 
| Parameter | Own development (Make) | External solution (Buy) |

| Startup Cost | [CAPEX development] | [Implementation Licenses] |





### 5. Financial performance indicators
- **Total net savings (3 years):** [Payroll savings for 3 years] - [TCO for 3 years] = **[Amount] rub.**
- **Payback Period:** CAPEX / (Annual Savings - OPEX) = **[X] months**
- **Project ROI:** (Net savings for 3 years / TCO for 3 years) × 100% = **[X]%**

### 6. Implementation risks and assumptions


- **Risk of rising support costs:** [description of infrastructure risks].
```

## Rules

- Prohibit the use of abstract arguments like “a tool will make work more enjoyable.” Any automation should be expressed in terms of FTE (employee hours freed) or money saved on licenses.


- Write in English.

## Metrics (Fintech/Lending)

### Outcome metric
**risk-adjusted profit, approved good customers, portfolio margin.** Main result and value.

### 
**KYC pass rate, approval rate by risk bucket, time-to-decision, utilization.** Managed outcome levers.

### Guardrails


### Diagnostic metrics


### Instrumentation
**application_id, risk bucket, decision, KYC steps, repayment/vintage data, fraud flags.** What data is needed.

### Decision rules
- Ship/Iterate/Kill

### Universal Metric Rule
If you are proposing a metric, answer 5 questions:

2. **How ​​often do we watch it?**


