---
name: cro-audit
description: Conduct a Conversion Rate Optimization (CRO) audit for a landing page or registration/onboarding scenario. The input is a description or URL page, the output is a structured audit using the Clarity/Relevance/Friction/Trust/Urgency framework and the top 5 improvements for the A/B test.
argument-hint: [description or text of landing page/audit screen]
allowed-tools: Read, Write
preset: e-commerce
lifecycle: any
business-model: any
domain: ecom-retail
stage: any
output-artifact: document
---

# Conversion optimization audit (CRO Audit)

Conduct a professional conversion audit (Conversion Rate Optimization) of the landing page, registration screen or onboarding funnel. Helps the product identify barriers that prevent users from taking the target action, analyze content based on key psychological factors, and create a priority list of changes for A/B testing.

## Process

1. **Define the landing page and key action.** (Product landing page, tariff page, card linking screen. Target action - leave a request, buy a subscription, register).
2. **Conduct an audit using the CRO framework:**
- *Clarity:* Is it clear from the first 3 seconds what the product offers and what the next step is (Call to Action - CTA)?
- *Relevance:* Does the content meet the user's expectations (after clicking on the ad)?
- *Friction:* How difficult is it to perform the target action (extra form fields, long loading times, difficult choices)?
- *Trust:* Does the page contain evidence of safety and reliability (certificates, bank logos, customer reviews, guarantees)?
- *Urgency:* Does the page encourage you to make a decision faster (limited promotions, seat limits, timers)?
3. **Make a plan of hypotheses for A/B tests (Top-5 Quick Wins).** What exactly to change in the interface, texts or logic to increase conversion.
4. **Save the output** in the current working directory as `cro-audit-[page-name].md`.

## Output Format

```
## CRO page conversion audit: [Page title]

### 1. Target Action and Current Conversion
- **Page description:** [for example, landing page of a B2B developer’s account]
- **Key Call to Action (CTA):** [“Register a company” button]
- **Current conversion rate (CR):** [for example, 2.4% from visitor to registration]

### 2. Detailed audit of the CRO framework
Analysis of barriers and triggers:
- **Clarity:**
- *Pros:* The company name and logo are clearly visible.
- *Cons:* The main title is blurry (“Innovations for the real estate market” instead of the specific “Automation of escrow account disclosure”). The CTA button is located below the first scroll screen.
- **Relevance:**
- *Analysis:* Traffic comes from advertising for the request “individual housing construction mortgage”, but the page only talks about MKD construction. The user does not find confirmation of his request.
- **Friction:**
- *Analysis:* The registration form contains 12 required fields (including OGRN, BIC of the bank and personal phone number of the general director). No input prompts.
- **Trust:**
- *Analysis:* There are no logos of partner banks, no information about licenses and data security. The “Reviews” section looks fake (text without real photos and company names).
- **Urgency:**
- *Analysis:* There is no incentive to make a decision now (the “First 3 trades are free when you connect before the end of the week” promotion is not displayed on the first screen).

### 3. Hypothesis plan for A/B testing (Top-5 Quick Wins)

| No. | Description of the change (What we are changing) | Expected effect (Due to what will increase the conversion) | Implementation difficulty (Low/Mid/High) | Priority (ICE Score) |
|---|----------------------------------|--------------------------------------------------|--------------------|-----------------------|
| 1 | Reduce the registration form from 12 to 3 required fields (TIN, Email, Phone). The rest should be filled out in the background using the TIN. | Reduced friction when entering data. | Lowe (Dadata integration) | Tall |
| 2 | Rewrite the main heading of the first screen under the pain of individual housing construction: “Open escrow accounts of individual housing construction automatically in 24 hours.” | Increased relevance and clarity. | Lowe | Tall |
| 3 | Raise the CTA button to the first screen and make it contrasting. | Increasing the visibility of the target action (Clarity). | Lowe | Tall |
| 4 | Add a trust block: “Bank-escrow agent of the first level” + license of the Central Bank of the Russian Federation. | Growing trust in the fintech segment. | Lowe | Medium |
| 5 | Add timer/banner: “Free 30-day trial if you register before [Date].” | Creating soft urgency. | Lowe | Medium |

### 4. Metrics to track in tests
- **Conversion Rate (CR):** % of visitors who successfully registered.
- **Bounce Rate:** % of users who leave the page in the first 15 seconds without interaction.
- **Form Drop-off Rate:** % of users who started filling out the registration form but abandoned it halfway through.
```

## Rules

- Challenge long data entry forms. Each extra field in the form reduces conversion by 5-10%. If the product asks to collect maximum data in the first step, demand that fields be reduced to an absolute minimum.
- The main title of the first screen (Hero Section) should contain a Value Proposition that is understandable without scrolling the page. No vague corporate philosophy.
- All hypotheses for A/B tests must be prioritized by framework (ICE/RICE).
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