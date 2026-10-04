---
name: pricing-experiment
description: Develop a pricing experiment design. The input is a product description and price hypothesis, the output is a structured test plan: methodology (Van Westendorp / PSM, Gabor-Granger, A/B tariff test), questionnaire, sampling, legal restrictions and criteria for evaluating results.
argument-hint: [product description and price testing hypotheses]
allowed-tools: Read, Write
preset: saas
lifecycle: any
business-model: any
domain: saas
stage: any
output-artifact: document
---

# Design of a pricing experiment

Design and prepare an experiment to test the cost of a subscription or product price. The skill helps the product choose a price research methodology (Van Westendorp Price Sensitivity Meter, Gabor-Granger, or A/B test of tariff plans on live traffic), create a survey questionnaire, determine the sample size and minimize the risks of negativity from current users.

## Process



- *Gabor-Granger:* survey with a sequential price offer (Will you buy for 5,000 rubles? If yes -> Will you buy for 7,500 rubles? If not -> Will you buy for 4,000 rubles?). Determination of elasticity of demand.
- *A/B testing of prices:* showing different prices on the landing page to different groups of users (testing the actual purchase action).
2. **Design a questionnaire/test design.**
- Write down the exact wording of the questions.
- Describe the conditions of the event (whom we interview, excluding current paying clients).
3. **Describe minimizing risks and PR negatives.**

- Assessment of legal risks of a public offer of the Russian Federation.


## Output Format

```
## Price Experiment Design: [Product Name]
- **Target stage:** [Discovery (hypothesis testing) / Rollout for production]
- **Selected method:** [Van Westendorp / Gabor-Granger / A/B tariff test]

### 
- **Test target audience:** [for example, new users who do not know the old brand; excluding the current customer base].

- **The purpose of the experiment:** to determine the optimal price point (OPP) and the limit of demand elasticity (price increase vs. conversion decline).

### 2. Interview script (for Van Westendorp PSM)
The wording of 4 mandatory questions for respondents:

2. *Bargain:* “At what price would you consider the product to be a great buy for your money?”

4. *Too expensive:* “At what price will the product seem so expensive to you that you will categorically refuse it?”

### 
- **Option A (Control):** displaying the current price of 9,900 rubles/month.
- **Option B (Test):** displaying the new price of 12,900 rubles/month.


- Testing only on new cohorts of users (the registration page is hidden from authorized users).
- Conditions of the public offer: fixing the price in the cart at the time of order.

### 

```

## Rules

- Do not conduct A/B tests of prices on current paying customers without their explicit notification or creating grandfathering plans (keeping the old price for existing customers). Attempting to secretly raise prices for current users will provoke a wave of negative feedback on social media, a drop in the app rating, and mass churn.
- Van Westendorp surveys should be conducted only on the target audience (ICP). Surveying random people will show underestimated results because they do not understand the value of the product.
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