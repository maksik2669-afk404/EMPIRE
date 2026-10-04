---
name: competitor-scan
description: Quickly analyze the competitive landscape for any product or market. The input is a description of the product/market, the output is a competitive map with positioning, gaps and opportunities.
argument-hint: [description of market or product]
allowed-tools: Read, WebFetch, WebSearch, Write
preset: discovery
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Competitor analysis

Conduct a quick analysis of the competitive landscape. The goal is to give the PM a clear picture of who is playing in this space, how they are positioned, and where the opportunities are.

## Process

1. **Parse the input** - Extract the key market/product for analysis. Define the category, target customer and key value proposition.
2. **Research competitors** - Use WebSearch to find direct competitors (same category, same client) and indirect (different approach, same task). The goal is 5-8 competitors. Check product pages, pricing, and recent content via WebFetch as needed.
3. **Analyze the positioning** - For each competitor, determine who they are targeting, what they are offering, how they value it, and what users are complaining about.
4. **Map the landscape** - Identify the two most differentiating axes of this market (for example, self-serve vs. enterprise, horizontal vs. vertical). Describe the position of each player.
5. **Find Gaps** - Look for underserved segments, missing features that are regularly mentioned in reviews, or price niches that no one is covering.
6. **Synthesize** - Write a short competitive brief.
7. **Save the output** in the current working directory as `competitor-scan-[context].md`.

## Output Format

### Market overview
One paragraph: what the market is, estimated maturity (emerging/growing/mature/declining) and dominant business model.

### Competitor table

| Competitor | Positioning | Target Client | Strengths | Weaknesses | Pricing Model |
|-----------|--------------|---------------|--------------|---------------|----------------------|
| ... | ... | ... | ... | ... | ... |

### Positioning map
Describe the chosen two axes and the position of each competitor. Use text 2x2 if it improves clarity.

### Opportunities in white space
A bulleted list of 3-5 gaps or underserved areas with a one-line explanation of each.

### Key Takeaway
One paragraph: the single most important insight a PM must take away.

## Rules

- Prioritize direct competitors over indirect ones. In cases of doubt, include, but mark as indirect.
- Always check the pricing pages - “Contact us” - valid data, mark as enterprise/opaque pricing.
- Don't make up data. If you can’t find reliable information about a competitor, say so explicitly.
- The entire output should take no more than 2 pages. Density is more important than length.
- Be opinionated: rank your competitors by threat level, say who wins and why.
- If there are less than 3 competitors in the market, mark this as a blue ocean and shift the focus to adjacent markets and substitutes.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?