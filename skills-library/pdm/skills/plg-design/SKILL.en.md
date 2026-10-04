---
name: plg-design
description: Design a product growth strategy using the Product-Led Growth (PLG) model. The input is a product concept, the output is a structured specification: freemium/trial design, activation points (Aha moment), upgrade triggers and a self-serve onboarding funnel.
argument-hint: [product description for PLG model design]
allowed-tools: Read, Write
preset: saas
lifecycle: any
business-model: any
domain: saas
stage: any
output-artifact: document
---

# Product-Led Growth / PLG

Create a detailed specification of a PLG model for a product (SaaS, mobile application, B2B tool). Helps the product to design a seamless user path from free use to purchase without the participation of sales managers (self-serve), determine freemium/trial limits, set up payment triggers (paywalls) and accelerate the achievement of the “Aha-moment”.

## Process

1. **Define your target free access model.**
- *Freemium:* free functionality forever with volume limitations (disk size, number of projects, API limit).
- *Free Trial:* access to all features for a limited period (7, 14, 30 days) with or without a card.
- *Reverse Trial:* access to premium for 14 days, then automatic rollback to the freemium tariff.

3. **Develop payment triggers (Upgrade Triggers).** What restrictions does the user encounter during the work process? (Resource usage limits, need for team functions (collab), access to advanced security/administration features).
4. **Describe Self-Serve Onboarding.** Step-by-step user path from landing page to the first value: interactive product tours, pre-filled templates, contextual hints on the first click.
5. **Define PLG metrics.** PQL (Product Qualified Leads - users ready to buy based on behavior in the product), Activation Rate (% of those who reached the Aha-moment), Conversion-to-Paid (conversion to paying people), Net Revenue Retention (NRR).
6. **Save the output** in the current working directory as `plg-design-[product-name].md`.

## Output Format

```
## PLG Model Specification: [Product Name]

### 1. Free-to-Paid Strategy

- **Limitations of the free version:**
- *Quantity limits:* [for example, up to 3 projects, up to 500 API requests per month].
- *Functional limitations:* [for example, no uploading of reports to PDF, no integration with Slack].

### 2. Aha Moment & Activation
- **Aha Moment Formulation:** [user took X actions in Y days, realizing value; for example: the developer created the first application and received an automatic preliminary calculation of the deposit in 5 minutes].
- **Activation Metric:** % of users who completed onboarding and performed the target action in the first 3 days.
- **Friction Reduction:** [simplification of the registration form, guest mode without entering email, ready-made project templates].

### 3. Triggers for Upgrade (Paywalls & Upgrade Triggers)


- *Collaborative trigger:* proposal to expand the tariff when adding a second/third colleague to the project.
- *Functional trigger:* inactive (locked) buttons for premium features in the interface with pop-up tooltips about the benefits of the feature.

### 

- **Ready templates:** gallery of ready-made presets for instantly starting work.


### 5. PLG Success Metrics
- **Activation Rate:** % of registered users who have reached the Aha Moment.

- **Self-Serve Conversion Rate:** conversion from registration to payment without the participation of the sales team.
- **LTV / CAC Ratio (Self-serve cohort):** unit economics of the PLG acquisition channel.
```

## Rules

- Prohibit requiring a call with a manager (Book a demo) for simple tariffs. The PLG model is based on self-onboarding. If the user cannot buy a product in one click with a card, you are violating the PLG principle, killing conversion.
- Be sure to formulate the Aha moment through user actions, and not just opening the application. The aha moment is the first real value achieved in a product.

- Write in English.

## Metrics (SaaS)

### 
**NRR, retained ARR/MRR, active paying accounts.** Main result and value.

### 


### 
**GRR, logo churn, support load, gross margin, implementation time.** What cannot be worsened.

### 


### 
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