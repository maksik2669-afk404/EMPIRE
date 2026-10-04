---
name: ecom-checkout-split
description: Specification for shopping bag, multi-shipment split orders, pickup points (PUDO), and Try-Before-You-Buy.
argument-hint: [concept of split checkout, pickup network, or try-on flow]
allowed-tools: Read, Write
preset: e-commerce
lifecycle: any
business-model: b2c
domain: e-commerce
stage: any
output-artifact: document
---

# E-com Bag, Split Orders & Pickup Checkout (ecom-checkout-split)

Design an E-commerce checkout experience: multi-warehouse order splitting, interactive pickup point maps (PUDO / lockers), courier time slots, Try-Before-You-Buy mechanics, and partial buyout recalculations.

## Process

1. **Design Multi-Shipment Splitting Engine:**
   - Automated routing grouping items across fulfillment centers (Parcel 1: Next-day from local warehouse, Parcel 2: 3-day from regional hub).
   - Clear delivery date and shipping cost transparency per parcel.

2. **Design Interactive Pickup Map (PUDO Selector):**
   - Interactive map with brand stores, partner lockers, and third-party pickup networks.
   - Map filter toggles: "Fitting Rooms Available", "Card Payment on Arrival", "24/7 Access".
   - Scheduled courier delivery window selection (morning, evening, precise 1-hour slots).

3. **Design Try-Before-You-Buy & Partial Purchase Flows:**
   - Order up to 5-10 items with payment authorization or pay-on-arrival.
   - Pickup station workflow: 15-minute fitting session, keep chosen items, hand back unwanted items to operator.
   - Dynamic receipt recalculation charging exclusively for accepted merchandise.

4. **Design Payment Options & Express Checkout:**
   - Instant payment rails, credit cards, BNPL / installment splits, loyalty point redemptions.
   - 1-click checkout for registered customers with saved preferences.

5. **Formulate Checkout & Buyout Metrics:**
   - Apply the mandatory 5-question test to every metric.

## Output Format

```markdown
# Checkout, Split Orders & Pickup Specification: [Project Name]

## 1. Multi-Shipment Splitting Flow
- **Splitting Rule:** In-stock local inventory ships in Package 1; cross-dock supplier items in Package 2.
- **UI Presentation:** Unified single-page checkout clearly partitioned into distinct shipment cards.

## 2. Pickup Network Integration
| Location Type | Fitting Policy | Payment Methods | Capabilities |
| :--- | :--- | :--- | :--- |
| Brand Store / PUDO | Up to 6 garments, fitting booth | Card, Cash, Instant Rail | Instant return, packaging recycling |
| Automated Locker | No fitting | App pre-payment only | QR / Bluetooth contactless pickup |
| Partner Network | Up to 4 garments | Online / Terminal | Content inspection |

## 3. Partial Buyout Orchestration
- **Pre-authorization:** $0 authorization (post-pay) or full hold released post-handover.
- **Fiscalization:** Split invoice generated only for items taken by customer.

## 4. Key Metrics
- **Bag-to-Order Conversion Rate:** Share of cart sessions successfully checking out.
- **Split Acceptance Rate:** % of buyers completing checkout despite multi-package delivery.
- **PUDO Pickup Share:** Ratio of pickup point orders vs home courier delivery.
- **Buyout Rate:** Total revenue retained vs gross ordered merchandise value.
```

## Guardrails

- Minimize friction: consolidate checkout into a seamless single-page experience.
- Do not use em-dashes. Use colons, periods, or standard hyphens.
- Every metric must answer the 5-question rule.
