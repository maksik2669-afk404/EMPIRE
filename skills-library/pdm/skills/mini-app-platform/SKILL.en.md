---
name: mini-app-platform
description: 
argument-hint: [widget app platform concept for third party developers]
allowed-tools: Read, Write
preset: govtech-b2g
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Mini-app-platform



## Process

2. **Describe the requirements for Developer Experience (DX).** CLI for downloading archives, JS SDK for working with super application functions, sandbox for testing.

4. **Save the output** in the current working directory as `mini-app-platform-[context].md`.

## Output Format
```
## Mini App Platform Specification

- **JS SDK functions:** `SuperApp.pay()`, `SuperApp.getUserInfo()`.
- **Sandbox:** super application emulator in the browser for developers.
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