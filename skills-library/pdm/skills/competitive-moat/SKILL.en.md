---
name: competitive-moat
description: Assess the security and competitive moat of the product (Competitive Moat). The input is a description of the product and competitors, the output is a structured audit: switching costs, network effects, data moats and recommendations for strengthening the moat.
argument-hint: [description of product and competitive environment]
allowed-tools: Read, Write
preset: strategy
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Product moat (competitive-moat)

Conduct an audit of the strategic protection of the product from copying by competitors (Competitive Moat / Protective Barriers). The skill helps the product analyze the strengths of the business according to the classic classification of moats (network effects, switching costs, cost advantages, intangible assets) and develop a roadmap for strengthening the protection of the product.

## Process

1. **Identify the Moat Types**
- *High Switching Costs:* How difficult is it for a customer to switch to a competitor? (for example, integrating a bank's API into a developer's CRM makes leaving extremely painful - you need to rewrite the code).
- *Network Effects:* Does the value of the product increase as the number of users increases? (for example, more buyers on the marketplace attract more sellers).
- *Data Moat:* unique data that the product accumulates and which improves the algorithms (for example, the history of credit transactions improves scoring, which cannot be copied by competitors).
- *Brand / Systemic advantages:* licenses from the Central Bank of the Russian Federation, exclusive partnerships.
2. **Rate the depth of the moat (Moat Rating).** Rating on a scale: No Moat, Narrow Moat, Wide Moat.
3. **Develop a strategy to strengthen protection.** What to include in the roadmap to increase loyalty and complicate customer migration (implementation of SSO, custom analytics, long-term contracts with a discount, proprietary algorithms).
4. **Save the output** in the current working directory as `competitive-moat-[product-name].md`.

## Output Format

```
## Strategic Security Audit: [Product Name]

### 1. Competitive Moat Map (Moat Matrix)
Analysis of business protective barriers:

| Ditch type | Current status in product | Barrier Strength (None/Narrow/Wide) | How this prevents competitors from copying us |
|---------|----------------------------|------------------------------------------|------------------------------------------|
| **Switching Costs** | Direct API integration of a bank’s personal account into developers’ ERP | **Wide Moat** | To change the partner bank, the developer needs to stop sales and rewrite the IT circuit for integrating estimates. |
| **Network Effects** | Two-sided partner base (banks <-> developers <-> appraisers) | **Narrow Moat** | Attracting new appraisers increases transaction speed, which attracts new developers. |
| **Data Moat** | Accumulated history of assessment of contractors' pledges and defaults for 5 years | **Wide Moat** | Our risk scoring model approves loans 20% more accurately, since new players do not have this data to train ML. |
| **System benefits** | Availability of licenses from the Central Bank of the Russian Federation, status of an official escrow agent | **Wide Moat** | Obtaining a license and status takes years and requires billions of capital. |

### 2. Moat Vulnerabilities
Where competitors can break through our defenses:
- *Technological vulnerability:* if a competitor offers free integration using their own developers, this will lower the switching barrier.
- *Price vulnerability:* dumping of escrow commissions by the largest banks.

### 3. Roadmap for strengthening the ditch (Strategic Recommendations)
1. **Increasing stickiness:** develop a module for auto-generating tax reporting for developers right inside our account. This will tie them even more closely to our system.
2. **Data exclusivity:** patent the computer vision algorithm for checking estimates and make it a closed API.
3. **Ecosystem bundling:** combine mortgage, insurance and collateral assessment into a single package with a discount that cannot be repeated by mono-services.
```

## Rules

- Challenge the illusion of security with a “unique interface” or “better design.” Any interface is copied by competitors within 2-4 weeks. The competitive moat must be built on system factors (data, network effects, integrations, licenses).
- The strategy for strengthening the moat should be tied to the product backlog (specific features/integrations), and not consist of general marketing phrases.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?