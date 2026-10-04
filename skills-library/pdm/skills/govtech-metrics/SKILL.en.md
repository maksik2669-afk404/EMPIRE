---
name: govtech-metrics
description: Design efficiency and quality metrics for a government or social service/portal (GovTech). The input is a description of the service or process, the output is a structured dashboard of metrics with a focus on self-service rate, accessibility, citizen CES and reducing the load on the MFC.
argument-hint: [description of government service or portal]
allowed-tools: Read, Write
preset: govtech-b2g
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# GovTech Product Metrics

Create a product specification of metrics for government services, socially significant services or city portals (analogues of State Services, Mos.ru). Helps the product switch its thinking from commercial metrics (LTV, Revenue, Churn) to social and operational metrics of efficiency, convenience of citizens and budget savings.

## Process

1. **Define the essence of the service.** What is the purpose of the service (get a certificate, register property, make an appointment with a doctor)? Who is the target applicant?
2. **Define delivery channels (Multi-channel).** How do you receive the service now: online on the portal, in person at the MFC, through the department by paper letter?
3. **Calculate the digitalization metric (Self-service Rate / Share of Online).** What proportion of citizens resolve the issue independently online without a personal visit to the authorities?
4. **Design convenience metrics (Citizen CES).** How much effort does the citizen spend? What is the time to complete the application (Time-to-completion) and the percentage of successful applications on the first try (First-time-right)?

6. **Save the output** in your current working directory as `govtech-metrics-[service-name].md`.

## Output Format

```
## GovTech Service Metrics: [Service Name]

### 1. Service Passport and User Context
- **Target result of the service:** [what document, status or right the citizen receives]
- **Target audience:** [applicant segments: pensioners, young parents, business]
- **Current receiving channels:** [Portal % | MFC % | Department %]

### 

- **Conversion Offline to Online:** rate of user migration from physical offices to the portal.


### 

- **Time-to-Completion:** the average time from the start of filling out the form to successful submission.
- **First-Time-Right Rate:** % of applications that are accepted by the department without being returned for revision/refusal due to filling errors.


### 4. Operational efficiency metrics (Back-office & Ops)




### 

- **Annual budget savings:** [Cost difference] × [Number of applications per year] = **[Amount] rub. saved.**
- **Reduction of queues:** reduction of physical flow in the MFC in FTE or man-hours.

### 6. Accessibility metrics (Accessibility / WCAG)


```

## Rules

- Prohibit the use of classic NPS as the only measure of success. In GovTech, the citizen has no choice (there are no alternative service providers), so NPS is often distorted by the attitude towards the government as a whole, rather than the quality of the interface. Use CES (Customer Effort Score) and CSAT of a specific service.
- Regulatory deadlines (SLA according to Federal Law-210) are sacred. Any excess of the specified period is a critical defect of the product. The metric “Share of overdue applications” should be in first place in the back office.
- The specification must take into account inclusivity. Everyone uses government services, including people with disabilities and low digital literacy.
- Write in English.

### Universal Metric Rule

1. **Who owns this metric?**
2. **How ​​often do we watch it?**

4. **What is the decision threshold?**
