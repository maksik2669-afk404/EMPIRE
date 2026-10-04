---
name: marketplace-model
description: 
argument-hint: [concept or idea of ​​a two-sided marketplace]
allowed-tools: Read, Write
preset: marketplace
lifecycle: any
business-model: any
domain: marketplace
stage: any
output-artifact: document
---

# Marketplace Business Model

Create a structured analysis of the business model of a two-sided marketplace. This skill helps the product design a balanced platform economy, solve the problem of cold start of supply and demand, calculate optimal commissions and determine key liquidity metrics.

## Process

1. **Define the sides of the platform.** Who supplies value (Supply / Sellers, performers) and who consumes it (Demand / Buyers, customers)?
2. **Define the type of marketplace.** (Transactional - WB/Ozon, lead generation - Profi/Avito, sharing - Airbnb, SaaS-enabled - when one of the parties uses the platform software).
3. **Develop a cold start strategy (Chicken and Egg).** How to attract the first party without the presence of the second? (Examples: subsidizing one side, creating “Single-Player Mode” value through useful software, aggregating open supply data).
4. **Design a monetization model.** What is the platform commission (take rate)? Who pays it - the buyer, the seller or both? Are there additional sources of income (subscriptions, paid card promotion, logistics services)?



## Output Format

```
## 

### 1. Architecture of the parties (Demand & Supply)
- **Demand side (Buyers):** [who they are, what is the frequency of purchase, average bill, key motivation to come to the platform]

- **Marketplace type:** [Transactional / Classifieds / On-demand / SaaS-enabled]

### 2. Strategy for solving the “Chicken and the Egg” problem (Cold start)

- **Cold start tactics:**
- *Subsidizing:* [for example, we give free leads to specialists at the start or guarantee a minimum income for taxi drivers]
- *Single-player tool:* [for example, a CRM system for beauty salons that works without customers from the marketplace]
- *Creating an artificial offer:* [ad parsing, manual onboarding of partners]

### 


- Promotion of offers (advertising model, paid promotion of advertisements).
- Logistics/financial services (delivery by the platform, transaction insurance, acquiring).
- SaaS subscription for sellers (CRM, advanced analytics).

### 

- **Seller Liquidity:** % of active product cards or performers that made at least one sale over a period of time (active assortment).
- **Match Rate / Fill Rate:** % of requests for services to which at least one contractor responded, or time until the first response.

### 

- **Counter-bypass measures:**

- Cumulative value (performer rating, order history, which gives him new orders).


### 6. Key business model risks
- **Risk of imbalance:** an excess of sellers in the absence of buyers (and vice versa). How to balance marketing.
- **Supply Quality:** how we protect the buyer from low-quality goods/services (ratings, reviews, moderation).
```

## Rules


- Challenge abstract liquidity indicators. “We have a lot of users” is not a liquidity metric. The metric is the conversion of a visit to a purchase or time to receive a service.
- Take Rate must be economically justified for sellers. Too high a commission will push them to competitors or offline. Too low and will not cover the CAC of the platform.
- Write in English.

## 

### Outcome metric
**successful transactions/matches, GMV with healthy take rate, liquidity.** Main result and value.

### Input metrics
**supply coverage, demand coverage, search success, time-to-first-match, reply rate.** Controlled outcome levers.

### 


### Diagnostic metrics
**liquidity by geo/category/price/time, supply quality, buyer conversion, seller activation.** Where to look for the reason.

### 
**buyer_id, seller_id, listing_id, category, geo, search_id, contact/match/transaction events.** What data is needed.

### Decision rules


### Universal Metric Rule
If you are proposing a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How ​​often do we watch it?**

4. **What is the decision threshold?**
