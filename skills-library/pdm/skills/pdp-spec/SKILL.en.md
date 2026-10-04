---
name: pdp-spec
description: Specification for Product Detail Page (PDP) in E-commerce.
argument-hint: [concept of product detail page or e-com category]
allowed-tools: Read, Write
preset: e-commerce
lifecycle: any
business-model: b2c
domain: e-commerce
stage: any
output-artifact: document
---

# Product Detail Page Specification (pdp-spec)

Design product requirements for an E-commerce Product Detail Page (PDP) across Fashion, Beauty, Electronics, or General Retail: rich media gallery, SKU/size variant selection, sizing guides, social proof, and high-converting purchase triggers.

## Process

1. **Design Media Showcase & Gallery:**
   - On-model photography, video covers, 360-degree interactive spin.
   - High-resolution fullscreen zoom, user-generated review photo integration.
   - Load time optimization (lazy-loading, WebP/AVIF formats, global CDN).

2. **Design SKU Variant & Inventory Selection:**
   - Color swatches, size selector, volume/spec choices.
   - Live inventory status: low-stock badges, local warehouse stock availability, dynamic delivery promises.
   - For Fashion: Interactive size charts and fit recommendation engines (height/weight parameters).

3. **Design Rich Content & Service Guarantees:**
   - Material composition, ingredients, washing/care instructions, compliance certificates.
   - Delivery timelines, returns policies, and Try-Before-You-Buy terms.

4. **Design Reviews & Social Proof (UGC):**
   - Star ratings breakdown, verified buyer badges, attribute-based review filters (reviewer height, skin type, true-to-size indicator).
   - Official brand reply badges.

5. **Formulate Key PDP Metrics:**
   - Apply the mandatory 5-question test to every metric.

## Output Format

```markdown
# Product Detail Page (PDP) Specification: [Category / Brand]

## 1. Above the Fold Layout
- **Media Gallery:** Swiper carousel with auto-playing video cover snippet.
- **Header Info:** Brand name, Product title, SKU ID, Star rating & review count.
- **Pricing Box:** Current price, struck-through MSRP, discount percentage, loyalty tier price.

## 2. Variant Selector (SKU Matrix)
| Attribute | UI Pattern | Out-of-Stock Fallback |
| :--- | :--- | :--- |
| Color | Circular swatch preview with active ring | Greyed-out strikethrough |
| Size | Button grid (XS, S, M, L, XL) | "Notify When Available" (Back in Stock modal) |
| Sizing Guide | Measurement table | "Find My Size" quiz modal |

## 3. Purchase Block & Service Badges
- **Primary CTA:** "Add to Bag" (Sticky Add-to-Cart bar on scroll).
- **Delivery Promise:** "Free next-day delivery to pickup point if ordered before 8 PM".
- **Guarantees:** "Try-on available at pickup", "Easy 14-day returns".

## 4. Key Metrics
- **PDP-to-Cart Conversion Rate:** Share of PDP sessions resulting in Add to Cart.
- **Gallery Engagement Rate:** % of users scrolling past 3 photos or playing video.
- **Size Calculator Usage:** Share of buyers utilizing fit prediction tools.
- **PDP Bounce Rate:** Single-page bounce percentage without interaction.
```

## Guardrails

- Focus on maximizing cart adds while reducing return rates driven by incorrect sizing.
- Do not use em-dashes. Use colons, periods, or standard hyphens.
- Every metric must answer the 5-question rule.
