---
name: incident-pm-role
description: Develop a checklist of PM actions in case of accidents (Incident PM Role) and a postmortem template.
argument-hint: [description of a product failure or incident for analysis]
allowed-tools: Read, Write
preset: platforms-tech
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Role of PM during incidents (incident-pm-role)

Create regulations for the product manager’s actions during a product failure/accident (Incident Management) and an incident analysis template (Postmortem) to prevent repetitions.

## Process
1. **Determine the criticality of the incident (Severity).** Sev-1 (authorization or payments are lying - everything is on fire), Sev-2 (an important feature is broken), Sev-3 (cosmetic bug).
2. **Describe the communication regulations.** Internal incident chat, status updates for stakeholders every 30 minutes, external information to clients (status page).
3. **Create Postmortem.**
- Chronology of events.
- Root Cause.
- List of tasks to prevent in the future (Action Items).
4. **Save the output** in the current working directory as `incident-pm-role-[context].md`.

## Output Format
```
## Incident Regulations and Postmortem: [Name of failure]
- **Criticality:** Sev-1.

### 1. Chronology (Incident Timeline)
- **12:00:** A spike in 500 errors was detected on the payment gateway.
- **12:10:** PM put together an incident chat and connected the backend team lead.
- **12:45:** Hotfix released, bug fixed.

### 2. Root Cause
- Changing the JSON structure in the API of a partner bank without notification (breaking change).

### 3. List of tasks (Prevention Action Items)
- [ ] Configure alerts in Grafana for increasing bank API errors.
- [ ] Rewrite the integration to be fault-tolerant with a backup script.
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