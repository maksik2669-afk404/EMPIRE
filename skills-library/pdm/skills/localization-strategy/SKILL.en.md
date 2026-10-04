---
name: localization-strategy
description: 
argument-hint: [description of product and target country for launch]
allowed-tools: Read, Write
preset: govtech-b2g
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Localization strategy (localization-strategy)



## Process
1. **Analyze regulatory requirements (Compliance).** Local laws on personal data, taxes (VAT), licensing.
2. **Adapt the interface and messages.** Language, date/time formats, cultural context.
3. **Integrate local payment methods.** Local payment gateways, currencies, taxes.
4. **Save the output** in the current working directory as `localization-strategy-[context].md`.

## Output Format
```
## Product Localization Plan: [Target Market]
- **Legal requirements:** storing citizen data on servers within the target country.

- **UX adaptation:** changing the default currency, transferring your personal account.
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