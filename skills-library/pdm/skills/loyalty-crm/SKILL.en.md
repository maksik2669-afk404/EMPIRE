---
name: loyalty-crm
description: 
argument-hint: [description of retail product and loyalty goals]
allowed-tools: Read, Write
preset: e-commerce
lifecycle: any
business-model: any
domain: ecom-retail
stage: any
output-artifact: document
---

# 

Design the mechanics of a loyalty program and CRM campaigns for personal offers for retail chains, e-grocery or FMCG services. The skill helps the product set up the rules for calculating bonuses, the logic of user segmentation by RFM (Recency, Frequency, Monetary), design trigger funnels for customer return and calculate the financial efficiency of the program (Uplift revenue vs. marginal losses on discounts).

## Process


- *Direct cashback/bonuses:* % return with points to the loyalty card.
- *Tiered:* status levels (Silver, Gold) depending on spending over the past month.
- *Paid loyalty:* paid subscription bundle for free delivery and increased cashback (for example, X5 Package).

- *Sleeping (Churn risk):* haven’t bought for a long time, high average bill. Mechanics: reactivation with increased cashback for 3 days.

3. **Describe trigger communications (CRM map).** At what points does push/email/SMS hit: abandoned cart, registration anniversary, drop in visit frequency below the historical average.


- *Margin Erosion:* how much net margin we lose by giving discounts to those who would have bought without them.
- *Incremental Revenue (Uplift):* additional revenue from changing user behavior.


## Output Format

```
## 

### 

- **Basic reward rules:** [for example, 1% points for any purchases, 5% in three favorite categories].


### 2. RFM segmentation and CRM mechanics


|------------------|--------------|------------------|--------------------------------------------|----------------|
| **1. Loyal Core** | R <= 7 days, F >= 4 times/month | Increase in average check | 10% discount on a related category with a receipt of 1,500 rubles. | In-app push |
| **2. Churn risk** | R > 30 days, F previously high | Return to application | “We are giving 300 points to your loyalty card. Hurry up to write off in 5 days" | SMS/Viber |
| **3. Newbies** | R <= 3 days, F = 1 purchase | Second purchase (activation) | Cashback 20% points on your second purchase within a week | Push + Email |

### 

- *Condition:* items have been added to the cart, but the order has not been placed within 2 hours.
- *Action:* sending a Push with a reminder: “Your cart is waiting for you. We’ll deliver in 30 minutes!”

- *Condition:* the user does not place an order during a period exceeding his average purchase interval by 50%.


### 

- **Redemption Rate:** percentage of points redeemed.
- **Margin Erosion Rate:** % of discounted transactions made by loyal users without a trigger (margin loss). Must be kept < 15%.
```

## Rules

- Prohibit launching discounts “for everyone” without a control group (Holdout Group). Without a dedicated cohort of users (usually 5-10%) who don't receive any emails or discounts, it's impossible to prove the ROI of CRM campaigns (you won't know if people bought because of the newsletter or just because they were hungry).
- Be sure to introduce a limit on the lifetime of loyalty points. Without this, you will accumulate a huge balance sheet debt to customers (unpaid points obligations).
- Write in English.

## Metrics (E-commerce / Retail)

### Outcome metric
**contribution margin per order, repeat purchase, paid orders.** Main result and value.

### Input metrics
**checkout conversion, add-to-cart, availability, delivery promise accuracy, promo conversion.** Managed outcome levers.

### Guardrails


### Diagnostic metrics
**funnel drop-off, category, device, payment method, delivery slot, promo dependency.** Where to look for the reason.

### Instrumentation
**cart_id, order_id, SKU, inventory, payment events, return/refund reason.** What data is needed.

### 


### Universal Metric Rule

1. **Who owns this metric?**

3. **What events count it?**

5. **How ​​can it be spoiled or screwed up?**