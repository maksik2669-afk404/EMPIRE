---
name: product-teardown
description: Analyze the strategy, UX solutions, business model and growth loops of any product. Use it when you need to understand how a product works and why.
argument-hint: [product name or URL]
allowed-tools: Read, WebFetch, WebSearch, Write
preset: fintech
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Product Teardown



## Process

1. **Research the Product** - Use WebSearch and WebFetch to gather information about the product, its market, competitors and users.
2. **Analyze** - break down the product into its key components.
3. **Write an analysis** - structured, brief, with an expressed position (opinionated).
4. **Save the output** in the current working directory as `product-teardown-[context].md`.

## Output Format

### [Product Name] - Product Analysis

**Essence (One-liner):** What this product does, in one sentence.





**Business Model:** How the product makes money. Subscription levels/rates, if applicable.

**Key product solutions:**
- A list of 3-5 notable UX or product solutions and WHY they work (or don't).

**Growth engine:** How it attracts users (virality, content, sales, advertising, PLG). What works best.



**Weaknesses:** 2-3 real vulnerabilities. Not general phrases, but specific to this product.

**If I were a PM:** 1-2 things you would change or build next, with justification.

## Rules

- Be categorical and have a position (be opinionated). “It all depends on the context” is not an analysis.


- The volume of analysis is maximum 1-2 pages. Density is more important than length.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?