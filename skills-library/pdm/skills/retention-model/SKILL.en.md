---
name: retention-model
description: Design or analyze a retention model and user churn. The input is raw retention data or a description of the churn problem, the output is a structured cohort analysis: building a retention curve, finding the plateau, calculating Lifetime, and creating user recovery scenarios.
argument-hint: [description of churn problem or cohort metrics]
allowed-tools: Read, Write
preset: growth
lifecycle: any
business-model: any
domain: saas
stage: any
output-artifact: document
---

# Retention Modeling (Retention Model)

Create a detailed analysis of user retention and churn for the product. It helps the product manager build a cohort model, visualize the retention curve, identify the stabilization point (retention plateau), calculate the average user lifetime, and develop product mechanisms for reactivating lost customers (resurrection).

## Process

1. **Determine the type of retention (Retention Type).**
- *N-Day Retention (Classic):* whether the user returns exactly on the N-th day (for daily apps: social networks, games).
- *Unbounded Retention (Rolling):* whether the user returned on day N or later (for irregular services).
- *Bracketed Retention:* whether the user returned in the given interval (for example, week 1, month 1).
2. **Design a retention curve and find the plateau.** What is the share of active users on Day 1, Day 7, Day 30? At what level does the curve reach a horizontal line (plateau)? If there is no plateau and the curve tends to zero, the product does not have Product-Market Fit.
3. **Identify the key churn drivers.** Why are users leaving (complex onboarding, lack of value, high price, technical bugs)?
4. **Calculate the product lifecycle (Lifetime / LT).** The average duration of product use by a user. Link Retention with the calculation of LTV (Lifetime Value).
5. **Design a resurrection strategy (Resurrection Strategy).** How to bring back users who have stopped using the product? (Triggered emails, special offers, informing about new features that address their past pain points).
6. **Save the output** in the current working directory as `retention-spec-[context].md`.

## Output Format

```
## User Retention Analysis: [Product Name]

### 1. Retention Measurement Methodology
- **Product type:** [for example, B2C service ordering mobile application]
- **Definition of an active action (Active Event):** [what action is considered a sign of engagement, for example: making a transaction / launching the application]
- **Selected metric type:** Bracketed Retention (monthly) / Classic N-Day Retention / Rolling Retention.

### 2. Cohort Retention Curve (Retention Curve & Plateau)
Current cohort retention metrics:

| Period (Month / Day) | Retention Rate (% Retention) | Cohort Status |
|-----------------------|---------------------------------|----------------|
| Month 0 (Start) | 100% | Cohort start |
| Month 1 | 35% | Initial dropout (activation) |
| Month 3 | 22% | Beginning of stabilization |
| Month 6 | 18% | Plateau point (PMF reached) |
| Month 12 | 17% | Long-term retention |

- **Assessment of the presence of a plateau:** [does the curve reach a stable plateau or fall to zero]. The presence of a plateau at the level of 18% confirms the presence of value for the core audience.

### 3. Churn Drivers (Churn Analysis)
- **Barrier of the 1st period (M1 Churn):** [the main reason for leaving immediately after registration, for example: the user downloaded the app but did not find a service provider in their area].
- **Long-term Churn (M3+):** [reasons for the departure of loyal users, for example: found a professional directly bypassing the platform].

### 4. Assessment of Lifetime (LT) and LTV
- **Lifetime (LT) calculation:** the average lifespan of a paying user in months (LT = 1 / Churn Rate).
- **Connection with LTV:** `LTV = ARPU × Lifetime`.
- **Growth vector:** how shifting the plateau point up by 2% increases the LTV of the entire cohort (forecast calculation).

### 5. Strategy for Reviving the Departed (Resurrection Plan)
- **Segmentation of churned users:** identification of a cohort of users who have not had active sessions for more than 60 days, but previously had an LTV > X.
- **Communication channels:** push notifications, personalized email newsletters, SMS offers.
- **Value proposition:** [offer a discount on a repeat order, showcase a new deal security feature that addresses their past concerns].
```

## Rules

- Do not allow calculating Retention based on ordinary app launches if the product is commercial. Launching the app without performing a target action (search, purchase, view) is false engagement. Retention should be calculated based on performing a value event.
- The presence of a retention plateau is a critical evaluation criterion. The product should not propose scaling marketing (traffic growth) if the retention curve does not reach a plateau (traffic will leak through the sieve).
- All retention calculations must be carried out strictly using the cohort method. The average Retention across the entire database without tying it to the cohort registration date is useless.
- Write in English.

## Metrics (SaaS)

### Outcome metric
**NRR, retained ARR/MRR, active paying accounts.** Main result and value.

### Input metrics
**activation rate, time-to-value, feature adoption, seats used, integrations connected.** Managed levers of outcome.

### Guardrails
**GRR, logo churn, support load, gross margin, implementation time.** What must not be worsened.

### Diagnostic metrics
**cohort retention by segment, churn reasons, expansion/contraction bridge, account health score.** Where to look for the reason.

### Instrumentation
**account_id, plan, seats, feature events, billing events, CRM segment.** What data is needed.

### Decision rules
- Ship / Iterate / Kill

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**