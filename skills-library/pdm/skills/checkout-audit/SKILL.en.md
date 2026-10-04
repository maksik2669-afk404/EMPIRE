---
name: checkout-audit
description: Analyze and optimize the ordering funnel (Checkout). The input is a description of the checkout or abandoned cart metrics, the output is a structured audit of the funnel: reasons for cart abandonment, payment friction, integration of payment methods and UX recommendations.
argument-hint: [description of checkout steps or funnel metrics]
allowed-tools: Read, Write
preset: e-commerce
lifecycle: any
business-model: any
domain: ecom-retail
stage: any
output-artifact: document
---

# Checkout Audit

Create a detailed analysis and plan for optimizing the checkout funnel. Helps the product increase payment conversion, reduce the percentage of cart abandonment, reduce friction when entering data and correctly integrate modern payment tools.

## Process

1. **Break out the checkout funnel into steps.** (Cart → Enter contacts → Select delivery → Select payment → Confirmation screen → Successful payment).
2. **Identify drop-off points and barriers.** Where are users leaving (e.g. unexpected shipping costs, required registration, complex address entry form)?
3. **Analyze payment methods (Payment Mix).** Are there enough payment methods? Are seamless methods integrated (SBP - Fast Payment System, SberPay, Tinkoff Pay, Yandex Pay, BNPL/installment plan in Shares)?
4. **Evaluate the friction when entering data (Data Entry Friction).** How many form fields does the user fill out? Are there any hints, automatic address substitution (FIAS/Dadata)?
5. **Formulate UX recommendations for optimization.** One-page checkout vs. Multi-step checkout, guest checkout without mandatory registration, display of the total amount at each step.
6. **Save the output** in the current working directory as `checkout-audit-[context].md`.

## Output Format

```
## Checkout funnel audit: [Product Name]

### 1. Funnel & Drop-offs map
- **Current funnel conversion:** [from cart to successful payment, %]
- **Analysis of funnel steps:**

| Funnel Step | Step Conversion | Share of people who left (Drop-off) | Key Reason for Step Dropout |
|------------|----------------|------------------------|----------------------------------|
| 1. Cart | [X%] | [Y%] | [for example, no information about shipping costs] |
| 2. Delivery | [X%] | [Y%] | [for example, a complex form for selecting a pickup point on the map] |
| 3. Payment | [X%] | [Y%] | [for example, an error when entering card details] |
| 4. 3D-Secure | [X%] | [Y%] | [for example, an SMS with a code from the bank did not arrive] |

### 2. Payment Friction & Mix Analysis
- **Set of payment methods:**
- *Seamless (SBP, SberPay, Tinkoff Pay):* [integrated/not, share in transactions]
- *Instalments / BNPL:* [is there payment in installments, what checks does it work on]
- *Payment by card (manual entry):* [is the input form convenient, is there auto-detection of the payment system]
- **Infrastructure payment errors:** share of acquiring errors (technical failures, bank timeouts, 3DS failures).

### 3. Assessing the complexity of forms (Form & Data Friction)
- **Number of input fields:** [total number of required and optional fields]
- **Autofill:** [is auto-substitution of full name, auto-determination of city by IP, address hints by FIAS/KLADR] used?
- **Registration:** [is registration required for purchase - the main barrier, or is there a one-click purchase/guest access]

### 4. Recommendations for UX/UI optimization (Quick Wins)
- **Guest checkout:** allow purchases without a password and email confirmation, create an account automatically in the background after payment.
- **Optimization of delivery:** Auto-calculation of cost and delivery time before selecting a specific pickup point/address.
- **Simplification of the form:** hide optional fields (for example, index, second phone number) under the spoiler.
- **Payment buttons on the first screen:** placing SBP and quick payment buttons directly on the shopping cart screen to skip data entry steps.

### 5. Checkout effectiveness metrics
- **Checkout Conversion Rate:** the ratio of paid orders to the number of checkout conversions.
- **Cart Abandonment Rate:** % of users who added an item to their cart but did not complete the purchase.
- **Payment Success Rate (PSR):** % of successful transactions from all payment attempts (acquiring quality).
- **Average Order Value (AOV):** the impact of introducing installments/BNPL on the average bill (usually +20-30%).
```

## Rules

- Prohibit requiring mandatory registration before purchase. This kills up to 20-30% of conversion. Require guest checkout to be implemented by default.
- Address hints are required. Manually entering zip code, state, and district on mobile devices is a critical UX flaw.
- Fast payment methods (SBP, SberPay, Tinkoff Pay) should be brought to the top. Manually entering the 16 digits of a card on your phone is an outdated pattern that reduces conversions.
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