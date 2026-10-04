---
name: gtm-strategy
description: Develop a strategy for bringing the product to market (Go-to-Market / GTM). The input is a product or feature concept, the output is a structured GTM plan: defining an ideal customer (ICP), positioning and key messages across acquisition channels, launch stages and KPIs for the first 90 days.
argument-hint: [product concept or feature to be launched]
allowed-tools: Read, Write
preset: strategy
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Go-to-Market Strategy

Create a detailed strategy for bringing a new product or major feature to market (GTM). The skill helps the product structure the launch, synchronize the marketing, sales and product teams, determine the most effective distribution channels and set measurable goals for the first 90 days after the launch.

## Process

1. **Define your target audience (Ideal Customer Profile - ICP).** Who is the product being launched for? What problems does it solve (pain points)?
2. **Formulate a Value Proposition and Message.** What are the key differences of our solution? Prepare a matrix of messages for different customer segments and channels.
3. **Develop a channel mix (Distribution Channels).** Through what channels do we attract users? (Direct B2B sales, content marketing, paid advertising, referral program, PR/media).
4. **Design Launch Phases.**
- *Soft Launch:* testing on a narrow cohort of users to collect feedback and check stability.
- *Hard Launch:* mass marketing campaign, media publications, PR.
5. **Define success metrics for the first 90 days.** (Number of registrations/applications, conversion to first purchase, CAC, channel return on investment, first customer satisfaction CSAT/NPS).
6. **Save the output** in the current working directory as `gtm-strategy-[product-name].md`.

## Output Format

```
## Go-to-Market Strategy: [Product Name]

### 1. Target segment and Problems (ICP & Pain Points)
- **Ideal Client (ICP):** [description of company/user: field of activity, business size, technology stack for B2B; demographics and behavior for B2C]
- **Key pain points:** [what are the 2-3 main problems of the client that the product solves]
- **Alternatives in the market:** how clients are solving this problem now (competitors, manual Excel spreadsheets, workarounds).

### 2. Messaging Matrix
How we communicate with different segments:

| Audience Segment | Key pain | Unique message (Hook) | Reason to Believe |
|-------------------|---------------|--------------------------|--------------------|
| **Segment 1:** [e.g. Developers] | [Long return of money from escrow] | “Open escrow accounts automatically in 1 day” | Integration with USRN/Rosreestr via SMEV |
| **Segment 2:** [e.g. Buyers] | [Fear of unfinished home] | "Secure payments with a money back guarantee" | Bank-escrow agent with AAA rating |

### 3. Distribution & Marketing Channels
- **Priority channels:**
- *Channel 1 (for example, B2B Direct Sales):* direct sales through personal meetings and presentations to partners.
- *Channel 2 (for example, Content Marketing):* webinars and articles on specialized resources (Habr, VC.ru, specialized conferences) about automation of individual housing construction.
- *Channel 3 (for example, Product-Led Loops):* invitation by the developer to the buyer’s personal account (viral loop).

### 4. Launch plan by phases (Launch Roadmap)
- **Phase 1: Soft Launch (Pilot):** rollout to 5-10 loyal partners in one region. The goal is to identify API bugs and collect first feedback. Duration: 3 weeks.
- **Phase 2: Hard Launch (Scaling):** official release, distribution to the entire database of bank partners, publications in industry Telegram channels and the media.
- **Phase 3: Optimization (Day 30 - Day 90):** finalizing the funnel based on analytics results, scaling profitable traffic channels.

### 
- **Activation:** the number of developers who made at least one transaction through the account in the first 30 days.
- **CAC (Cost of Customer Acquisition):** cost of attracting one active channel partner.
- **Time-to-First-Value (TTFV):** average time from registration to the first successful transaction.
- **CSAT of first users:** assessment of satisfaction with your personal account.
```

## Rules

- Prohibit launching products using the “hard launch for everyone at once” model. Soft Launch is a must—without it, you risk burning your marketing budget for a product that has critical bugs in the onboarding funnel or crashes under load.
- Messaging should respond to specific pain points of the audience. General phrases like “our product is innovative, fast and convenient” should be excluded.
- The channel mix must take into account the economics of the product. If the LTV of a product is low (for example, a cheap B2C subscription), an expensive direct sales channel will kill the unit economics.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?