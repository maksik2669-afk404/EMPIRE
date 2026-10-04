---
name: returns-management
description: Develop a product strategy and optimize the process of product returns (Reverse Logistics). The input is a description of the returns funnel, and the output is a specification: return logic for the customer (returns UX), fraud protection, reverse logistics to the warehouse, and return economics.
argument-hint: [description of return processes or e-commerce project]
allowed-tools: Read, Write
preset: retail-ops
lifecycle: any
business-model: any
domain: ecom-retail
stage: any
output-artifact: document
---

# Returns Management (returns-management)

Optimize the processes of product returns (Reverse Logistics) in e-commerce, marketplaces, or retail. The skill helps a product manager design a customer-friendly returns interface (Returns UX), implement mechanisms to prevent fraud (product swapping, returning worn clothing), organize the logistics of returning goods back to the warehouse/pickup point, and minimize the business's financial losses on logistics.

## Process

1. **Design the user return journey (Returns UX).**
- How does a customer report a return? (Application request -> select reason -> upload photo of the defect -> choose return method: courier, pick-up point, mail).
- Metric: Time-to-Refund (time from shipment of the product to the refund to the customer).
2. **Develop rules for fraud protection (Anti-Fraud).**
- *Item swapping:* checking the barcode/tag at the pickup point upon receipt. Photographic documentation of the item by the pickup point employee.
- *Wardrobing fraud:* returning worn items. Requirements for preserving the commercial appearance, tags, and seals.
- *Blacklist:* restriction of the ability to return without verification for customers with an abnormally high return rate (Return Rate > 80%).
3. **Describe the reverse logistics.** Product path: Pickup point -> Sorting center -> Defective goods warehouse / Resale warehouse (restoring packaging, dry cleaning, markdown).
4. **Calculate the return unit economics.** Cost of reverse logistics + salary of the PVZ employee + salary of the warehouse receiver + product markdown.
5. **Save the output** in the current working directory as `returns-spec-[product-name].md`.

## Output Format

```
## Returns Process Specification: [Brand Name]

### 1. User flow for returns (Returns UX)
- **Processing mechanics:** Application in the buyer's personal account.
- The buyer selects a product from the order history, specifies the quantity, and chooses the reason for the return from the reference guide.
- Mandatory requirement: for the reasons 'Defect' or 'Incomplete set,' it is necessary to upload 2-3 photos and a short video.
- **Methods of delivery:** Drop off at any branded pick-up point for free or call a courier for 199 rubles (deducted from the refund amount).

### 2. Protection against fraud and scam (Anti-Fraud Gateways)

| Risk Category | Validation Rule | Action at Pickup Point / Warehouse |
|-----------------|-------------------|--------------------------|
| **Brand substitution** | Comparison of the box weight and barcode on the original tag (RFID tags) | Pickup point employee scans the tag; if there is a mismatch, the system blocks the "Accept" button |
| **Worn items** (Wardrobing) | Visual inspection for absence of signs of wear, perfume smell, presence of factory seal | Refusal to accept the return on the spot with issuance of a motivated refusal form |
| **Systematic Fraud** | Calculation of the individual Return Rate of a client. If the Return Rate > 75% with purchases of 10 or more items | Disabling the “Free Return” option. Return shipping at the customer’s expense |

### 3. Reverse Logistics and Sorting (Reverse Logistics)
- **Entry point:** The pickup point receives the goods and packs them in a security bag.
- **Sorting Center:** Distribution of goods into 3 streams:
- *Stream A (Fit for sale):* goods in perfect condition, returned to active warehouse shelves.
- *Stream B (Discount/Repackaging):* requires box replacement or minor repair. Sold at a discount in the 'Discount' section.
- *Stream C (Waste/Disposal):* write-off and return to the supplier.

### 4. Unit Economics of Returns (Return Cost Analysis)
- **Return Rate (target):** [for example, 22% in the Clothing category].
- **Cost structure per return:**
- *Transport from pick-up point to warehouse:* 120 RUB.
- *Labor cost for acceptance and sorting:* 40 rubles.
- *Depreciation of goods (loss of value due to packaging damage):* on average 10% of COGS (about 150 RUB).
- *Total cost of one return:* **310 rubles** (these expenses should be included in the product price as a reserve for returns).
```

## Rules

- Do not allow automatic unconditional refunds (instant refund) until the moment of physical receipt and inspection of the goods at the pickup point or warehouse for expensive categories (> 5,000 rubles). This creates ideal conditions for fraudsters who will send empty boxes.
- The PVZ returns acceptance interface should contain a step-by-step checklist for inspecting the product with mandatory photo documentation of its condition.
- Write in English.

## Metrics (E-commerce / Retail)

### Outcome metric
**contribution margin per order, repeat purchase, paid orders.** Main result and value.

### Input metrics
**checkout conversion, add-to-cart, availability, delivery promise accuracy, promo conversion.** Managed levers of outcome.

### Guardrails
**Gross margin after returns, refund rate, return abuse, stockout, payment failure.** What cannot be worsened.

### Diagnostic metrics
**funnel drop-off, category, device, payment method, delivery slot, promo dependency.** Where to look for the reason.

### Instrumentation
**cart_id, order_id, SKU, inventory, payment events, return/refund reason.** What data is needed.

### Decision rules
- Ship / Iterate / Kill

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**