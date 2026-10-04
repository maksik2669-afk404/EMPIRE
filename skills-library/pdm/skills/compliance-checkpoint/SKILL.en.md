---
name: compliance-checkpoint
description: Check a feature or product for compliance with the regulatory requirements of the Russian Federation (fintech, banking, data processing). The input is a description of the feature, the output is a structured audit of compliance risks: 152-FZ (personal data), AML/CFT (115-FZ), requirements of the Central Bank of the Russian Federation and an information security checklist.
argument-hint: [description of the feature or process to be tested]
allowed-tools: Read, Write
preset: fintech
lifecycle: any
business-model: any
domain: fintech
stage: any
output-artifact: document
---

# Regulatory Compliance Checkpoint

Create a detailed compliance audit for a product feature or process in regulated areas (fintech, banking, government services, e-commerce). Helps the product identify legal and regulatory risks at the design stage in order to avoid fines from the Central Bank of the Russian Federation, Roskomnadzor blocking and information security problems.

## Process

1. **Understand the feature.** What data is collected? What are the financial flows? Who are the parties to the transaction?
2. **Check according to 152-FZ (Personal Data).** Is PD collection required? Where are they stored (localization of databases in the Russian Federation)? What are the conditions for obtaining consent (PDN, advertising mailings, transfer to third parties)?
3. **Check for AML/CFT (115-FZ - Anti-money laundering).** Is client identification required (simplified, complete)? Is the operation subject to fraud/legalization risk monitoring?
4. **Check the requirements of the Bank of Russia (Central Bank of the Russian Federation).** (Limits, reservations, PSC, information disclosure, payment rules).
5. **Assess information security (IS) risks.** Compliance with GOST R 57580, transaction protection, data encryption, requirements for electronic signatures (UKEP/UNEP).
6. **Save the output** in the current working directory as `compliance-audit-[feature-name].md`.

## Output Format

```
## Feature compliance audit: [Feature name]

### 1. Risk Scoreboard
- **Regulatory risk level:** [Critical / High / Medium / Low]
- **Critical blocker:** [description of the main risk, for example: transfer of passport data to a partner without explicit consent]
- **Regulators in the circuit:** [Central Bank of the Russian Federation, Roskomnadzor, Federal Tax Service, Ministry of Digital Development]

### 2. Personal data (152-FZ & Roskomnadzor)
- **Category of data collected:** [public, biometric, special, general personal data]
- **Consent to processing (Consent):**
- Requirements for consent checklists in the interface (the checkbox should not be pre-filled).
- Links to Privacy Policy and Terms of Use.
- **Database localization:** [confirmation of data storage on servers within the Russian Federation].
- **Transfer to third parties:** [is separate consent required for the transfer of data to partners/developers/insurers].

### 3. Identification and AML/CFT (115-FZ)
- **KYC (Know Your Customer) requirements:**
- Level of identification: [without identification (limits of anonymous wallets) / simplified (by passport/SNILS/State Services) / full (with personal presence/biometrics)].
- **Transaction monitoring:** triggers for suspending transactions (abnormal amounts, frequent transfers, signs of droppership).

### 4. Requirements of the Bank of Russia (CBRF)
- **Limits and reserves:** [limitations on transaction amounts, requirements for reserving funds for transactions].
- **PSC (Full cost of loan) and commissions:** [rules for disclosing the cost of services to the client in the interface, font and location of information].
- **Customer complaints:** compliance with SLA for responses to citizens’ requests (Federal Law-59 / Central Bank requirements).

### 5. Information security and Electronic signatures
- **Requirements for information security (GOST R 57580 / PCI-DSS):** encryption of data during transmission and storage, differentiation of developer access rights to combat bases.
- **Signing of documents:** what type of signature is required to complete a transaction/send an application (Simple electronic signature PEP (SMS code) / UNEP (in an application like Goskey) / UKEP on a token).

### 6. Recommendations for finalizing requirements (Action Items)
| Priority | Frontend/backend requirements | Legislative framework | Owner (PM/Lawyer/IS) |
|-----------|----------------------------------|---------------------|----------|
| P0 | Separate consent for personal data and marketing | 152-FZ | PM + Lawyer |
| P0 | Set up passport verification through SMEV | 115-FZ | PM + Developer |
| P1 | Add a UCS block to the first screen of the calculator | Central Bank requirements | PM + Designer |
```

## Rules

- Prohibit pre-ticked checkboxes for consent to the processing of personal data and sending advertisements. In the Russian Federation, this is a direct violation of the requirements of the FAS and Roskomnadzor.
- If the product is a credit or transactional product, identification of the borrower is required. Specifications that allow anonymous financial transactions without taking into account the requirements of 115-FZ should be blocked.
- All information about the full cost of services (PSC, hidden commissions, insurance) must be visible to the client BEFORE making a transaction.
- Write in English.

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