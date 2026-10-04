---
name: credit-product-spec
description: Create a specification for a loan product (consumer loan, credit card, mortgage, installment plan/BNPL). The input is a product concept, the output is structured requirements describing the scoring funnel, limit utilization, CLV calculation and NPL protection.
argument-hint: [credit product concept or terms]
allowed-tools: Read, Write
preset: fintech
lifecycle: any
business-model: any
domain: fintech
stage: any
output-artifact: document
---

# Loan product specification

Create detailed requirements for the launch or development of a credit product. This skill helps the product take into account the key specifics of fintech: the decision-making funnel for the borrower, scoring restrictions, the life cycle of debt and the balance between profitability and risks.

## Process

1. **Understand the introductory information.** What type of loan (secured/unsecured, installment plan, card)? Who is the target audience? What are the key parameters (rate, limits, term)?
2. **Define the stages of the approval funnel.** From filling out the application to issuing funds. Highlight automatic failure points (hard checks) and scoring stages.
3. **Describe the logic of limits and recycling.** How the initial limit is calculated, how its use (recycling) is stimulated, and under what conditions the limit can be increased or blocked.
4. **Design risk protection (NPL/Delinquency).** How does the system prevent borrower default? What triggers trigger work with overdue debt (soft/hard collection).
5. **Calculate the unit economy of the borrower (CLV vs. NPL).** Describe the structure of income (interest, commissions, fines, insurance) and expenses (cost of funding, operating expenses, losses from defaults - Cost of Risk).
6. **Save the output** in the current working directory as `credit-spec-[product-name].md`.

## Output Format

```
## Loan product specification: [Name]

### 1. Product parameters and target audience
- **Product Type:** [for example, BNPL installment plan for the purchase of electronics / Cash loan]
- **Limits:** Min [X] rub. | Max [Y] rub.
- **Rate and Term:** [interest rate, interest-free period (grace), loan terms]
- **Target segment:** [what client profile we are targeting - age, income, employment]

### 2. Approval Funnel (Decision Engine)
- **Application steps:** [what data the client fills in, what data we pull from the BKI / State Services]
- **Hard Checks:** [instant rejection criteria: age < 18, current overdue, stateless]
- **Scoring model:** [what factors we evaluate: PDN credit load, payment discipline, behavioral scoring]
- **Decision time:** [target SLA for approval, e.g. auto-approval < 1 minute]

### 3. Limit Management
- **Logic of the first limit:** [how we determine the amount for a new client]
- **Triggers for limit changes:**
- *Increase:* [for example, 3 months of active use without delays, increase in transaction activity]
- *Downgrade/Blocking:* [the occurrence of arrears on other loans in BKI, inactivity > 6 months]
- **Scenarios for increasing utilization:** [how we motivate to spend the limit - cashback, affiliate discounts, reminders]

### 4. Risks and Collection (NPL & Collection)
- **Target level of risk (Cost of Risk):** [expected % of losses, for example, NPL 90+ < 3%]
- **Life cycle of overdue:**
- *Grace for overdue (1-3 days):* [reminders, no fines, technical overdraft]
- *Soft Collection (4-30 days):* [calls, SMS, push notifications, restructuring proposal]
- *Hard Collection (30+ days):* [transfer to a collection agency, preparation of a lawsuit]

### 5. Client economics (CLV Model)
- **Revenue Streams:** [interest, transfer fees, service fees, insurance products, interchange fee]
- **Cost Structure:**
- Cost of capital (funding)
- Cost of acquisition (CAC)
- Operating expenses (verification, BKI, SMS notification)
- Losses from non-returns (Provisioning / Cost of Risk)
- **Key balance:** [which should cover losses, making the product profitable]

### 6. Compliance & Regulation
- **Regulator requirements (Central Bank of the Russian Federation):** [PSC (full cost of the loan), limits on PDN (debt load indicator), reservation]
- **Consents:** [consent to personal processing. data, consent to a request to the BKI, consent to receive reports]
```

## Rules

- The product should not be designed in a vacuum. Require explicit indication of data sources for verification (BKI, SMEV/Gosuslugi, internal transactional data).
- The concepts of PDN (Debt Burden Indicator) and PSK (Full Cost of Loan) are mandatory for any loan product in the Russian Federation. Challenge specifications that ignore Central Bank regulatory restrictions.
- Turn on the recycling logic. An approved but unused limit costs the bank money (reserves). The PM must think about how to make the limit work.
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