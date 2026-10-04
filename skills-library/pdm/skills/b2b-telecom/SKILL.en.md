---
name: b2b-telecom
description: Develop a product strategy for B2B telecom products and integration with corporate IT systems.
argument-hint: [B2B telecom product concept (virtual PBX, VPN, FMC)]
allowed-tools: Read, Write
preset: telecom
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# B2B-telecom products (b2b-telecom)

Develop requirements for corporate telecom products (virtual PBX, cloud call center, VPN for business) and their integration with clients’ CRM systems.

## Process
1. **Describe integration scenarios with CRM.** Automatic opening of a client card in CRM when there is an incoming call to a virtual PBX, recording conversations.
2. **Define SLA parameters.** Availability of communication channels (for example, 99.99%), backup channels.
3. **Design a personal account for a corporate client.** Managing employee limits, ordering SIM cards.
4. **Save the output** in the current working directory as `b2b-telecom-[context].md`.

## Output Format
```
## B2B telecom product specification: [Name]
- **Integration scenario:** API webhooks for transferring call recordings to Bitrix24 / amoCRM.
- **Telephony availability SLA:** 99.99% (no more than 4 minutes of downtime per month).
- **Personal account:** managing employee SIM card budgets with monthly spending limits.
```


## Rules

- Write in English.
## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?