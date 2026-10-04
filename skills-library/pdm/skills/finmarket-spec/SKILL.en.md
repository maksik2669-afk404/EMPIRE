---
name: finmarket-spec
description: Create a specification for a financial marketplace or aggregator (loans, deposits, insurance, investments). At the entrance is a Finnish concept. marketplace, the output is structured requirements for aggregation of offers, API integrations with banks, Central Bank compliance and monetization.
argument-hint: [concept of a financial marketplace or aggregator]
allowed-tools: Read, Write
preset: fintech
lifecycle: any
business-model: any
domain: fintech
stage: any
output-artifact: document
---

# Financial Marketplace Specification

Create detailed requirements for a financial marketplace or aggregator (analogs of Banki.ru, Sravni.ru, Financial Services). Skill helps the product design a platform that aggregates offers from dozens of banks, insurers and brokers, ensures seamless submission of applications and is monetized without compromising user trust.

## Process

1. **Determine the type of aggregated products.** (Deposits, consumer loans, mortgages, OSAGO/CASCO car insurance, microloans).
2. **Design an integration model with partners (bank APIs).** How does the marketplace receive current rates and transmit completed questionnaires? (Transfer of leads - Lead Gen, direct integration of API/SMEV, or redirecting the user to the bank’s website).
3. **Describe the balance between monetization and trust.** How does the monetization model work (pay-per-click CPC, fee-per-approved CPL, or commission-per-issue CPS)? How are offers ranked - fairly based on benefit to the client or with priority given to sponsored partners?
4. **Design a funnel and a user questionnaire.** How to minimize the number of fields to be filled in (for example, integration with State Services/USIA for auto-filling out a questionnaire).
5. **Describe compliance and legal architecture.** Consents to BKI, requirements of 152-FZ, requirements of the Bank of Russia for operators of financial platforms.
6. **Save the output** in the current working directory as `finmarket-spec-[product-name].md`.

## Output Format

```
## Financial Marketplace Specification: [Name]

### 1. Product strategy and aggregation model
- **Financial product category:** [for example, deposit aggregator with online opening]
- **Integration scheme with banks:**
- *White Label / Direct integration:* registration takes place inside the marketplace, the bank receives a ready-made transaction.
- *Lead Generation:* the marketplace collects contacts and transfers them to the bank’s CRM.
- *Referral:* the marketplace simply redirects to the bank’s website using a referral link.

### 2. Monetization and Ranking of offers
- **Monetization model:** [CPL (payment for a completed application form), CPS (percentage of the issued loan/open deposit), or advertising model]
- **Ranking algorithm (Fair Play):**
- How is the default output generated (based on the best rate, the probability of approval for a given client, or taking into account the affiliate commission).
- How advertising/sponsored offers are marked (advertising tagging).

### 3. User funnel and Autofill (USIA/Government services)
- **Comparison flow:** filters by parameters (amount, term, deposit requirements) -> comparison of product cards.
- **Seamless questionnaire:** integration with State Services (USIA) for instant confirmation of identity and auto-filling of passport data, registration address and income level (via the Pension Fund).
- **Multi-application:** sending one application form to 5-10 partner banks at once. How responses are aggregated and displayed (approved/rejected/conditions changed).

### 4. User Trust and Safety
- **Data reconciliation:** protection against substitution of conditions (how we guarantee that the rate on the marketplace matches the rate in the bank agreement).
- **Transaction security:** if the marketplace accepts money (for example, to open a deposit on Financial Services through SBP) - integration with the RFI (Financial Transaction Registrar).

### 5. Marketplace success metrics
- **Match Rate:** % of users who found at least one suitable offer and submitted an application.
- **Approval Rate:** % of approvals by partner banks for applications sent from the marketplace (lead quality for the bank).
- **Take Rate / Revenue per Lead:** average platform income from one submitted/approved application.
- **Drop-off on the profile:** in which field of the profile users most often leave.

### 6. Legal requirements and Regulation (Central Bank of the Russian Federation)
- **Licensing:** requirements of the Central Bank of the Russian Federation for the register of financial platform operators (Law No. 211-FZ).
- **Consent to BKI:** a mandatory step of signing consent via SMS/UKEP to check your credit history in several bureaus.
```

## Rules

- Challenge specifications where the user must fill in 30 fields manually. The financial marketplace is required to use integration with State Services (USIA/SMEV) for auto-filling.
- Monetization should not kill trust. The ranking algorithm must be transparent to the user. If sponsorship offers appear above, they should be clearly labeled.
- Consider the risk of changes in conditions by the bank. The marketplace must regularly update bid data (via bank APIs or scraping) to avoid accusations of false advertising.
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