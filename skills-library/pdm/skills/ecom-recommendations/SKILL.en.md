---
name: ecom-recommendations
description: Specification for product recommendations, cross-sell engines, and Shop the Look / Total Look in E-commerce.
argument-hint: [concept of product recommendations or curated sets]
allowed-tools: Read, Write
preset: e-commerce
lifecycle: any
business-model: b2c
domain: e-commerce
stage: any
output-artifact: document
---

# E-com Product Recommendations & Shop the Look (ecom-recommendations)

Design an E-commerce recommendation engine: cross-sell carousels on PDP, curated "Shop the Look" (Total Look) outfit builders, personalized homepage discovery, and cart upsell triggers.

## Process

1. **Map Recommendation Placements & Objectives:**
   - **Product Detail Page (PDP):** "Pairs Well With / Complete the Look", "Similar Alternatives".
   - **Cart / Checkout:** Impulse accessories, threshold cross-sell ("Add $15 for Free Shipping").
   - **Homepage Feed:** "Recently Viewed", "Personalized For You", "Trending in Your Favorite Category".

2. **Design Shop the Look (Total Look Builder):**
   - Interactive editorial photography with shoppable hotspots on garments/accessories.
   - Quick size selector modal and 1-click "Buy Full Outfit (-10% Bundle Discount)" CTA.
   - Automated fallback to stylistic substitutes when specific sizes run out of stock.

3. **Design Recommendation Heuristics & Filtering:**
   - Collaborative filtering ("Shoppers who bought this also bought...").
   - Content-based embeddings matching brand tier, color palette, aesthetics, and category compatibility.
   - Business guardrails: exclude past purchases, zero-stock items, and out-of-season items.

4. **Design UI & Micro-interactions:**
   - Smooth horizontal swipe carousels preserving scroll positions.
   - Bundle savings callouts.

5. **Formulate Recommendation Revenue Metrics:**
   - Apply the mandatory 5-question test to every metric.

## Output Format

```markdown
# Product Recommendations Specification: [Project Name]

## 1. Recommendation Placement Grid
| Placement | Module Name | Algorithm Engine | Business Objective |
| :--- | :--- | :--- | :--- |
| Product Page | Complete the Look | Stylist curated set + Visual AI embeddings | Items per order expansion |
| Product Page | Similar Styles | Vector text/image similarity | Churn prevention on missing size |
| Bag Drawer | Free Shipping Booster | Complementary low-ticket items under $25 | Average Order Value (AOV) lift |

## 2. Shop the Look Interaction Model
- **Hotspots:** Interactive tap pins on outfit photos displaying name, price, and instant size dropdown.
- **Bundle Offer:** "Get the complete look for $189 instead of $210".

## 3. Business Guardrails
- Strictly suppress items unavailable in the customer's localized fulfillment hub.
- Prevent gender/category mismatch based on explicit customer preferences.

## 4. Key Metrics
- **Recommendation CTR:** Click-through rate across recommendation carousels.
- **Recommendation Revenue Share:** % of total GMV attributed to recommendation interactions.
- **AOV Lift:** Delta in average order value for baskets containing recommended items.
- **Units per Transaction (UPT):** Average item depth per closed order.
```

## Guardrails

- Ensure local warehouse availability to prevent recommending items with delayed delivery.
- Do not use em-dashes. Use colons, periods, or standard hyphens.
- Every metric must pass the 5-question test.
