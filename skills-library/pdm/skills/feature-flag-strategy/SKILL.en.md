---
name: feature-flag-strategy
description: Develop a strategy for the gradual rollout of features using feature flags/toggles. The input is a description of the feature, the output is a structured rollout plan: dogfooding, canary testing, targeting logic, stability monitoring metrics and a code cleanup plan (Sunset plan).
argument-hint: [description of the feature to be rolled out and stability risks]
allowed-tools: Read, Write
preset: platforms-tech
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Feature flag management (Feature Flag Strategy)

Create a detailed requirements specification for a product release using feature toggles. Helps the product and development team safely roll out functionality, minimize the risk of failures on the product through canary deployments, target features to specific user segments, and manage technical debt for clearing old flags.

## Process

1. **Define the type and life cycle of the flag.** (Release flag (temporary for rollout), operational flag (kill switch for load), experimental flag (for A/B tests)).
2. **Design Rollout Phases.**
- *Stage 1:* Internal test (dogfooding / dev environment).
- *Stage 2:* Alpha/Beta test (closed group of loyal users).
- *Stage 3:* Canary release (1% -> 5% -> 10% -> 25% -> 50% of users).
- *Stage 4:* Full rollout (100% General Availability).
3. **Describe the targeting logic (Targeting Rules).** By what criteria do we divide users? (Region/geo, application version, partner/developer ID, iOS/Android platform).
4. **Design a rollback plan (Kill Switch & Emergency Plan).** Which stability metrics are we monitoring (CPU, 5xx errors, application crashes, drop in target conversions)? Who and how has the right to instantly turn off the flag in case of an emergency?
5. **Create a code cleanup plan (Sunset & Clean-up Plan).** How and when we remove the flag from the code after 100% rollout of the feature, so as not to generate technical debt.
6. **Save the output** in the current working directory as `feature-flag-[feature-name].md`.

## Output Format

```
## Strategy for rolling out a feature through feature flags: [Feature name]

### 1. Description of the feature flag and Classification
- **Flag technical key:** `feature.mortgage.escrow.auto-release`
- **Flag type:** Release Toggle / Experimental / Operational.
- **Default state:** Disabled (FALSE) for all users.

### 2. Rollout stages and Schedule (Rollout Plan)
Plan for the gradual rollout of the feature:

| Stage | Audience share (%) | Target Cohort/Restrictions | Duration | Criteria for moving to the next step |
|------|--------------------|------------------------------|--------------|--------------------------------------|
| 1. Dogfooding | 100% (Dev) | Bank internal employees | 3 days | No critical bugs (Blockers) |
| 2. Beta | 5% | Region X pilot developers | 7 days | Positive feedback, no API errors |
| 3. Canary 1 | 10% | Random users of the Russian Federation | 3 days | Monitoring logs and crashes |
| 4. Canary 2 | 50% | Random users of the Russian Federation | 3 days | System stability metrics are normal |
| 5.GA | 100% | All system users | Constantly | Moving to the code cleanup phase |

### 3. Targeting Rules
- **Conditions for turning on the flag (Targeting Group):**
- Application version: `>= 4.12.0`
- Geo: [only Moscow and Moscow region at stages 1-3]
- Type of developer: [accredited partners with A rating]

### 4. Emergency Plan and Stability Metrics (Kill Switch)
- **Rollback Triggers:**
- Increase in 5xx errors on the `/api/v1/escrow/*` endpoints by more than 0.5%.
- Increase in the number of support calls with the topic “Error opening escrow” by more than 3 per hour.
- Increase in application crashes on iOS/Android.
- **Emergency shutdown instructions:** turning off the flag in the control panel (for example, LaunchDarkly/GitLab/own admin account) occurs instantly without re-deploying the code. The system's response time to a flag change is up to 30 seconds.

### 5. Code cleanup plan (Sunset & Clean-up)
- **Owner of the deletion task:** [Product Manager together with the Team Technical Lead].
- **Criteria for readiness for removal:** The feature works for 100% of users within 14 days without incidents.
- **Action plan:** creating a task in Jira/Trello to delete the `if (feature.flag) {} else {}` branch and removing the key itself from the flag configuration database. Deadline - no later than the end of the next sprint after 100% rollout.
```

## Rules

- Prohibit the launch of major architectural or high-risk features without feature flags. Any change in critical funnels (payment, registration, scoring) must have a Kill Switch.
- Sunset plan (cleaning plan) is required. The accumulation of old flags in the code leads to spaghetti code, more complex testing, and increased technical debt.
- When planning releases, require a description of targeting rules by application versions (especially for iOS/Android mobile platforms, where users may have older versions installed).
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?