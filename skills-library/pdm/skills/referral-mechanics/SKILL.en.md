---
name: referral-mechanics
description: Design a referral program or a viral loop for a product. Input — product concept, output — structured specification: incentive architecture (one/double-sided), anti-fraud protection, invitation funnel (sharing UX), and K-factor calculation.
argument-hint: [product concept for a referral program]
allowed-tools: Read, Write
preset: growth
lifecycle: any
business-model: any
domain: saas
stage: any
output-artifact: document
---

# Referral Programs and Virality (Referral Mechanics)

Create a detailed specification of a referral program or viral loop for the product. Helps the product team design an organic user acquisition loop, choose the right incentives for the inviter and the invitee, protect the system from abuse and sybil attacks, and design a seamless link-sharing UX.

## Process

1. **Determine the type of incentives (Incentive Structure).**
- *Double-sided:* both receive a bonus (ideal for B2C: '500 rubles for you and 500 rubles for a friend').
- *One-sided (Single-sided):* only one participant receives the bonus.
- *Non-monetary bonus:* disk space (Dropbox), premium access for a week, unique content.
2. **Design the invitation funnel (Share Intent UX).** How does the user share the link? (Copying the promo code, 'Share on Telegram/WhatsApp' button, importing the address book, automatic generation of a referral link).
3. **Develop validation rules and anti-fraud protection.**
- Bonus accrual conditions (for example, only after the first successful payment by the invited friend, and not for simple registration).
- Limits on the maximum amount of bonuses per month.
- Protection against multi-accounting (analysis by card details, device, IP).
4. **Describe the mathematics of virality (Viral Loop Math).** How is the K-factor calculated? (`K-factor = i × c`, where `i` is the average number of invitations sent per user, `c` is the conversion from invitation to registration). Goal: The K-factor is close to 1 for exponential growth.
5. **Save the output** in the current working directory as `referral-spec-[product-name].md`.

## Output Format

```
## Referral Program Specification: [Product Name]

### 1. Architecture of incentives (Incentives & Rules)
- **Compensation model:** [Double-sided / Single-sided / Indirect]
- **Bonus for the Referrer:** [for example, 500 bank loyalty bonus points to the account]
- **Bonus for the Referee:** [for example, a 15% discount on the first month of service]
- **Bonus payout trigger:** [the bonus is credited only after the target action is completed: first successful transaction / subscription payment by the referred person].

### 2. User Path and Sharing (User Flow & Sharing UX)
- **Referral program screen:** location in the app (profile menu → 'Invite a friend').
- **Sending mechanics:**
- The "Share" button with a call to the OS native sharing (Telegram, WhatsApp, SMS).
- Personalized message text: ["Hi! I use [Name] for work. Here’s a 15% discount on your first deal through my link: [Link]"]
- **Onboarding of the invited user:** follow the link -> automatic promo code entry on the registration screen -> welcome banner about the bonus.

### 3. Rules for Protection Against Abuses (Anti-Fraud Strategy)
Rules for blocking fraudulent activities:

| Fraud risk | Protection mechanism | System action upon detection |
|------------|-----------------|------------------------------|
| **Multi-accounts** (self-referrals) | Device ID check, phone number, payment card fingerprints | Blocking bonus accrual, transaction cancellation |
| **Bot boosting** | Limit on the number of invitations: no more than 10 invitations per day from one account | Suspension of the referral link for 24 hours |
| **Collusion with clients** | Analysis of connections in social graphs, identical IPs during transactions | Manual moderation of bonus payment |

### 4. Viral Loops and K-Factor Calculation
- **Viral Cycle (Viral Cycle Time):** the average time from the registration of the inviter to the moment of registration of the friend invited by them (target value < 5 days).
- **K-factor formula:**
- `i (Number of invites)`: the average number of clicks on the “Share” button per user.
- `c (Conversion)`: the conversion of clicks on the referral link into successful registration with the target action.
- Target `K-factor`: [for example, K = 0.15 — means that every 100 new users will bring 15 new ones for free].

### 5. Performance Metrics of the Referral Program
- **Referral Conversion Rate:** conversion from clicking on a referral link to making the first transaction.
- **Viral Coefficient (K-factor):** viral metric.
- **Referral Customer Acquisition Cost (rCAC):** average costs of acquiring one referral user (the cost of paid bonuses). Should be 30-50% lower than the standard paid CAC.
- **LTV of referral clients:** the quality of attracted users (usually they live 15-20% longer due to social approval).
```

## Rules

- Prohibit awarding cash bonuses for simple registration (sign-up). Bots and fraudsters will instantly scoop up the entire campaign budget. Bonuses should be awarded only after a valuable action by the friend (first transaction, payment).
- Having payout limits is mandatory. A strict limit must be set on the number of bonuses that one user can receive per month (for example, no more than 5,000 rubles).
- Link sharing should be seamless. Requiring the user to manually copy a long ID code and send it manually is a critical UX mistake that drastically reduces the K-factor.
- Write in English.

## Metrics (SaaS)

### Outcome metric
**NRR, retained ARR/MRR, active paying accounts.** Main result and value.

### Input metrics
**activation rate, time-to-value, feature adoption, seats used, integrations connected.** Managed levers of outcome.

### Guardrails
**GRR, logo churn, support load, gross margin, implementation time.** What must not be worsened.

### Diagnostic metrics
**cohort retention by segment, churn reasons, expansion/contraction bridge, account health score.** Where to look for the reason.

### Instrumentation
**account_id, plan, seats, feature events, billing events, CRM segment.** What data is needed.

### Decision rules
- Ship / Iterate / Kill

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**