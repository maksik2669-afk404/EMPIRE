---
name: metrics-analyzer
description: Analyze product and financial data from CSV or pasted text. Finds trends, anomalies, segments, and takes into account fintech specifics (seasonality of disbursements, fraud spikes, credit cohorts).
argument-hint: [path to CSV or inserted data]
allowed-tools: Read, Write, Bash
preset: core
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# 

Turn raw data about user behavior or transactions into understandable insights. The skill supports standard data analysis (trends, segments, anomalies), as well as a specialized fintech/banking mode for working with the loan portfolio, fraud activity and seasonal fluctuations in demand.

## Process




- *Fraud Spikes:* look for abnormal peaks of transactions with a high percentage of chargebacks or refunds, a sharp increase in small transactions (a sign of brute force/carding) or atypical geo-transitions.

3. **Detect general trends and anomalies.** Calculate deviations more than 2 standard deviations from the mean.
4. **Formulate 3 actionable insights** with recommendations for business and product.
5. **Save the output** in the current working directory as `metrics-analysis-[date].md`.

## Output Format

```
## 
- **Data range:** [Start date] to [End date]
- **Analysis specifics:** [Standard / Fintech analysis]

### 1. Key Indicators and Trends


| [metric] | [X] | [Y] | [+/-Z%] | [Growing / Falling / Stable] |

### 

- **Fraud signals (for transactional data):** [are refund spikes, duplicate payments, card/IP anomalies detected].

### 3. Seasonal analysis and cohort shifts
- **Impact of seasonality:** [assessment of the influence of the time of year/holidays on metrics; for example, “The current 15% drop in issuances in January is consistent with historical holiday seasonality, there is no panic”].


### 
1. **[Insight title]:** [What the data shows] - [Why it matters] - [Suggested action for the product team]
2. **[Insight Title]:** [What the Data Shows] - [Why It Matters] - [Suggested Action]

```

## Rules


- Always separate the real deterioration of metrics from seasonal fluctuations. The decrease in transaction volume in the first half of January is normal seasonality in retail and banking, and not a sign of product failure.

- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?