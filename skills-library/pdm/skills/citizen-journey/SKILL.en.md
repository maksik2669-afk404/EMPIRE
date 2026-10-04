---
name: citizen-journey
description: Design a Citizen Journey through a government portal or digital government service.
argument-hint: [description of public service or process for design]
allowed-tools: Read, Write
preset: govtech-b2g
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Citizen-journey

Design a citizen’s path when receiving a government service online (for example, State Services, Mos.ru), identify points of friction and accessibility of the service for all categories of people.

## Process
1. **Describe the steps of the Citizen Journey Map.** Search for a service -> Verify rights -> Fill out the form -> Attach documents -> Application status -> Result.
2. **Assess accessibility.** Compliance with WCAG standards (visually impaired, elderly, mobile devices).
3. **Identify friction points.** Authorization failures for State Services (USIA), complex legal formulations.
4. **Save the output** in the current working directory as `citizen-journey-[context].md`.

## Output Format
```
## Citizen Journey Map: [Service Name]
- **Target citizen:** [profile, for example: pensioner applying for a benefit]
- **Drop-off points:** drop in conversion at the step of uploading a scan of a passport in PDF format.
- **Recommendations for accessibility:** simplify the form, use auto-filling of data from the personal account of the State Services.
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