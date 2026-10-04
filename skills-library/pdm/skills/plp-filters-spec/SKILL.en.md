---
name: plp-filters-spec
description: Specification for Product Listing Page (PLP), faceted filters, and catalog navigation in E-commerce.
argument-hint: [concept of catalog listing or e-com filter system]
allowed-tools: Read, Write
preset: e-commerce
lifecycle: any
business-model: b2c
domain: e-commerce
stage: any
output-artifact: document
---

# Product Listing Page & Filtering Specification (plp-filters-spec)

Design requirements for an E-commerce catalog and Product Listing Page (PLP): multi-facet filtering, smart sorting heuristics, responsive grid card states, Quick View / Quick Add interactions, and pagination dynamics.

## Process

1. **Design Faceted Filtering Architecture:**
   - Deep attributes: brand multi-select, price range (dual slider + numeric inputs), sizes, color palettes, materials, seasonal collections, in-stock status.
   - Quick-filter chips: "Same-Day Delivery", "On Sale", "Best Sellers", "Premium Brands".
   - Dynamic inventory recalculation updating result counts instantly on checkbox toggle without full page reload.

2. **Define Sorting Logic (Sort Order Rules):**
   - Popularity ranking (algorithmic blend of revenue velocity, click-through rate, stock depth), discount depth, price low-to-high/high-to-low, new arrivals, average customer rating.

3. **Design Grid Product Card Interactions:**
   - Desktop hover carousel cycling through product angles.
   - 1-click Quick Add trigger with size flyout overlay.
   - Wishlist toggle animation.
   - Promotional badges: "New Season", "-30% Off", "Express Delivery", "Exclusive".

4. **Design Navigation & Pagination Experience:**
   - Infinite scrolling with "Load More" milestone breaks every 3 viewports to maintain user orientation and footer access.
   - State preservation in URL query parameters for seamless deep linking and browser back-button support.

5. **Formulate PLP Discovery Metrics:**
   - Apply the mandatory 5-question test to every metric.

## Output Format

```markdown
# Product Listing Page (PLP) Specification: [Category Name]

## 1. Faceted Filtering System
- **Form Factor:** Left sidebar on desktop, sticky slide-up bottom sheet on mobile.
- **Application Logic:** Multi-select checkboxes with sticky "View [N] Items" footer CTA.
- **Top Quick Chips:** "Next-Day Delivery", "Sale Items", "Brand Focus".

## 2. Sorting Heuristics
| Sort Option | Ranking Formulation | Usage Priority |
| :--- | :--- | :--- |
| Best Match / Popularity | 14-day sales volume * 0.5 + Product views * 0.3 + In-stock ratio * 0.2 | Default |
| Discount Depth | Relative discount percentage off MSRP | User selected |
| Newest | Warehouse arrival timestamp (last 30 days) | User selected |

## 3. Grid Card Capabilities
- **Hover Preview:** Seamlessly cycle through up to 4 image angles on hover.
- **Quick Add:** Size selection modal on "Add to Bag" click without opening full PDP.
- **Scarcity Alerts:** "1 size left" badge to trigger urgency.

## 4. Key Metrics
- **PLP-to-PDP Click-Through Rate (CTR):** Share of catalog sessions clicking through to PDP.
- **Filter Engagement Rate:** % of users applying at least one filter or sort option.
- **Quick-Add Conversion:** Share of bag additions made directly from listing.
- **Zero-Results Rate:** % of filter/search combinations yielding 0 products.
```

## Guardrails

- Prevent Zero-Results dead ends by providing automated filter relaxation recommendations.
- Do not use em-dashes. Use colons, periods, or standard hyphens.
- Every metric must answer the 5-question rule.
