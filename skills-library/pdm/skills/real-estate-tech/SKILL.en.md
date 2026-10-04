---
name: real-estate-tech
description: Design or analyze a product in the PropTech and mortgage ecosystem. The input is the concept of a product or integration, the output is structured requirements for seamless interaction between the developer, bank, buyer and partners.
argument-hint: 
allowed-tools: Read, Write
preset: fintech
lifecycle: any
business-model: any
domain: fintech
stage: any
output-artifact: document
---

# PropTech and Mortgage Ecosystem Specification



## Process


- *Borrower/Buyer:* wants to buy a home quickly, safely and with the lowest interest rate.


- *Partners (Real Estate Agencies, Brokers):* want to earn a commission and provide service to the client.
2. **Design an integration path (Partner Pipeline).** How does the developer transmit data about the client and apartment reservation to the bank? Describe the partner API and the developer’s personal account.
3. **Describe the logic of conducting a transaction and secure payments.** How the sequence works: mortgage approval → opening an escrow account → signing the shared-equity participation agreement (DDU) → releasing the escrow.
4. **Design a service for appraisal and insurance of collateral.** How to automate the assessment of the value of real estate and the issuance of mandatory insurance policies (life, property, title).
5. **Identify the key metrics of the ecosystem.** Time from selection to deal (Time-to-deal), developer conversion to bank issuance, share of electronic registrations, escrow account utilization.
6. **Save the output** in the current working directory as `proptech-spec-[product-name].md`.

## Output Format

```
## PropTech Product Specification: [Name]

### 1. Ecosystem Context and Stakeholders
- **Main business goal:** [what task the product solves, for example, reducing the time to complete a new building deal from 14 to 3 days]
- **Map of participants and their value:**
- *Developer:* [what they receive, for example, accelerated release of escrow accounts]
- *Buyer:* [for example, seamless document submission online without visiting the bank]
- *Bank:* [for example, reducing operational costs through API verification]

### 2. Partner Dashboard and API Integration (Developer to Bank)
- **Lead transfer flow:** [what booking and buyer data the developer sends from their CRM/ERP to the bank]
- **Developer's API:** [requirements for transmitting transaction statuses, property parameters, shared-equity construction contracts]
- **Broker/Developer Office:** requirements for the application submission interface (document verification, developer subsidy program calculator).

### 3. Calculation Mechanics and Transaction Security
- **Opening an escrow account:** [how the process of opening a depositor's account is automated when registering an equity participation agreement with the Rosreestr]
- **Electronic transaction registration (ETR):** integration with SMEV / Rosreestr, issuance of UKEP (enhanced qualified electronic signature) for the parties.
- **Safe Payment Service (SPS):** [the logic of freezing the down payment funds and transferring them to the developer after registration confirmation]

### 4. Collateral Appraisal and Insurance
- **Automated Valuation (AAV - Automated Valuation Model):** [how the market value of an apartment is assessed based on comparables, integration with appraisers' databases]
- **Insurance marketplace:** integration with insurance companies (accredited by the bank) for issuing personal and property insurance policies. The impact of insurance on the mortgage rate.

### 5. Ecosystem Performance Metrics
- **Time-to-Deal (TTD):** the average calendar time from booking an apartment to transferring money to escrow/the developer.
- **Conversion Rate (Partner Funnel):** % of applications submitted by the developer that reached mortgage approval.
- **Share of electronic registration:** % of transactions registered without visiting the MFC.
- **Integration SLA:** average time for status exchange between the developer's CRM and the bank's core.

### 6. Risks and Regulatory Restrictions
- **Developer risks:** developer default, construction delays (impact on escrow disclosure).
- **Compliance:** Federal Law 214-FZ (shared-equity construction), Federal Law 152-FZ (personal data when transferring to a partner), Central Bank requirements for reserving for escrow loans.
```

## Rules

- Do not let the B2B component (developers) be overlooked. The success of the mortgage ecosystem depends 80% on how convenient it is for the developer to sell apartments through this bank. Having a partner personal account and API integration is mandatory.
- Request a description of the escrow accounts mechanism and disclosure control. According to law 214-FZ, the bank is obliged to hold the buyer's money in escrow until the house is commissioned. The product manager must describe the triggers for account disclosure.
- Exclude schemes where the buyer has to take paper documents from the bank to the developer and back three times. The process should be designed as fully digital (paperless) based on electronic registration and a qualified electronic signature (QES).
- Write in English.

## Metrics (Fintech / Lending)

### Outcome metric
**risk-adjusted profit, approved good customers, portfolio margin.** The main result and value.

### Input metrics
**KYC pass rate, approval rate by risk bucket, time-to-decision, utilization.** Managed levers of outcome.

### Guardrails
**NPL 30/60/90, fraud loss, complaints, regulatory breaches, manual review overload.** What must not be worsened.

### Diagnostic metrics
**vintage analysis, PD/LGD, funnel by segment, false positives/negatives, channel quality.** Where to look for the cause.

### Instrumentation
**application_id, risk bucket, decision, KYC steps, repayment/vintage data, fraud flags.** What data is needed.

### Decision rules
- Ship / Iterate / Kill

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**