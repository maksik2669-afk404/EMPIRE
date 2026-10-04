---
name: icp-definition
description: Design an ideal customer profile (ICP) for a B2B product. The input is a description of the product and its business goals, the output is a structured B2B ICP: firmographics, technographics, behavioral readiness signals and a negative ICP profile.
argument-hint: [description of B2B product and sales goals]
allowed-tools: Read, Write
preset: discovery
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Ideal Customer Profile / B2B ICP

Create a detailed ideal customer profile (ICP) specification for a B2B product or B2B2C platform. Helps the product to focus marketing and sales (Outbound/Inbound Sales) on those companies that get the maximum value from the product, buy the fastest, pay the most and do not experience low churn.

## Process

1. **Section the concepts of ICP and Persona.**
- *ICP (Ideal Customer Profile):* description of a **company** (company graphics, technographics) that is an ideal customer.
- *Persona:* description of specific **people** within this company (Decision Maker, Economic Buyer, Blocker, User).
2. **Describe Firmographics.** Company size (revenue, number of employees), field of activity (industry), geographic location, business model (B2B/B2C).
3. **Describe Technographics.** What technology stack does the company use? (For example: CRM 1C, Postgres database, Russian cloud servers, integration with external APIs).
4. **Identify behavioral signals (Buying Signals / Triggers).** What events signal that the company is ready to buy the product right now? (For example: obtaining a developer’s license, starting a new construction project, actively hiring certain specialists).
5. **Design a negative ICP profile.** Which clients do we deliberately exclude from our sales focus, since the cost of their support or integration exceeds LTV (for example, micro-agencies, developers without a Russian Federation Taxpayer Identification Number).
6. **Save the output** in the current working directory as `icp-definition-[product-name].md`.

## Output Format

```
## Ideal Customer Profile (ICP): [B2B Product Name]

### 1. Firmographics
Parameters of a company that is ideal for our product:

| Parameter | Ideal value (ICP) | Minimum entry threshold | Rationale |
|----------|-----------|------------------------|-------------|
| **Industry** | Development of countryside real estate (IZHS) | Construction / Development | Only they have an acute pain with escrow accounts of individual housing construction |
| **Revenue** | From 500 million to 5 billion rubles/year | From 100 million rubles/year | Small developers do not have budgets for automation |
| **State** | From 50 to 300 employees | From 15 employees | There is a dedicated IT department or technical director |
| **Geography** | Moscow region, Leningrad region, Krasnodar region | RF | Regions with the maximum volume of suburban construction |

### 2. Technology Stack and Maturity (Technographics)
- **Systems used:** [for example, CRM 1C, Bitrix24, having our own IT department or contractor].
- **Integration Requirements:** [company must be able to work with external REST/gRPC APIs for seamless account disclosure].

### 3. Buying Triggers
Events in the company that indicate an urgent need for a solution:
- Launch of a new large-scale individual housing construction project in the Moscow region.

- Receiving an order from the creditor bank on the need to speed up work with project financing accounts.

### 4. Negative ICP
Companies we do not work with or place as a low priority:
- Micro-contractors (build 1-2 houses per year manually) - no processes for automation, high Churn.
- Developers of apartment buildings (MKD) - they have different processes and other integrations (for example, large-scale project financing through other IT systems).


### 5. ICP Validation Metrics

- **Win Rate:** % of won deals from companies that comply with ICP (target > 30-40%).
- **LTV / CAC:** ratio of value and acquisition costs within ICP.
```

## Rules


- Be sure to prescribe Negative ICP. Without it, the sales team will waste time on small, untargeted accounts with high support costs and zero LTV.
- Buying Triggers must be verifiable external sources (vacancies on HeadHunter, state registers, news about financing).
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?