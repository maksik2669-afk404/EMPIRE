---
name: dsp-ssp-spec
description: Develop specifications for a programmatic advertising platform (DSP/SSP).
argument-hint: [concept of DSP or SSP advertising product]
allowed-tools: Read, Write
preset: media-adtech
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Programmatic platforms (dsp-ssp-spec)

Design requirements for programmatic advertising products: Demand-Side Platform (DSP - advertising purchase) or Supply-Side Platform (SSP - sale of advertising space by publishers).

## Process
1. **Define key metrics.** Fill Rate (share of purchased inventory), CPM/CPC, Win Rate in the RTB (Real-Time Bidding) auction.
2. **Design the auction logic.** Setting the Bid Floor (minimum cost per thousand impressions), logic of the first/second type of auction.
3. **Save the output** in the current working directory as `dsp-ssp-spec-[context].md`.

## Output Format
```
## Programmatic module specification: [DSP/SSP]
- **Target metric (for SSP):** maximizing Fill Rate (target > 92%) while maintaining the Bid Floor at 80 rubles.
- **RTB auction algorithm:** selection of the winner using the Second Price Auction model.
```


## Rules

- Write in English.
## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?