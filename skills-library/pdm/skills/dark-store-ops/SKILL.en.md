---
name: dark-store-ops
description: Develop a product strategy and optimize the operations of dark stores (e-grocery). The input is a description of the warehouse and delivery processes, the output is a specification for slot management, picking rules, delivery SLA and slot unit economics.
argument-hint: [description of darkstore or e-grocery project operations]
allowed-tools: Read, Write
preset: retail-ops
lifecycle: any
business-model: any
domain: ecom-retail
stage: any
output-artifact: document
---

# Darkstore operations (dark-store-ops)

Optimize grocery processes of a closed warehouse (dark store) and delivery in e-grocery / express retail. The skill helps the product set up dynamic management of delivery slots, optimize picking time using algorithms for laying out goods and routing pickers, control the SLA of delivery by couriers and calculate the unit economics of one order/slot.

## Process

1. **Design Slot Management.**
- *Interval delivery:* dividing the day into slots (for example, 10:00-12:00). How to close slots when the capacity of collectors/couriers is exceeded?
- *Express delivery:* delivery in 15-30 minutes. How to dynamically change the delivery zone (service radius of the dark store) depending on the weather, traffic jams or lack of couriers?
2. **Optimize the assembly process (Picking Optimization).**
- Algorithm for grouping goods by storage zones (dry zone, fresh, frozen, chemical).
- Routing of the assembler throughout the warehouse (minimizing steps, walking around the warehouse in a snake without returning).
- Metrics: Pick Time per Item (time to assemble one item in seconds, norm < 30 sec).
3. **Develop delivery SLA control.** Estimation of time for assembly, transfer to the courier, courier route. Logic for auto-assigning orders (batching - combining 2 orders for one courier).
4. **Describe the unit economics of the slot/order.** Income from check + delivery fee vs. cost of goods + payroll of the collector + payroll of the courier + write-off of damaged goods (fresh loss).
5. **Save the output** in the current working directory as `dark-store-[product-name].md`.

## Output Format

```
## Optimizing darkstore operations: [Project name]

### 1. Managing capacity and delivery zones (Dynamic Capacity)
- **Delivery model:** [Express in 15-30 min / Interval slots]
- **Load management algorithm (Surge Strategy):**
- If there is a shortage of couriers: automatic reduction of the radius of the delivery zone from 2 km to 1.2 km.
- When assembly load is high: increase the app's expected delivery time (ETA) by +15 minutes.

### 2. Algorithm and Assembly Metrics (Picking Engine)
- **Assembly logic:** Multiassembly (one assembler collects up to 3 orders at the same time, if they contain few items).
- **Warehouse traversal scheme (Routing):** Generation of the optimal picker path in the picker application based on product proximity (starting with heavy/large goods at the bottom of the shelves, ending with the Fresh and frozen zones).
- **Build Target Metrics:**
- *Pick Time per Item:* < 20 seconds.
- *Order assembly SLA:* < 8 minutes for an order of 15 items.
- *Proportion of assembly errors (Pick Accuracy):* > 99.8% (control through barcode scanning with a TSD scanner).

### 3. Courier delivery and Batching
- **Algorithm for combining orders (Batching):** gluing two orders to one courier if their geo-points are in the same direction (angle < 30 degrees from the darkstore) and total weight < 15 kg.
- **Delivery SLA:** < 20 minutes from the moment the order is transferred to the courier.

### 4. Unit economics of one order (Order Economics)
Average order profitability calculation:

| Economy element | Meaning | Share of the check | Description |
|----------|----------|--------------|----------|
| **Average Check (AOV)** | 1,800 rub. | 100% | Customer cart cost |
| **Cost (COGS)** | RUB 1,260 | 70% | Purchase of goods (Margin 30%) |
| **Picking Cost** | 60 rub. | 3.3% | Payroll of the assembler in 8 minutes of work |
| **Delivery Cost**| 180 rub. | 10% | Payment to the courier for delivery |
| **Write-offs / Fresh Loss** | 36 rub. | 2% | Spoiled food, vegetables/fruits |
| **Net Slot Margin (Order Contribution)** | **+264 rub.** | **+14.7%** | Profit before darkstore rental |
```

## Rules

- Prohibit pickers from collecting orders without scanning barcodes (TCD). Assembling “by eye” leads to mis-sorting (the client receives bananas instead of apples), an increase in returns and a drop in loyalty.
- Always include fresh category write-offs (Fresh Loss / Waste) in the darkstore unit economy. E-grocery does not exist without write-offs; keeping write-offs within 2-4% of revenue is an excellent product result.
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