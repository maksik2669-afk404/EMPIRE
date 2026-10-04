---
name: search-ranking
description: Design or analyze search and ranking algorithms (for marketplaces, classifieds, catalogs). The input is a description of a search scenario or relevance problem, the output is a structured specification of ranking factors, the balance of relevance and commercial benefit, and a solution to the cold start problem.
argument-hint: [description of the search scenario or issue with results]
allowed-tools: Read, Write
preset: marketplace
lifecycle: any
business-model: any
domain: marketplace
stage: any
output-artifact: document
---

# Search and Ranking

Create a detailed specification of requirements for search results and ranking algorithms for catalogs, marketplaces, or classifieds (like WB, Ozon, Avito, CIAN). Helps the product manager design a balanced search logic that takes into account text relevance, the platform's commercial interests, and behavioral metrics.

## Process

1. **Define the stages of search operation.** Query parsing (synonyms, typo correction) → Candidate extraction (filtering) → Ranking (sorting candidates).
2. **Identify groups of ranking factors.**
- *Textual relevance:* matching the title, description, characteristics.
- *Behavioral factors:* CTR of the card in the search results, conversion to cart/purchase, bounce rate.
- *Commercial/Business factors:* product margin, delivery cost, paid boosting (advertising), seller rating.
3. **Resolve the conflict of interest (Relevance vs. Revenue).** How to balance the output so that the user finds exactly what they are looking for (relevance), but the platform earns money (priority for products with high commission or paid advertising).
4. **Solve the 'Cold Start' problem.** How new products/cards get their first impressions and views so that the algorithm can evaluate their conversion (boosting new items).
5. **Define search quality metrics.** NDCG (Normalized Discounted Cumulative Gain), CTR of the results, share of empty search results (Zero Results Rate), conversion from search to purchase.
6. **Save the output** in the current working directory as `search-spec-[context].md`.

## Output Format

```
## Search and Ranking Specification: [Product Name]

### 1. Search Architecture and Query Processing
- **Type of catalog:** [for example, goods marketplace / real estate rental]
- **Text input processing (NLP/Search Engine):**
- Recognition of typos and autocorrection.
- Support for synonyms (for example, 'mobile phone' = 'smartphone').
- Autocomplete (Search Autocomplete) with suggestions of popular categories.

### 2. Ranking Formula (Ranking Factors)
Factors determining the position of the card in the results:

| Factor Group | Specific Parameters | Weight in Formula (High/Medium/Low) | Justification |
|-----------------|----------------------|---------------------------------------|-------------|
| **1. Textual** | Match in title, tags, description | [High] | Basic hygiene factor of relevance |
| **2. Behavioral** | Card CTR, conversion to cart, purchase completion | [High] | The algorithm should promote what is actually being bought |
| **3. Commercial** | Commission size (take rate), delivery speed | [Average] | It is beneficial for the Bank/Platform to deliver faster and earn more |
| **4. Advertising** | Paid promotion by the seller | [Medium] | Sponsored cards rise to fixed positions |

### 3. Balancing Output (Relevance vs. Monetization)
- **Advertising boosting rules:** on which positions sponsored products are displayed (for example, 1st, 5th, 9th positions in the search results).
- **Pessimization (Downranking):** why cards are lowered in search results (low seller rating, high return rate of goods, long delivery, out-of-stock items).

### 4. Solving the 'Cold Start' Problem (Cold Start Strategy)
- **Boosting new items:** new cards without sales statistics automatically receive a temporary boost (for example, +10% to the score for the first 500 impressions).
- **Collection of behavioral signals:** as soon as the card accumulates test impressions, boosting is turned off, and its position is determined by the real conversion.

### 5. Search Quality Metrics (Search KPIs)
- **Zero Results Rate:** % of search queries that returned 0 results (target < 1-2%).
- **NDCG (Normalized Discounted Cumulative Gain):** a measure of search result relevance (how much the best results are at the very top).
- **Search Conversion (Search Conversion):** the conversion from a click on a search result to a target action (purchase/application).
- **Share of clicks to the second page:** a high figure indicates that the first search results page is irrelevant.
```

## Rules

- Do not prohibit strict ranking only by date added or only by price unless this is selected by the user in the filters. The default output (smart sorting) should be based on a combination of relevance and conversion factors.
- The Zero Results Rate metric is mandatory. Empty results are a dead end for the user. The specification should describe fallback scenarios (search by similar words, category recommendations).
- Do not allow advertising cards to dominate the top of the search results. If the first 10 products are only ads and irrelevant to the query, the user will leave the platform.
- Write in English.

## Metrics (Marketplace / Classifieds)

### Outcome metric
**successful transactions/matches, GMV with healthy take rate, liquidity.** The main result and value.

### Input metrics
**supply coverage, demand coverage, search success, time-to-first-match, reply rate.** Managed levers of outcome.

### Guardrails
**seller margin, dispute rate, cancellation rate, fraud rate, leakage/disintermediation.** What cannot be worsened.

### Diagnostic metrics
**liquidity by geo/category/price/time, supply quality, buyer conversion, seller activation.** Where to look for the cause.

### Instrumentation
**buyer_id, seller_id, listing_id, category, geo, search_id, contact/match/transaction events.** What data is needed.

### Decision rules
- Ship / Iterate / Kill

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**