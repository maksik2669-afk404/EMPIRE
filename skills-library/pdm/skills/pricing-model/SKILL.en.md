---
name: pricing-model
description: Develop a pricing strategy and tariff structure (Packaging & Pricing). Input — product description and its value, output — a structured tariff grid, choice of monetization metric, justification of the price and mechanics of price testing.
argument-hint: [product description and hypotheses about tariffs]
allowed-tools: Read, Write
preset: saas
lifecycle: any
business-model: any
domain: saas
stage: any
output-artifact: document
---

# Pricing Strategy (Pricing Model)

Develop and justify the pricing model and tariff structure for a product (SaaS, transactional platforms, B2C subscriptions). The skill helps the product team determine the optimal monetization metric (value metric), distribute features across tariff plans (Free, Starter, Pro, Enterprise), and design a willingness-to-pay testing plan.

## Process

1. **Define the monetization metric (Value Metric).** What does the client pay for? The metric should grow along with the increase in value for the client. (For example: for the number of users/seats, for the number of completed deals/estimates, for the amount of stored data).
2. **Design the structure of the tariff grid (Packaging & Tiering).**
- *Starter/Individual:* basic features for starting, low price, strict limitations.
- *Professional/Growth:* team features, integrations, extended limits (main revenue generator).
- *Enterprise:* advanced security (SSO, SLA, dedicated server), custom contract.
3. **Justify the price thresholds.** Based on value-based pricing analysis or competitive analysis. What portion of the value do we take for ourselves in the form of a price? (Usually 10-20% of the money saved for the client).
4. **Design a Willingness-to-Pay testing plan.** Describe price validation methods (Van Westendorp surveys, tariff A/B tests, prepaid pre-orders).
5. **Save the output** in the current working directory as `pricing-model-[product-name].md`.

## Output Format

```
## Pricing Model and Rates: [Product Name]

### 1. Monetization Metric (Value Metric)
- **Selected metric:** [for example, the number of successfully closed escrow accounts per month]
- **Rationale for choice:** [why this metric correlates with value for the client's business; for example, the developer saves on payroll and loan interest on each deal, so paying per transaction is the most fair].

### 2. Pricing Grid (Pricing Tiers & Packaging)
Service package design:

| Tariff | Target segment | Monthly price | Key limits / Features | Trigger for upgrade to next level |
|-------|-----------------|--------------|------------------------|---------------------------------------|
| **Base** | Individual estimators | 2,900 RUB | Up to 3 projects, no API, PDF export only | Exceeding the project limit (>= 4) |
| **Pro (Team)** | Small developers | 14,900 RUB | Up to 5 users, 1C integration, auto-fill | Adding a 6th user |
| **Enterprise** | Large developers | Custom (from 100k) | Unlimited, SSO, custom SLAs, dedicated database | Security requirement / On-premise |

### 3. Economic Justification (Value-Based Pricing)
- **Client savings:** [for example, using the service saves the developer 3 days of a lawyer's work on each deal (about 5000 rubles) and reduces project financing interest by 15,000 rubles].
- **Our Take Rate (share of value):** [we take 2,000 rubles per transaction, which is only 10% of the total value of 20,000 rubles created by the service].

### 4. Price Validation Plan (Willingness-to-Pay Testing)
- **Research method:** [for example, Van Westendorp survey among 100 developers to determine the optimal price range].
- **A/B test of prices on the landing page:** [show 50% of traffic the old price of 14,900 rubles, and the other 50% — 19,900 rubles. Measure conversion to successful payment].
```

## Rules

- Do not allow using parameters unrelated to value as the Value Metric (for example, charging for disk space if the product is an analytics system). The Value Metric should increase as the customer receives more benefit.
- The Enterprise plan must necessarily include 'security and management' features (SSO, SAML, audit logs, custom SLAs), not just increased quantitative limits. Corporations pay for control and reducing legal risks, not for volumes.
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