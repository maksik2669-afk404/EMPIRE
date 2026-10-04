---
name: vas-product
description: Design a product strategy for value-added services (VAS) in telecom.
argument-hint: [VAS service concept (security, music, content) for telecom]
allowed-tools: Read, Write
preset: telecom
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# VAS-products in telecom (vas-product)

Develop a product strategy and requirements for Value-Added Services (additional services of a telecom operator: anti-spam, cloud storage, music subscriptions, parental control).

## Process
1. **Design activation mechanics (Opt-in).** Protection against automatic subscriptions — a requirement for the user's explicit consent via SMS/Personal account according to Russian law.
2. **Determine the monetization structure.** Daily/monthly subscription fee, trial periods.
3. **Develop integration with billing.** Deduction of funds from the mobile phone account, logic of limits when the balance is zero.
4. **Save the output** in the current working directory as `vas-product-[context].md`.

## Output Format
```
## VAS Service Specification: [Service Name]
- **Activation mechanics:** double confirmation (Double Opt-in) on the landing page with SMS sending a confirmation code.
- **Monetization:** 7 days free (trial), then 5 RUB/day charged to the mobile account.
- **Integration with billing:** service suspension when the mobile account balance is negative.
```


## Rules

- Write in English.
## Metrics

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**