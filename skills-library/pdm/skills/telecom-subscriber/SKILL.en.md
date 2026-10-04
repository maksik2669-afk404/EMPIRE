---
name: telecom-subscriber
description: Design a B2C product for a telecom operator - tariff package, convergent bundle (Internet + TV + mobile), anti-churn or upsell. The input is the segment and context of the operator, the output is the product structure, pricing logic and retention metrics.
argument-hint: [description of subscriber segment, current tariff/service, problem or goal]
allowed-tools: Read, Write
preset: telecom
lifecycle: any
business-model: subscription
domain: telecom
stage: any
output-artifact: document
---

## Metrics

### Universal metric rule
If you are proposing a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How ​​often do we watch it?**
3. **What events count it?**
4. **What is the decision threshold?**
5. **How ​​can it be spoiled or screwed up?**
# B2C telecom operator products (telecom-subscriber)

Design a consumer product for a telecom operator: tariff plan, converged service package (Internet + TV + mobile), retention mechanics (anti-churn) or upsell into a premium package. The skill helps the product work with the specifics of the subscription business: high churn, price sensitivity, the role of the call center and cross-selling.

## Process

1. **Please clarify the context:**
- **Product type:** New tariff / Bundle (convergent package) / Anti-outflow / Upselling / Loyalty program.
- **Segment:** Individuals (B2C mass market / premium) or households.
- **Current situation:** What does the subscriber have now? What is the average ARPU? What is the churn rate?
- **Goal:** Reduce churn / Increase ARPU / Convert to bundle / Launch a new service.

2. **Design product logic:**

**For a new tariff/bundle:**
- Determine the anchor service - what is the main thing in the package for the subscriber.
- Calculate the discount on the bundle vs individual services - it should be significant (≥15%).
- Design a switching cost trap: the discount is active only if all services in the package are available.
- Define connection conditions: online / call center / dealer network.

**For Anti-Churn:**
- Highlight churn triggers (reduced consumption, expired contract, support complaints).
- Design a retention-offer: personal discount / speed upgrade / free month.
- Determine the cohort for proactive calling (propensity-to-churn scoring).
- Set a request window: 30 days before the end of the contract.

**For upselling:**
- Determine the upsell trigger: reaching the speed limit, increasing TV consumption, buying a new device.
- Design an offer: upgrade without interrupting the service, the price difference is minimal.
- Select a channel: push in personal account / call center / SMS / in-app.

3. **Calculate the unit economy:**
- **ARPU** before and after switching to a new tariff.
- **CAC** (cost of attraction/conversion): call center expensive (500-2000 rubles), online cheap (<100 rubles).
- **LTV** = ARPU × average subscriber lifetime - show how the bundle increases LTV.
- **Churn rate** target: a decrease by X% gives Y million rubles. additional revenue.

4. **Define pilot metrics:**
- Conversion to bundle (% of those offered).
- ARPU delta (growth of the average bill).
- Churn rate 3/6/12 months after the transition.
- NPS after contacting the call center.
5. **Save the output** in the current working directory as `telecom-subscriber-[context].md`.

## Output Format

```
## Product specification: [Name of tariff/bundle/mechanics]

### Product Description
- **Type:** [Bundle / Tariff / Anti-churn offer / Upsell]
- **Target segment:** [description]
- **Anchor service:** [Internet / TV / mobile]

### Package contents
| Service | Options | Price separately | Price in bundle |
|--------|----------|--------------|--------------|
| Internet | 500 Mbps | 800 rub./month | — |
| TV | 200 channels, 4K | 400 rub./month | — |
| **Bundle** | All inclusive | 1200 rub./month | **990 RUR/month** |

### Unit-economy
- ARPU up to: [X] rub. → ARPU after: [Y] rub. (+Z%)
- CAC: [amount] rub. (channel: [online/call center])
- Payback period: [N] months

### Pilot Success Metrics
- Bundle conversion ≥ [X%]
- Churn after 6 months ≤ [Y%]
- NPS ≥ [Z]
```

## Rules and restrictions
- The bundle discount versus individual services must be tangible - otherwise there is no motivation to switch.
- The retention offer should not be visible to new subscribers - otherwise everyone will “leave” for the discount.
- Anti-churn scoring is more important than mass calling: don’t touch loyal ones, don’t irritate them.
- Take into account the regulations: prohibition of auto-subscriptions without explicit consent (Federal Law “On Communications”).

## Skill success metrics
- The specification contains the calculation of ARPU delta and payback period.
- There is a clear distinction: what the subscriber receives and why it is better than the current tariff.
- The retention offer does not create adverse selection (only those leaving receive a discount).

## Rules


- Write in English.
