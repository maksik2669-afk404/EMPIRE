---
name: persona
description: 
argument-hint: 
allowed-tools: Read, Write
preset: discovery
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# 



## Process





- **Economic Buyer:** who holds the budget and makes the final financial decision (for example, CFO, CEO). Interested in ROI, savings, payback.
- **Champion (Champion/Lobbyist):** who suffers the most without our product and will defend our implementation within the company (for example, the head of operations). Interested in convenience and speed.
- **Blocker:** who can block a transaction based on formal criteria (information security, lawyers, compliance). Interested in security, licenses, lack of risks.


4. **Describe the impact on the product (Product Impact).** What interface or functionality requirements are dictated by this profile (for example, Information Security requires SSO and 2FA, and the Economic Buyer requires a flexible cost reporting dashboard).
5. **Save the output** in the current working directory as `personas-[context].md`.

## Output Format

```
## User Personas / Buying Committee: [Product Name]
- **Mode:** [B2C Persons / B2B Purchasing Committee]

### 1. B2B Buying Committee Map
*(To be completed for B2B mode)*

| Role on the committee | Who is this in the company | Key Pain/Interest | What is he afraid of (Blocking factor) | Product Impact |
|----------------|---------------------|-------------------------|----------------------------------|------------------------------------|
| **Economic Buyer** | CFO | IT tools take a long time to pay for themselves | Hidden costs, excess TCO | Requires a detailed ROI dashboard and flexible pricing |
| **Champion** | Head of individual housing construction | Delays in transactions, routine | Delays in delivery of objects | Requires a personal account with automatic opening of escrow |
| **Blocker** | Information Security Director | Leak pers. customer data | Fines 152-FZ, break-ins | Requires authorization through Active Directory / AD, logging of all actions |
| **End User** | Estimator / Manager | Spends 3 hours downloading estimates | Complex, incomprehensible interface | Requires auto-fill fields and drag-and-drop file uploads |

### 2. Key person details (Deep Dive)
- **Descriptive name:** [for example, Alexander, Head of Individual Housing Construction (Champion)]
- **Brief summary:** [Who are they in one sentence].
- **Behavior patterns:** [frequency of working with the product, technical literacy, devices used].
- **Key Quote:**
> “[Phrase that reflects the main pain or value]”

### 3. Anti-persona (Anti-profile)
- **Who is this:** [profile of the company/user we are NOT building the product for]

```

## Rules

- In B2B products it is prohibited to focus only on the end user. If the product is convenient for the collector, but the information security director (Blocker) sees in it a threat of data leakage, the product will never be purchased. Design the requirements of all committee members.

- The “Anti-person” section is mandatory - it keeps the team from inflating the product scope for non-target requests.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?