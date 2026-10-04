---
name: admin-ux
description: Design the interface and logic of the admin panel (Admin UX) for internal use.
argument-hint: [description of admin functions and admin roles]
allowed-tools: Read, Write
preset: internal-products
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Designing admin panels (admin-ux)

Design UX/UI admin panels (back-office) for support staff, moderators or marketplace/bank operators.

## Process
1. **Focus on the task (Task-oriented UX).** The admin panel should be fast and functional, beauty comes second.
2. **Design foolproof protection (Error Prevention).** Confirmation of critical actions (deletion, blocking, tariff change), logging changes (Audit Trail).
3. **Describe Bulk Actions.** Select 100 users -> block with one button.
4. **Save the output** in the current working directory as `admin-ux-[context].md`.

## Output Format
```
## UX Admin Panel Specification: [Module]
- **Critical action (Delete account):** requires entering the word “DELETE” to confirm the action by the operator.
- **Audit Trail:** logging operator IP, time and old/new parameter values ​​in the database for any change.
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