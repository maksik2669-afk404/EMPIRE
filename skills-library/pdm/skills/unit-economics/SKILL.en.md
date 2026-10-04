---
name: unit-economics
description: Calculate the unit economics of a financial or credit product. Input — issuance and acquisition parameters, output — a digital model: calculation of LTV of a financial client (marginal income, funding, reserves, risk price), CAC, payback (Payback), and sensitivity analysis.
argument-hint: [parameters of a financial or credit product]
allowed-tools: Read, Write
preset: fintech
lifecycle: any
business-model: any
domain: fintech
stage: any
output-artifact: document
---

# Unit economics of financial products (unit-economics)

Build a detailed unit economics model for a financial, credit, or mortgage product. The skill helps a product manager calculate the lifetime value of a customer (LTV) taking into account interest income, cost of funding (CoF), reserves for potential loan losses (LLP), transaction costs, customer acquisition cost (CAC), and payback period.

## Process

1. **Identify the unit (unit of analysis).** (Usually this is one issued loan, one active card, or one acquired client).
2. **Assemble the revenue structure (Revenue Drivers).**
- *Interest Revenue:* interest on a loan.
- *Fee Revenue (Commission Income):* issuance fees, insurance, SMS notifications, acquiring.
3. **Collect the structure of expenses (Cost Drivers).**
- **Cost of Funds (CoF / Стоимость фондирования):** the cost of money for the bank (for example, the interest rate on deposits or the key rate of the Central Bank of the Russian Federation).
- **Expected Loss / LLP (Provision for Losses):** the cost of credit risk. Calculated as `PD (probability of default) × LGD (loss given default)`.
- *Operating Costs (Transaction costs):* Salaries of underwriters, credit bureau scoring requests, conducting calculations.
4. **Calculate the payback period.**
- **LTV:** total marginal income over the entire product lifecycle (taking early repayment into account).
- **CAC:** marketing and sales expenses divided by the number of products issued.
- **LTV / CAC:** the ratio should be > 3 for a stable business model.
5. **Save the output** in the current working directory as `unit-economics-[product-name].md`.

## Output Format

```
## Unit Economics of the Credit Product: [Product Name]
- **Basic unit:** One issued consumer loan (average amount [X] rubles, term [Y] months).

### 1. Revenue per Unit
- **Interest Revenue:** [X] rubles for the entire term (rate [Y%] per annum).
- **Commission income (Fees & Cross-sell):** [Z] rubles (including life insurance, processing fees).
- **Total income per unit (Lifetime Revenue):** [R] rubles.

### 2. Expenses per Unit (Cost of Goods Sold / COGS)
- **Cost of Funds (CoF):** [C1] rubles (based on the bank's deposit attraction rate of [W%] per annum).
- **Credit risk (Expected Loss / LLP):** [C2] rub. (based on historical probability of default PD = [A%] and loss given default LGD = [B%]).
- **Transactional costs (Operations Cost):** [C3] RUB (requests to credit bureaus, scoring, payroll verification, SBP commissions).
- **Total expenses for one unit (Lifetime COGS):** [Total Costs] RUB.

### 3. Marginality and Convergence of the Economy
- **Lifetime Value (LTV):** [Revenue - COGS] = [LTV] RUB.
- **Cost of Acquisition (CAC):** [CAC] RUB (marketing + agency commission to partners/realtors per lead).
- **Net profit per unit (Contribution Margin):** [LTV - CAC] = [Margin] RUB.
- **LTV / CAC Ratio:** [LTV / CAC] (Health assessment: Healthy / Risk).
- **Payback period (CAC Payback Period):** [N] months.

### 4. Sensitivity Analysis (Sensitivity Analysis)
How LTV will change with fluctuations in key factors:
- If the key rate rises by +2% (increase in funding cost CoF): LTV will drop by [X%].
- If the credit risk (PD) increases by +1%: LTV will fall by [Y%], the economy will only break even with a CAC growth of [Z%].
```

## Rules

- Do not allow calculating the unit economics of credit products without considering the cost of funding (CoF) and credit risk (LLP). Showing gross interest income without deducting the cost of raising funds and default reserves is a critical mistake that creates the illusion of profitability on a loss-making portfolio.
- Early repayment (prepayment rate) must be taken into account when calculating the loan-to-value (LTV) ratio. If clients repay loans faster than the contract term, the bank receives less interest income, which reduces the LTV.
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