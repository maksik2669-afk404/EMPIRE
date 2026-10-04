---
name: ab-test-design
description: Develop a full A/B test or ML experiment from a hypothesis. The input is what you want to test, the output is the design of the experiment: hypothesis, metrics, sampling, as well as ML specifics (shadow testing, Champion/Challenger).
argument-hint: [what do you want to test]
allowed-tools: Read, Write
preset: core
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# A/B test and ML experiment design (ab-test-design)

Design a plan for a product experiment or testing an ML model. The skill helps the product formulate a hypothesis, select primary and protective metrics, calculate sample size and duration, and design shadow testing and Champion/Challenger logic for artificial intelligence algorithms.

## Process

1. **Specify the type of experiment.**
- *Classic A/B test:* comparison of interfaces or logic on users.
- *ML experiment:* comparison of recommendation, ranking or scoring models.
2. **Formulate a hypothesis.** Use the template: `If we [change/model], then [metric] [direction] by [magnitude] because [causal relationship]`.
3. **Define metrics.** Choose one primary metric (decision to win), 2-3 secondary and 2-3 protective (metrics of stability, crashes, ML errors).
4. **Design ML variants (for ML tests):**
- *Shadow Testing:* launching a new model on production in “recording” mode - it calculates scores/recommendations in the background, but the old logic is shown to the user. Evaluation of offline metrics on a real data stream.
- *Champion/Challenger:* rolling out traffic to the old base model (Champion) and new experimental models (Challengers) in real time.
5. **Estimate sample size and duration.** Based on MDE (Minimum Detectable Effect), base conversion and daily traffic.
6. **Save the output** in the current working directory as `ab-test-design-[context].md`.

## Output Format

```
## Experimental Design: [Name]
- **Test type:** [Classic A/B / ML experiment]

### 1. Hypothesis
If we [change/implement model X], then [primary metric] [direction] by [X%] because [reason].

### 2. Test metrics
- **Primary metric:** [one primary metric, for example: Avg. mortgage check]
- **Secondary metrics:** [conversion per deal, limit utilization]
- **Security metrics (Guardrail):** [for ML: latency of p95 model < 200ms, error rate of 5xx model < 0.1%, NPL delay rate < 2.5%]

### 3. Rollout Scheme and Options (Rollout Strategy)
- **Control (Champion):** [current state / current ranking model]
- **Test (Challenger):** [new solution / new ML model]
- **Test mode:**
- *Shadow Testing (if applicable):* [description of shadow data collection: we write logs of the new model for 7 days, evaluate offline Precision/Recall on real applications without influencing clients].
- *Split test:* [share of traffic distribution, for example, 90/10 for a new complex ML model at the start].

### 4. Sample Size and Duration
- **Minimum Detectable Effect (MDE):** [X%]
- **Base Conversion/Value:** [Y%]
- **Sample size per option:** [N users/applications]
- **Test duration:** [X days/weeks] with [Y] daily traffic.

### 5. Risks and criteria for early termination
- **Kill Switch Criterion:** [for example, a drop in loan approval rates of more than 5% or an increase in model errors].
- **P-peeking problem:** prohibition on making decisions until the full sample is recruited.
```

## Rules

- Only one primary metric for decision making. Trying to optimize 5 metrics simultaneously leads to false positives.
- For ML models, protective performance metrics (latency, error rate) are required. A heavy model with high accuracy, but increasing the response time (latency) by 1 second, will kill the conversion to purchase.
- If the MDE is too small and the traffic is low (the test will run for > 4 weeks), request a design review (increase the MDE, choose a proxy metric with a higher event frequency).
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?