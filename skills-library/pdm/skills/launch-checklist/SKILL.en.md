---
name: launch-checklist
description: 
argument-hint: 
allowed-tools: Read, Write
preset: core
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# 

Create a complete, product-specific launch checklist from the product or feature description. Covers pre-launch, launch day and post-launch - with responsibilities, deadlines and blocking dependencies.

## Process

1. Read the description of the product or feature.
2. Determine the type of launch (new product, major feature, minor update, beta) to calibrate the depth of the checklist.
3. Generate a checklist adapted for a specific product - not a template.
4. Mark blocking elements against nice-to-have.
5. Turn on timing (T-2 weeks, T-1 week, Launch day, T+1 day, T+1 week).
6. Save the output in the current working directory as `launch-checklist-[product-name].md`.

## Output Format

### 
- **Product/Feature:** [name]
- **Target launch date:** [date or TBD]
- **Launch type:** New product / Major feature / Minor update / Beta
- **Target Audience:** [specific]

---

### 



#### Internal readiness
Generate 4-6 product-specific elements covering: development acceptance, QA, load testing (if applicable), rollout strategy and rollback plan. Include only elements relevant to the launch type.

#### Documentation and support


#### Preparation of communications
Generate 3-5 elements specific to this product, covering: release notes, announcements (channels depend on the product) and sales/CS training. Include only channels relevant to the audience of this product.

---

### Launch day (T-0)

#### Rollout
Generate 3-5 elements covering: deployment, verification, monitoring and duty. Adapt to the product deployment model (phased rollout, feature flags, full launch, etc.).


Generate 3-5 elements covering: publishing announcements and notifying internal teams. Include only channels relevant to this product.

#### Monitoring
Generate 3-4 items covering: error rate, performance, user requests, and support ticket volume. Refer to specific metrics from the product description.

---

### After launch (T+1 day to T+2 weeks)

#### First 24 hours
Generate 3-4 elements covering: monitoring review, triage of support requests, initial feedback and decision to expand rollout.




#### First two weeks


---

### Stakeholder checklist


|------------|--------------|--------------|--------------|--------|
| [Those. lead] | [Specific information] | [Date] | [Who notifies] | [ ] |
| [Support Team] | [Specific information] | [Date] | [Who notifies] | [ ] |
| [Sales Team] | [Specific information] | [Date] | [Who notifies] | [ ] |
| [Project Sponsor] | [Specific information] | [Date] | [Who notifies] | [ ] |
| [Marketing] | [Specific information] | [Date] | [Who notifies] | [ ] |

## Rules

- Be specific to the product. “Prepare marketing materials” is general. “Write an announcement email with an emphasis on [specific benefits of the feature] for [specific audience]” is specific.
- Each element must have a clear owner (not necessarily a name, but a role).
- Clearly mark what BLOCKS the launch against nice-to-have. Startup should not be delayed by non-blocking elements.
- Turn on timing relative to the launch date (T-2n, T-1n, T-1d, T-0, T+1d, T+1d).
- Adapt the depth to the type of launch. A minor bug fix does not require a full GTM checklist. A new product is required.
- The stakeholder checklist should include specific information for each stakeholder, and not just “inform them.”
- If the product description is too vague to generate specific elements, first list what information is needed.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?