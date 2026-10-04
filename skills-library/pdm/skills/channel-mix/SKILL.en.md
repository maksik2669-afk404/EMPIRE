---
name: channel-mix
description: Analyze and prioritize customer acquisition channels (Channel Mix) from the point of view of unit economics. The input is a description of the product and available channels, the output is a structured channel assessment matrix: CAC, scaling potential, saturation risks and launch plan (Now/Later/Never).
argument-hint: [description of product and hypotheses by attraction channels]
allowed-tools: Read, Write
preset: growth
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Analysis of attraction channels (Channel Mix)

Create a detailed analysis and prioritization of acquisition channels (Channel Mix) for the product. Helps the product assess the convergence of unit economics across different traffic sources, compare the cost of acquisition (CAC) with potential revenue (LTV), identify the risks of channel burnout and create a matrix of distribution priorities (Now/Later/Never).

## Process

1. **Define a set of potential channels.** (Performance advertising (Yandex.Direct, VK), SEO traffic, affiliate integrations (cross-promo), referral loops, direct B2B sales).
2. **Estimate CAC and LTV for each channel.** Which channel requires the most upfront costs? What is the Payback Period?
3. **Assess Scale Potential and Saturation.** What is the channel capacity? How quickly will the cost of acquisition increase when trying to double traffic (auction effect)?
4. **Design a channel matrix (Now/Later/Never).**
- *Now:* cheap, fast or most converting channels for the current stage.
- *Later:* channels with a long launch cycle (e.g. SEO, content marketing) that require scaling after PMF.
- *Never:* ineffective channels that break unit economics.
5. **Save the output** in the current working directory as `channel-mix-[product-name].md`.

## Output Format

```
## Analysis and prioritization of acquisition channels: [Product name]

### 1. Current Unit Economics and Constraints
- **LTV of product (target):** [X] rub.
- **Maximum allowable CAC (Max CAC):** [LTV / 3 = Y] rub.
- **Main limitation:** [for example, limited budget for paid advertising, high competition in the auction].

### 2. Comparative assessment of attraction channels
Channel analysis based on key criteria:

| Recruitment channel | Predictive CAC | Scaling potential | Launch speed / Time-to-ROI | Risk of saturation (burnout) | Priority |
|----|---|---|---|---|---|
| **1. Affiliate channel** (Banks/Developers) | [Low] | [High] | [Mid (need API integration)] | [Low] | **P0 (Now)** |
| **2. Contextual advertising** (Yandex.Direct) | [High] | [Medium] | [Fast (1-3 days)] | [High (auction overheated)] | **P1 (Now)** |
| **3. SEO Marketing** (Blog, Articles) | [Low (long)] | [High] | [Slow (3-6 months)] | [Low] | **P2 (Later)** |
| **4. Direct Sales** (Direct walk-through of small contractors) | [Critical high] | [Low] | [Slowly] | [High] | **Never** |

### 3. Channel prioritization matrix (Now / Later / Never)
- **Launch NOW:**
- *[Channel name and rationale]:* quick launch to receive the first paying cohorts (for example, context for hot keywords “mortgage individual housing construction developer”).
- *Affiliate cross-promotion:* offering a service to current clients of the escrow agent bank (free base).
- **Launch LATER:**
- *SEO and knowledge base:* creation of a content hub according to the laws of individual housing construction and escrow for organic traffic. Start preparing now, the effect will be in 6 months.
- **DO NOT START (Never):**
- *Paid advertising for a wide audience (B2C social networks):* too low concentration of target developers in the total mass of users, CTR will be extremely low, CAC will exceed LTV by 5 times.

### 4. Metrics for monitoring acquisition channels
- **CAC by Channel:** cost of customer acquisition, detailed for each source.
- **LTV / CAC by Channel:** convergence of unit economics of a specific channel (goal > 3).
- **CAC Payback Period:** speed of return on investment in attraction (target < 6-12 months).
- **Channel Share:** share of each channel in the total volume of new registrations/deals.
```

## Rules

- Prohibit launching acquisition channels without taking into account the LTV of the product. If LTV is 500 rubles, channels with manual processing of applications by sales managers (Direct Sales) are strictly prohibited.
- Be sure to consider the risk of saturation (burnout) of advertising channels. Contextual advertising in overheated auctions quickly becomes more expensive when trying to scale traffic.
- The Now/Later/Never prioritization matrix should contain clear logical arguments for each status.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?