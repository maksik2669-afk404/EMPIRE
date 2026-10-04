---
name: classifieds-model
description: Design or analyze a Classifieds and service product. The input is the concept of a classifieds product, the output is a structured specification: monetization of listings (freemium, premium), lead collection logic (leadgen), assessment of ad quality and response metrics.
argument-hint: [classifieds product or bulletin board concept]
allowed-tools: Read, Write
preset: marketplace
lifecycle: any
business-model: any
domain: marketplace
stage: any
output-artifact: document
---

# Classifieds Model Business Model

Create a detailed specification of requirements for a product in the field of bulletin boards (Classifieds) and marketplace services (analogues of Avito, CIAN, Profi.ru, Yandex Services). The skill helps the product design an ad placement funnel, choose a monetization model (paid placements, commissions per transaction, payment for contacts), evaluate the quality of content and set up liquidity metrics.

## Process

1. **Define the vertical of the classification.** (Real estate, cars, work, goods, services). What are the specifics of the deal (high check/low frequency vs. low check/high frequency)?
2. **Design a listing monetization model.**
- *Freemium limit:* how many ads a user can place for free per month in a given category.
- *Paid services (VAS - Value Added Services):* boosting (raising to the top, increasing views by X times), highlighting, VIP placement.
- *Pay-per-Lead / Pay-per-Contact:* payment for viewing a phone number or starting a chat (Profi.ru / Avito Services model).
3. **Develop criteria for listing quality (Listing Quality Score).** How the algorithm evaluates the completeness of the description, the quality of photos, the adequacy of the price and the seller’s rating to make a decision on moderation.
4. **Design protection against duplicates and fraud.** How to identify repeated advertisements (spam), fake objects (for example, non-existent “lantern” apartments in real estate), fraudulent schemes with prepayment.
5. **Define classification liquidity metrics.** Reply Rate (share of ads with responses), Time-to-Reply (seller response rate), conversion from view to contact (View-to-Contact).
6. **Save the output** in the current working directory as `classifieds-spec-[product-name].md`.

## Output Format

```
## Classifieds Product Specification: [Name]

### 1. Vertical and Target Audience
- **Specialization:** [for example, commercial real estate rental classification]
- **Participant Profile:**
- *Supply:* [individuals / professional realtors / agencies]
- *Seekers (Demand):* [business, entrepreneurs]
- **Trade Difficulty:** [low frequency trade with long decision cycle]

### 2. Monetization model and Tariffing
- **Free posting limits:** [for example, 1 free ad in the “Offices” category once every 90 days, then a paid listing].
- **Package subscriptions (for B2B):** rates for agencies (for example, a package for 50 active ads per month + personal page).
- **Value-Added Services (VAS packages):**
- Boosting: increase in coverage by 2/5/10 times for 1 or 7 days (the algorithm dynamically calculates the price of promotion depending on the competition in the category and geo).
- Premium design: enlarged card in the feed, highlighted title.

### 3. Content quality and moderation (Quality Score)
- **Ad Quality Score:**
- Evaluation factors: number of photos (at least 5), completion of key fields (area, floor, price), uniqueness of the description text.
- Impact on search results: ads with a high Quality Score are shown higher, all other things being equal.
- **Moderation rules:** automatic checking of photos for duplicates, checking the price for compliance with the market interval (protection from fakes).

### 4. Liquidity and Responses (Liquidity Loop)
- **Reply Rate:** % of ads for which the buyer completed the target action (clicked “Show phone” / wrote in chat) within 48 hours after publication.
- **Time-to-Reply (TTR):** the median time for a seller to respond to a buyer’s message in the platform chat.
- **Scenarios for increasing liquidity:** [automatic prompts to the seller to reduce the price if there are no calls on the ad for > 7 days].

### 5. Transaction security and protection from fraud (Trust & Safety)
- **Number protection (Masking):** substitution of a real phone number with a temporary platform number to protect against spammers and parsers.
- **Verification of the seller:** “Documents verified” icons (using passport/company details via State Services/T-ID/Sber ID).
- **Safe transaction:** holding the buyer’s funds on the platform until confirmation of receipt of the goods (for product verticals).

### 6. Key metrics of the classifieds platform
- **View-to-Contact Conversion:** conversion from viewing an ad to clicking the “Show phone” or “Write” button.
- **ARPU by sellers:** average income per user submitting an ad due to paid services and listings.
- **Liquidity Rate:** the share of active ads for which a transaction was made (or a response was received) before the publication deadline.
```

## Rules

- Prohibit classified files without protection against spam and duplicates. Parsing other people's databases and massively re-uploading ads will instantly turn the platform into a dump of irrelevant content.
- Require the development of author verification mechanisms (KYC). Verified profile badges through State Services/ID banks are the main factor of buyer confidence on classified sites today.
- Monetization of lead generation (Pay-per-Lead) must contain rules for compensating for fake leads. If a realtor/executor pays for a contact, and the user does not respond or is a bot, the platform should automatically return the money for the lead (flow arbitrage).
- Write in English.

## Metrics (Marketplace / Classifieds)

### Outcome metric
**successful transactions/matches, GMV with healthy take rate, liquidity.** Main result and value.

### Input metrics
**supply coverage, demand coverage, search success, time-to-first-match, reply rate.** Controlled outcome levers.

### Guardrails
**seller margin, dispute rate, cancellation rate, fraud rate, leakage/disintermediation.** What cannot be worsened.

### Diagnostic metrics
**liquidity by geo/category/price/time, supply quality, buyer conversion, seller activation.** Where to look for the reason.

### Instrumentation
**buyer_id, seller_id, listing_id, category, geo, search_id, contact/match/transaction events.** What data is needed.

### Decision rules
- Ship/Iterate/Kill

### Universal Metric Rule
If you are proposing a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How ​​often do we watch it?**
3. **What events count it?**
4. **What is the decision threshold?**
5. **How ​​can it be spoiled or screwed up?**