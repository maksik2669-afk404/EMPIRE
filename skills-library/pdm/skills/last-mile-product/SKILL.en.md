---
name: last-mile-product
description: Design or analyze a last-mile delivery product or pick-up point network. The input is a delivery concept or operational problem, the output is a structured specification: couriers routing, SLA management, pickup room and parcel tracking UX.
argument-hint: 
allowed-tools: Read, Write
preset: retail-ops
lifecycle: any
business-model: any
domain: ecom-retail
stage: any
output-artifact: document
---

# Last-Mile Delivery and Pick-up Point (Last-Mile)

Create a detailed specification of requirements for a last-mile logistics product (courier delivery, pickup point management, logistics aggregators such as SDEK, Yandex Delivery). Helps the product to increase the accuracy of delivery in time slots (SLAs), optimize the utilization of couriers, reduce the cost of one delivery (Cost per Delivery) and design convenient B2B interfaces for couriers and pick-up point employees.

## Process

1. **Define the delivery model.** (Interval delivery to slots, express delivery in 15-30 minutes, or pick-up from pick-up points/post offices).

3. **Describe the requirements for the courier application (Courier App).** Building a route (navigator), order statuses (accepted, arrived, handed over), delivery confirmation logic (code from SMS, door/passport photo, payment upon receipt).

5. **Describe the UX of tracking for the customer (Customer Tracking UX).** Displaying the courier on the map in real time, dynamic calculation of estimated time of arrival (ETA), communication with the courier without revealing phone numbers (masking).


## Output Format

```
## Last-Mile Product Specification: [Name]

### 1. Operating Model and Business Goals
- **Delivery format:** [for example, delivery from darkstore to door by courier on an electric bike, SLA < 20 minutes]



### 2. Dispatching algorithm and Routing (Courier Routing)



### 3. Courier App Capabilities
- **Route screen:** integration with maps/navigator, display of points A (fence) and B (delivery) with comments (“entrance from the yard”, “intercom code”).
- **Status model:** status transition [Assigned -> In warehouse -> On the way -> On site -> Delivered / Canceled].
- **Order closing flow:** confirmation of delivery (scanning the barcode of the package, entering an OTP code from the client, or photographing contactless delivery).

### 4. PVZ employee’s office (PVZ Portal)
- **Acceptance of shipments:** mass scanning of parcels when unloading the courier vehicle, recording damage/shortages.

- **Issue by QR/Barcode:** the client shows the barcode from the application -> the employee scans it -> the system highlights the numbers of the cells with the client’s parcels.
- **Partial redemption and Returns:** flow of trying on clothes, refusing some items, recalculating the receipt and sending the return to the warehouse.

### 
- **Live Tracking:** displaying the courier’s location on the map when the order becomes “On the way” status.
- **Dynamic ETA:** updating delivery time depending on traffic jams and the courier’s movement along the route.


### 




```

## Rules




- Write in English.

## Metrics (E-commerce / Retail)

### 
**contribution margin per order, repeat purchase, paid orders.** Main result and value.

### Input metrics
**checkout conversion, add-to-cart, availability, delivery promise accuracy, promo conversion.** Managed outcome levers.

### 
**gross margin after returns, refund rate, return abuse, stockout, payment failure.** What cannot be worsened.

### Diagnostic metrics
**funnel drop-off, category, device, payment method, delivery slot, promo dependency.** Where to look for the reason.

### 
**cart_id, order_id, SKU, inventory, payment events, return/refund reason.** What data is needed.

### 


### Universal Metric Rule
If you are proposing a metric, answer 5 questions:

2. **How ​​often do we watch it?**

4. **What is the decision threshold?**