---
name: c2c-dynamics
description: Design C2C liquidity balance, ratings and local network effects.
argument-hint: [description of the C2C platform and liquidity problems in the regions]
allowed-tools: Read, Write
preset: marketplace
lifecycle: any
business-model: any
domain: marketplace
stage: any
output-artifact: document
---

# Dynamics of C2C platforms (c2c-dynamics)

Optimize the balance of supply and demand on peer-to-peer (C2C) platforms, taking into account local network effects.

## Process
1. **Determine the critical mass of liquidity (Liquidity Threshold).** How many ads/performers are needed in the geo-zone for the buyer to find the service.
2. **Design a system of ratings and reviews.** Protection against cheating, smoothing out the ratings of new users.
3. **Save the output** in the current working directory as `c2c-dynamics-[context].md`.

## Output Format
```
## C2C liquidity analysis: [Service]
- **Critical accessibility radius:** [for example, 5 km for sharing scooters].
- **Mechanics for stimulating liquidity:** increased bonuses for sellers in scarce areas.
```

## Metrics (Marketplace / Classifieds)

### Outcome metric
**successful transactions/matches, GMV with healthy take rate, liquidity.** Main result and value.

### Input metrics
**supply coverage, demand coverage, search success, time-to-first-match, reply rate.** Controlled outcome levers.

### Guardrails
**seller margin, dispute rate, cancellation rate, fraud rate, leakage/disintermediation.** What cannot be worsened.

### Diagnostic metrics
**liquidity by geo/category/price/time, supply quality, buyer conversion, seller activation.** Where to look for the reason.

### Instrumentation
**buyer_id, seller_id, listing_id, category, geo, search_id, contact/match/transaction events.** What data is needed.

### Decision rules
- Ship/Iterate/Kill

### Universal Metric Rule
If you are proposing a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How ​​often do we watch it?**
3. **What events count it?**
4. **What is the decision threshold?**
5. **How ​​can it be spoiled or screwed up?**

## Rules

- Write in English.
