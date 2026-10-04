---
name: retail-supply-chain
description: Design or analyze algorithms and control logic for supply chains in retail and e-groceries. The input is a description of warehouse/dark store processes or a product availability problem; the output is a structured specification: auto-replenishment, inventory control, minimizing write-offs, and OSA.
argument-hint: [description of the logistics process or the issue of leftovers]
allowed-tools: Read, Write
preset: retail-ops
lifecycle: any
business-model: any
domain: ecom-retail
stage: any
output-artifact: document
---

# Supply Chain Management in Retail (Supply Chain)

Create a detailed requirements specification for an inventory management system, automatic ordering, or warehouse logistics in retail and e-groceries (similar to Samokat, Yandex Lavka, X5, Magnit). Helps the product manager automate the stock replenishment process, minimize spoilage of perishable goods (fresh), and maximize product availability for customers.

## Process

1. **Determine the type of warehouse/location.** (Dark store for express delivery, central distribution center (CDC), or physical supermarket shelf).
2. **Design an auto-replenishment model.** What is the algorithm for calculating the order quantity? (Demand forecast based on historical sales + safety stock + accounting for seasonality, promotions, and weather).
3. **Describe the logic of freshness management (Fresh & Expiry Date).** How does the system manage products with a short shelf life? (FEFO mechanism — First Expired, First Out; automatic price reduction before expiration; write-off of expired products).
4. **Design a product availability metric (OSA - On-Shelf Availability).** How to track that a product is actually available for purchase? How to identify “virtual stocks” (when a product is recorded in the system but is actually stolen or lost in the warehouse).
5. **Determine the key logistics metrics.** Out-of-Stock rate (share of lost sales), Write-off rate (share of write-offs in revenue), inventory turnover (Inventory Turnover), demand forecast accuracy (Forecast Accuracy).
6. **Save the output** in the current working directory as `supply-chain-spec-[product-name].md`.

## Output Format

```
## Supply Chain Specification: [Product Name]

### 1. Supply Chain Architecture and Context
- **Type of logistics hub:** [for example, 15-minute express delivery dark store, 2000 SKUs]
- **Supplier scheme:** [direct deliveries from distributors to the dark store / cross-docking through the DC]
- **Key challenge:** [balance between product availability (OSA) and the level of write-offs for expired items]

### 2. Auto-Replenishment Algorithm (Auto-Replenishment Logic)
- **Reorder formula (Reorder Point):** `Order = Forecast demand for the lead time period + Safety stock - Current inventory - Goods in transit`.
- **Predictive factors:** [which variables the model takes into account: sales trend, day of the week, holidays, weather (affects demand for water/ice cream), local promotions].
- **Order interval (Lead Time):** supply lead (time from ordering from the supplier to receipt at the warehouse).

### 3. Specifics of the Fresh category and Expiry Date Control
- **Assembly management (FEFO):** requirements for the picker interface (darkstore picker app) to select items with the shortest shelf life first.
- **Dynamic markdown engine (Markdown Engine):** automatic creation of a discount (for example, -30%) on products that have less than 20% of their shelf life remaining.
- **Write-off control:** automatic blocking of product sales at the checkout/in the app 1 day before the expiration date.

### 4. Shelf Availability Control (OSA & Virtual Stock)
- **Detection of virtual stock:** an algorithm for identifying discrepancies (for example, if the stock of a product in the system > 3 units, but there have been no sales in the last 2 days despite high demand — the system assigns the task to a warehouse employee to conduct an inventory).
- **Out-of-Stock (OOS) logic:** automatic hiding of the product from the app storefront when the actual stock is zero, offering alternatives to the user.

### 5. Supply Chain Performance Metrics (Logistics KPIs)
- **OSA (On-Shelf Availability):** % of time when the product from the top matrix was available for purchase.
- **Write-off Rate:** the cost of written-off goods (expired, defective) to total turnover.
- **Inventory Turnover:** the average time a product stays in stock in days (target value for fresh categories < 2-3 days).
- **Forecast Accuracy (WAPE):** the accuracy of the demand forecast of the auto-ordering system.
```

## Rules

- Do not allow manual ordering of goods by warehouse/dark store managers by default. The human factor leads to overstocking of warehouses or the absence of goods. The process should be automatic (auto-ordering), with the possibility of manual adjustment only in case of force majeure.
- Require a description of the FEFO (First Expired, First Out) logic for picking. Picking according to the LIFO principle ('take what is on top/closest') leads to spoilage of goods at the back of the shelf.
- Be sure to take into account the logic of the virtual stock. In e-grocery, the difference between the database and what’s actually on the shelf leads to the picker canceling items in the customer’s order, reducing NPS.
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