---
name: fintech-product-teardown
description: Conduct an in-depth analysis of the FinTech Product Teardown, taking into account the regulatory framework and monetization.
argument-hint: [name of fintech product or service for analysis]
allowed-tools: Read, Write
preset: fintech
lifecycle: any
business-model: any
domain: fintech
stage: any
output-artifact: document
---

# Analysis of a fintech product (fintech-product-teardown)

Conduct a detailed analysis of the fintech solution, analyzing its regulatory framework (Central Bank of the Russian Federation, licensing), money flow architecture and risk model.

## Process
1. **Analysis of money flow (Money Flow).** Where the funds come from, where they are stored (nominal accounts, escrow), how commissions are written off.
2. **Regulatory compliance.** Licenses (Central Bank, NPO, bank), compliance with 115-FZ (AML/CFT).
3. **Risk model.** Credit risk, operational risk, fraud.
4. **Save the output** in the current working directory as `fintech-product-teardown-[context].md`.

## Output Format
```
## Fintech product analysis: [Name]
- **License type:** [Banking/NPO/Agent]
- **Money flow architecture:** [nominal accounts, acquiring gateways]
- **Compliance with 115-FZ:** automatic scoring of transactions for suspiciousness.
```

## Metrics (Fintech/Lending)

### Outcome metric
**risk-adjusted profit, approved good customers, portfolio margin.** Main result and value.

### Input metrics
**KYC pass rate, approval rate by risk bucket, time-to-decision, utilization.** Managed outcome levers.

### Guardrails
**NPL 30/60/90, fraud loss, complaints, regulatory breaches, manual review overload.** What cannot be worsened.

### Diagnostic metrics
**vintage analysis, PD/LGD, funnel by segment, false positives/negatives, channel quality.** Where to look for the reason.

### Instrumentation
**application_id, risk bucket, decision, KYC steps, repayment/vintage data, fraud flags.** What data is needed.

### Decision rules
- Ship/Iterate/Kill

### Universal Metric Rule
If you are proposing a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How ​​often do we watch it?**
3. **What events count it?**
4. **What is the decision threshold?**
5. **How ​​can it be spoiled or screwed up?**

## Rules

- Write in English.
