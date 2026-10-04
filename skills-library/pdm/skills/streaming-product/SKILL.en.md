---
name: streaming-product
description: Develop a product strategy for a streaming platform (movies, music).
argument-hint: [goals and specifics of a streaming service]
allowed-tools: Read, Write
preset: media-adtech
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Streaming Products (streaming-product)

Design a product strategy for video or audio streaming (OTT platforms, music applications) with a focus on engagement and recommendation algorithms.

## Process
1. **Describe the distribution strategy (Windowing).** At what point does the content become available by subscription, and at what point is it available for an additional fee (TVOD/EST).
2. **Design the recommendation logic.** Homepage ranking factors (viewing history, favorite genres, popular in the region).
3. **Define engagement metrics.** Attention Time (time of active viewing), Completion Rate of series/film, Subscription churn.
4. **Save the output** in the current working directory as `streaming-product-[context].md`.

## Output Format
```
## Streaming Product Strategy: [Name]
- **Monetization model:** SVOD (subscription) + TVOD (new release rentals).
- **Recommendation engine:** personalization of the first screen by 70% based on collaborative filtering algorithms.
- **Target KPI:** increase the average viewing time per user to 45 minutes per day.
```


## Rules

- Write in English.
## Metrics

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**