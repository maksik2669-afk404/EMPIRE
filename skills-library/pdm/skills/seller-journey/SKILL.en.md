---
name: seller-journey
description: Design or analyze the path of a merchant/seller on a marketplace or platform. Input — a description of the platform or sellers' problems; output — a structured analysis of the seller funnel: from onboarding and first sale to scaling and retention.
argument-hint: [description of the marketplace or sellers' problem]
allowed-tools: Read, Write
preset: marketplace
lifecycle: any
business-model: any
domain: marketplace
stage: any
output-artifact: document
---

# The Seller's Journey on the Marketplace (Seller Journey)

Create a specification and a seller (merchants/sellers) journey map for a two-sided platform or marketplace (like WB, Ozon, Avito, Yandex Market). The skill helps the product manager focus on the B2B component of the platform: how to onboard sellers quickly and cheaply, encourage them to make their first sales, and retain them on the platform to ensure market liquidity.

## Process

1. **Determine the type of platform and sellers.** Who is selling (private individuals C2C, self-employed, small businesses, large brands)? What are they selling (physical goods, services, digital content)?
2. **Break down the seller's journey into key phases.** Onboarding/Registration → Activation/First listing → First sale → Scaling/Retention.
3. **Identify the barriers at each stage.** Where is the biggest drop-off and why (complex legal entity verification, unclear logistics, high commission).
4. **Design the key metrics of the seller funnel.** Highlight Time-to-first-sale, GMV per seller, active sellers, seller churn rate.
5. **Describe the B2B toolkit of a seller.** What does a seller need for scaling (promotion/advertising, sales analytics, price/discount management, API integration).
6. **Save the output** in the current working directory as `seller-journey-[platform-name].md`.

## Output Format

```
## Seller Journey: [Platform Name]

### 1. Seller Profile and Value Proposition
- **Type of sellers:** [C2C users / small B2B business / large retailers]
- **Value Proposition for the seller:** why they should come to us (access to the audience, easy delivery, low commission).
- **Moderation complexity:** [what checks of legal entities/individual entrepreneurs we conduct at the entry]

### 2. Seller Journey Map (Activation Funnel)

| Stage of the journey | What the seller does | Key barrier (Friction) | Stage success metric |
|-----------|---------------------|----------------------------|-----------------------|
| **1. Onboarding** | Creates an account, uploads documents | Complex legal checks, digital signature | Conversion to verification |
| **2. First Listing** | Uploads product cards | Complex templating system, card moderation | Time-to-first-listing |
| **3. First Sale** | Receives order, ships | Unclear logistics (FBO/FBS), lack of first reviews | Time-to-first-sale |
| **4. Scaling** | Spends money on advertising, analyzes inventory | Complex ad account, cash flow gaps | GMV per Seller |

### 3. Key metrics of a B2B platform
- **Time-to-First-Sale (TTFS):** the average time from completing registration to the first successful sale. The main metric of the "Aha moment" for the seller.
- **Seller Retention / Churn:** % of sellers who made at least one sale in the current month out of those who sold in the past.
- **Concentration Risk:** what share of the platform's total GMV belongs to the top 5% of sellers (high concentration is dangerous for the platform).
- **Adoption Rate of advertising tools:** % of sellers using paid product listing promotion.

### 4. Seller Tools (Product Capabilities)
- **Personal Account (Seller Portal):** requirements for the order and inventory management interface.
- **Seller API:** the need to integrate with sellers' accounting systems (1C, MyWarehouse).
- **Promotion tools:** advertising campaigns, participation in overall platform promotions, search boosting.

### 5. Platform Risks and Fraud Protection
- **Product fraud:** sale of replicas, counterfeits, low-quality goods (brand moderation system, test purchases).
- **Financial fraud:** review boosting and self-purchases (detection of abnormal activity, protection against rating manipulation).
- **Collusion:** fraud by sellers with buyers (protection of the transaction through the platform's escrow mechanisms).
```

## Rules

- Remember the 'chicken and egg problem' on marketplaces. Sellers will not come if there are no buyers, and buyers will not come if there is no assortment. The specification should answer the question: how does this seller journey help balance the liquidity of the marketplace at early stages.
- Time-to-First-Sale (TTFS) is the holy grail for a marketplace. If a seller registers and sells nothing within 30 days, there is an 80% chance they will leave forever. Demand the elaboration of the seller's first steps to maximize the acceleration of the first sale (for example, initial free boosting of products).
- Don't make the B2B dashboard overly complicated for small sellers. Separate the flow for 'Individual Entrepreneur with 3 products' and 'Distributor with 10,000 SKUs'.
- Write in English.

## Metrics (Marketplace / Classifieds)

### Outcome metric
**successful transactions/matches, GMV with healthy take rate, liquidity.** The main result and value.

### Input metrics
**supply coverage, demand coverage, search success, time-to-first-match, reply rate.** Managed levers of outcome.

### Guardrails
**seller margin, dispute rate, cancellation rate, fraud rate, leakage/disintermediation.** What cannot be worsened.

### Diagnostic metrics
**liquidity by geo/category/price/time, supply quality, buyer conversion, seller activation.** Where to look for the cause.

### Instrumentation
**buyer_id, seller_id, listing_id, category, geo, search_id, contact/match/transaction events.** What data is needed.

### Decision rules
- Ship / Iterate / Kill

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**