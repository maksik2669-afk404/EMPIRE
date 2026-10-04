---
name: market-sizing
description: 
argument-hint: 
allowed-tools: Read, WebFetch, WebSearch, Write
preset: discovery
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Market Size Estimation

Create a rigorous TAM/SAM/SOM assessment that the PM can use in a pitch deck, strategy document, or investment memorandum. The goal is defensible numbers with transparent assumptions, not bloated vanity metrics.

## Process


2. **Find the Data** - Use WebSearch to find industry reports, public reporting, analyst estimates, census data and any reliable sources. Prioritize recent data (last 2 years). Please cite each source.
3. **Calculate TAM (Total Addressable Market)** - Use a top-down (industry report size) and bottom-up (number of leads x average revenue per customer) approach if possible. If both methods give different numbers, show them both and explain the difference.


6. **Check Assumptions** - Provide a range (conservative/baseline/optimistic) for at least the SOM.
7. **Save the output** in the current working directory as `market-sizing-[context].md`.

## Output Format

### Market Definition
One paragraph: what market, who is buying, what problem, geographical coverage.

### TAM (Total Addressable Market)

**Top to bottom:** $X based on [source]. Calculation: [show math].
**Bottom to top:** $X based on [number of clients] × [ARPU]. Calculation: [show math].


### SAM (Served Addressable Market)

**Filters applied:**


- Other: [filter]



### 


|----------|-----|-----------|






### Key Assumptions

| # | Assumption | Impact if incorrect | Confidence |
|---|-----------|---------------------|------------|



### Sources


### Confidence level


## Rules



- Bottom-up estimates are generally more reliable than top-down estimates for niche markets. Talk about it when it's relevant.

- Round numbers accordingly. Don’t write “RUB 4,237,891” - write “RUB 4.2 million.” False precision undermines trust.



- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?