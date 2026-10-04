---
name: d2c-subscription-model
description: Design a D2C subscription for a physical product: food box, beauty box, premium goods, farm basket or regular delivery. The output is model selection, tariffs, unit economics, retention loop, fulfillment risks, supplier economics, subscription metrics and go/no-go decision.
argument-hint: [description of product, audience, price, frequency of purchase and logistics]
allowed-tools: Read, Write
preset: saas
lifecycle: strategy,growth,measure
business-model: d2c,subscription,ecommerce
domain: retail,food-d2c
stage: idea,mvp,pre-pmf,pmf,scale
output-artifact: d2c-subscription-business-case
---

# D2C subscription for a physical product

Design a direct sales subscription business model for a physical product where value is created not only by the digital interface, but also by regular delivery, quality, trust, brand and operational discipline.

## When to use

- Farm/food subscription, premium goods, beauty box, pet food, wellness, regular delivery of consumables.
- The brand wants to move away from one-time sales to recurring revenue.
- There is an expensive CAC and we need a model where retention is more important than constant re-attraction.
- You need to choose between an online store, someone else’s marketplace and your own subscription.

## When NOT to use

- Purchase is irregular and there is no natural frequency of consumption.
- Logistics eats up margins, and you can’t raise a check.
- The user is not ready for re-delivery or wants to select manually every time.
- There is no quality control of delivery, packaging and returns.

## Process

1. **Identify a recurring job.** What regular need makes a subscription natural?
2. **Compare models.** One-time e-commerce purchase, someone else’s marketplace, D2C subscription, retail/offline.
3. **Create tariffs.** Frequency, composition, price, pause, skip, cancel, upsell.
4. **Calculate unit economics.** AOV, ARPU, gross margin, delivery cost, CAC, LTV, payback, break-even.
5. **Design a retention loop.** What makes you wait for the next delivery?
6. **Design fulfillment.** SLA, freshness, packaging, routes, replacements, returns.
7. **Describe supplier economics.** Partner’s share, minimum volumes, quality, reliability.
8. **Build a growth loop.** Referral, content, community, brand, gift mechanics.
9. **Collect a risk heat map.** Logistics, CAC, churn, quality, suppliers, seasonality, reputation.
10. **Give me a go/no-go solution.** Pilot / narrow wedge / build / partner / kill.
11. **Save the output** in the current working directory as `d2c-subscription-model-[context].md`.

## Output Format

```md
## D2C Subscription Model: [Name]

### 1. Context and recurring job
- **User:** [segment]
- **Regular need:** [which is repeated]
- **Why subscription is natural:** [frequency/convenience/trust/saving effort]

### 2. Model selection
| Model | Pros | Cons | Conclusion |
|---|---|---|---|
| One-time online store | | | |
| Alien marketplace | | | |
| D2C subscription | | | |

### 3. Tariffs and UX subscriptions
| Tariff | Price | Frequency | For whom | Margin | Risks |
|---|---:|---|---|---:|---|

- **Pause:** [how it works]
- **Skip:** [how it works]
- **Cancel:** [without dark patterns]
- **Replacements:** [if the product is out of stock]

### 4. Unit economics
| Metric | Meaning | Comment |
|---|---:|---|
| AOV | | |
| Deliveries/month | | |
| ARPU | | |
| Gross Margin | | |
| Delivery Cost | | |
| CAC | | |
| Monthly Churn | | |
| LTV | | |
| LTV/CAC | | |
| CAC Payback | | |
| Break-even subscribers | | |

### 5. Subscription metrics
- **Outcome:** active subscribers, MRR, contribution margin.
- **Input:** activation, first delivery success, delivery SLA, referral rate.
- **Retention:** monthly churn, pause rate, pause return rate, repeat delivery success.
- **Guardrails:** complaint rate, refund rate, late delivery rate, supplier margin, quality incidents.
- **Diagnostics:** churn reasons, cohort retention, CAC by channel, NPS by delivery cohort, stockout rate.

### 6. Fulfillment and SLA
| Stage | SLA | Risk | Guardrail |
|---|---|---|---|
| Assembly | | | |
| Packaging | | | |
| Delivery | | | |
| Replacements/Refunds | | | |

### 7. Supplier economics
- **Partners/suppliers:** [who]
- **Supplier share:** [%]
- **Minimum volume:** [value]
- **Quality control:** [how we check]
- **Backup supply:** [2-3 suppliers per critical component]

### 8. Growth/Retention Loop
1. Acquisition: [brand/content/referral/paid]
2. First order: [first moment of trust]
3. Delivery value: [why the user is satisfied]
4. Retention content: [what maintains the habit]
5. Referral/community: [how the user refers others]

### 9. Risk Heat Map
| Risk | Probability | Influence | Trigger signal | Mitigation |
|---|---|---|---|---|

### 10. Solution
**Recommendation:** [pilot/build/narrow/partner/kill]
**First pilot:** [segment, geo, number of clients, duration]
**Exit criteria:** [success/failure metrics]
```

## Rules

- Do not design a subscription without a fair pause, skipping and canceling. Retention should be built on value, not traps.
- Don’t count LTV from revenue. Use margin after goods, delivery, packaging and returns.
- Check that the frequency of delivery matches the actual consumption, otherwise there will be a churn and accumulation of unnecessary goods.
- If delivery/freshness is part of the value, the SLA should be a guardrail, not an operational detail.
- Always show the sensitivity of the economy to churn, CAC and delivery cost.
- Write in English.

## Metrics (Subscription/D2C)

### Outcome metric
**active subscribers, MRR, contribution margin.** Main result and value.

### Input metrics
**first order success, delivery SLA, referral rate, content engagement, pause return rate.** Controlled outcome levers.

### Guardrails
**monthly churn, refund rate, late delivery rate, complaint rate, supplier margin, quality incidents.** What cannot be worsened.

### Diagnostic metrics
**churn reason, cohort retention, CAC by channel, NPS by delivery cohort, stockout/substitution rate.** Where to look for the reason.

### Instrumentation
**subscription_id, delivery_id, pause/cancel events, SKU availability, channel, refund reason.** What data is needed.

### Decision rules
- Ship/Iterate/Kill

### Universal Metric Rule
If you are proposing a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How ​​often do we watch it?**
3. **What events count it?**
4. **What is the decision threshold?**
5. **How ​​can it be spoiled or screwed up?**
