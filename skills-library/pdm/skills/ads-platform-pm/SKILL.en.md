---
name: ads-platform-pm
description: Design or analyze a product in the field of advertising technologies (AdTech / Advertising account). The input is the concept of an advertising account or auction, the output is a structured specification: auction mechanics (GSP/VCG), purchasing models (CPM/CPC/CPA), targeting and conversion attribution logic.
argument-hint: [concept of an advertising platform or advertising account]
allowed-tools: Read, Write
preset: media-adtech
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Advertising Platform Specification (AdTech PM)

Create a detailed specification of requirements for an advertising platform or advertising account (for marketplace sellers, B2B clients or external monetization). Helps the product to design advertising auction rules, traffic purchasing models, an interface for setting up advertising campaigns, and a performance analytics system (conversion attribution).

## Process

1. **Define the target advertiser and placement.** Who buys the advertising (internal marketplace sellers, external brands)? Where are advertisements shown (banners on the main page, boosting cards in search results, contextual blocks)?
2. **Select a purchasing model (Pricing Models).** (CPM - payment for impressions, CPC - payment for clicks, CPA/CPS - payment for actions/sales).
3. **Describe Auction Mechanics.** How is the auction winner and write-off price determined? (GSP is a generalized second price auction, when the winner pays the next bidder’s bid + 1 kopeck, or VCG auction. The minimum bid is Floor Price).
4. **Design targeting.** (Search phrases, catalog categories, geotargeting, behavioral segments based on purchase history).
5. **Describe the Attribution model.** How do we link an ad click to a subsequent purchase? (Last Click, First Click, linear model, attribution window - for example, 7 days or 14 days).
6. **Save the output** in the current working directory as `ads-spec-[product-name].md`.

## Output Format

```
## Advertising Platform Specification: [Name]

### 1. Advertising formats and placement
- **Advertising formats:** [for example, boosting product cards in search / sponsored banners in the catalog]
- **Where we show:** [specific screens and positions, for example, a product card on the 3rd line of issue]
- **Buying model:** [CPC (cost per click) / CPM (cost per 1000 impressions) / CPA (cost per sale)]

### 2. Auction logic (Ad Auction & Bidding)
- **Auction type:** GSP (Generalized Second Price) - payment at the competitor’s bid behind + 1 kopeck. /VCG (Vickrey-Clarke-Groves).
- **Auction ranking formula:** [for example, Rank = CPC Bid × Predicted CTR of the card]. Advertising should not only be expensive, but also clickable.
- **Minimum bid (Floor Price):** basic threshold for entering the auction for different categories (for example, from 1.5 rubles per click).

### 3. Targeting and setting up audiences
- **Targeting types:**
- *Contextual:* display by key search phrases (search queries).
- *Category:* display in specific branches of the product catalog.
- *Behavioural (Audience Segments):* targeting cohorts (for example, “purchased children's products in the last 30 days”).

### 4. Analytics for the advertiser and Attribution
- **Default attribution model:** Last Touch / Last Click (the sale is credited to the last ad clicked on by the user).
- **Attribution Window:** the period of time after a click/impression during which the purchase is considered a result of the advertisement (for example, 14 days).
- **Post-View conversions:** do we take into account users who simply saw the banner, did not click, but bought the product later (impression -> purchase).

### 5. Platform performance metrics
- **Ad CTR (Click-Through Rate):** click-through rate of ad units (target value for search > 2-3%).
- **Bid Win Rate:** % of auctions won from the total number of advertiser bids.
- **eCPM (Effective Cost per Mille):** platform income per 1000 impressions of an advertising space (the main metric for the effectiveness of site monetization).
- **ROAS (Return on Ad Spend):** return on investment in advertising for the advertiser (ROAS = Revenue from Advertising / Advertising Costs).

### 6. Protection from fraud (Anti-Fraud & Brand Safety)
- **Click Fraud Filtering:** algorithms for cutting off clicks by competitors (excluding repeated quick clicks from the same IP/device).
- **Brand Safety:** exclusion of displaying brand advertisements on pages with negative context or next to products in the 18+ category.
```

## Rules

- The auction formula should not take into account only the bid. If you rank only by bid, irrelevant products with poor CTR will appear in the top results, and the site will lose income (users will stop clicking). The formula `Bid × CTR` is required for the CPC model.
- Require a clear definition of the attribution window. Without an attribution window, an advertiser can accuse the platform of taking credit for “organic” sales made a month after the click.
- Include anti-click protection (click fraud) in the requirements for the platform backend.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?