---
name: catalog-strategy
description: Develop a product catalog management strategy (Catalog Strategy) in retail or e-commerce. The input is the product structure, the output is the specification: taxonomy and classification, search personalization logic, optimization of Long Tail products and catalog quality metrics.
argument-hint: [description of product catalog and assortment structure]
allowed-tools: Read, Write
preset: e-commerce
lifecycle: any
business-model: any
domain: ecom-retail
stage: any
output-artifact: document
---

# Catalog management strategy (catalog-strategy)

Design and optimize the structure of a product catalog for retail chains, e-grocery or large e-commerce platforms. The skill helps the product build a clear taxonomy, set up storefront personalization rules, manage a low-demand assortment (Long Tail) and control the quality of content.

## Process

1. **Design the catalog structure (Taxonomy & Navigation).** Describe categories, subcategories, facet filters (for example: brand, color, size, fat content for milk).
2. **Set up a catalog personalization rule.** What is the algorithm for sorting goods on a shelf for a specific user? (purchase history, related products).
3. **Describe the management of Long Tail (long tail of the assortment).** How to merchandise products with low purchase frequency so that they find their buyer without overloading the main interface (markdowns, selections, smart search).
4. **Define catalog quality metrics (Catalog KPIs).** Search-to-Detail Rate (conversion from search to card), Fill Rate of characteristics, share of products without photos.
5. **Save the output** in the current working directory as `catalog-strategy-[product-name].md`.

## Output Format

```
## Catalog management strategy: [Brand]

### 1. Taxonomy & Facets Architecture
- **Hierarchy of categories:** [for example: Products -> Dairy products -> Yoghurts].
- **Facet filtering:** [list of key filters for the category].
- **Data Completeness:** the requirement to fill out 100% of the required characteristics before publishing the SKU on the storefront.

### 2. Personalization of the showcase (Catalog Personalization)
- **Sorting algorithm:** [priority of goods based on the client’s past purchases in this category (repurchase), then popular in the region].
- **Block of recommendations:** “They buy with this product” (cross-sell based on association rules).

### 3. Long Tail Strategy
- **Problem:** 80% of SKUs are rarely purchased (low turnover).
- **Solution:**
- Automatic display of Long Tail products in search results for low-frequency queries.
- Inclusion in thematic personalized selections (“Healthy breakfast”, “For the garden”).

### 4. Catalog quality metrics (Catalog KPIs)
- **Search Relevance Rate:** share of clicks on the first 5 search results.
- **Listing Completeness Score:** average % completion of the product card (photo + description + properties). Target > 95%.
- **Zero Search Results Rate:** % of search queries with zero results (target < 1.5%).
```

## Rules

- Prohibit the publication of products with blank key characteristics or without photographs. A card without a photo reduces purchase conversion by 80%.
- Be sure to consider Long Tail products. You can’t overload the main storefront with them, but they should be easy to find through a high-quality text search.
- Write in English.

## Metrics (E-commerce / Retail)

### Outcome metric
**contribution margin per order, repeat purchase, paid orders.** Main result and value.

### Input metrics
**checkout conversion, add-to-cart, availability, delivery promise accuracy, promo conversion.** Managed outcome levers.

### Guardrails
**gross margin after returns, refund rate, return abuse, stockout, payment failure.** What cannot be worsened.

### Diagnostic metrics
**funnel drop-off, category, device, payment method, delivery slot, promo dependency.** Where to look for the reason.

### Instrumentation
**cart_id, order_id, SKU, inventory, payment events, return/refund reason.** What data is needed.

### Decision rules
- Ship/Iterate/Kill

### Universal Metric Rule
If you are proposing a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How ​​often do we watch it?**
3. **What events count it?**
4. **What is the decision threshold?**
5. **How ​​can it be spoiled or screwed up?**