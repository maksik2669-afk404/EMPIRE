---
name: matching-algorithm
description: Design or analyze an algorithm for matching supply and demand in real time. The input is the concept of an on-demand service (taxi, delivery, cleaning), the output is a structured specification of the algorithm: dispatching, dynamic pricing (Surge Pricing), geo-zoning and market balancing.
argument-hint: 
allowed-tools: Read, Write
preset: marketplace
lifecycle: any
business-model: any
domain: marketplace
stage: any
output-artifact: document
---

# Matching algorithms in On-demand services



## Process



3. **Develop dynamic pricing (Surge Pricing).** What are the triggers for turning on a markup? (If the number of free performers in the zone < X with an increase in orders > Y, the price is multiplied by a coefficient).




## Output Format

```
## 

### 

- **Input parameters of the algorithm:** [customer coordinates, coordinates and direction of movement of free performers, their rating, class of service, ETA]

### 2. Dynamic Pricing (Surge Pricing & Balance)
- **Geo-analysis grid:** dividing the map into hexagons (Uber H3 indexes, resolution detail level, for example, H3 Resolution 8).
- **Algorithm for calculating the coefficient (Surge Multiplier):**




### 
- **Destination Prioritization:**
- `Executor speed = Distance weight (ETA) × Rating weight × Transport type coefficient`.

- **Prevention of idle mileage:** algorithms for assigning an order during the completion of the current trip (Back-to-back orders).

### 4. Behavioral incentives of the parties (Marketplace Incentives)
- **For performers:** additional payments for work in “hot” hexagons (Surge zones), bonuses for completing goals for the number of orders per day.


### 
- **Match Rate / Fill Rate:** % of orders for which a contractor has been successfully assigned.

- **Driver Acceptance Rate:** % of proposed orders that the performers accepted (low % indicates unfavorable rates or bad routes).
- **Pickup ETA:** average time for the courier/driver to arrive at the client after the appointment.
```

## Rules

- Avoid Greedy-matching (assigning to the closest one at a given second) in high-traffic markets. Batching reduces the average feed distance across the system by 15-20% compared to Greedy.


- Write in English.

## 

### Outcome metric


### Input metrics
**supply coverage, demand coverage, search success, time-to-first-match, reply rate.** Controlled outcome levers.

### Guardrails
**seller margin, dispute rate, cancellation rate, fraud rate, leakage/disintermediation.** What cannot be worsened.

### 
**liquidity by geo/category/price/time, supply quality, buyer conversion, seller activation.** Where to look for the reason.

### Instrumentation
**buyer_id, seller_id, listing_id, category, geo, search_id, contact/match/transaction events.** What data is needed.

### 
- Ship/Iterate/Kill

### Universal Metric Rule

1. **Who owns this metric?**
2. **How ​​often do we watch it?**
3. **What events count it?**

