---
name: digital-workspace-superapp
description: Specification for enterprise digital workplace and employee superapp.
argument-hint: [concept of enterprise superapp or employee digital workspace]
allowed-tools: Read, Write
preset: internal-products
lifecycle: any
business-model: internal
domain: enterprise
stage: any
output-artifact: document
---

# Digital Workspace SuperApp (digital-workspace-superapp)

Design the architecture and service catalog for an enterprise employee superapp (Digital Workplace): unified self-service portal, resource booking, internal news, and productivity tools for distributed teams.

## Process

1. **Define target audience and user journeys:**
   - Office staff, remote workers, field teams, and team leads.
   - Core journeys: daily check-in, PTO/sick leave requests, desk/room booking, HR document requests, org-chart colleague discovery.

2. **Design Employee Self-Service Catalog:**
   - **HR Services:** PTO approvals, proof of employment / tax statement requests, corporate health insurance (VHI), business trips.
   - **Office & Facilities:** Guest badges, hot-desking, conference room booking, parking spot reservations.
   - **IT Services:** Hardware requests, access management, password resets.

3. **Design Engagement & Information Flow:**
   - Personalized company newsfeed segmented by department and region.
   - Virtual AI assistant answering FAQ on corporate policies and benefits.
   - Pulse surveys and eNPS feedback loops.

4. **Define Non-Functional Requirements:**
   - Multi-platform: Web Portal + Native Mobile Apps (iOS / Android).
   - SSO integration (Active Directory, Keycloak, SAML).
   - Granular role-based access control (RBAC).

5. **Formulate Success Metrics:**
   - Apply the mandatory 5-question rule to every metric.

## Output Format

```markdown
# Employee Digital Workplace Specification: [Company / Project Name]

## 1. Concept & Platform Architecture
- **Target Audience:** [Office / Remote / Field Staff]
- **Form Factor:** [Web + Mobile App]
- **Architecture Model:** [Microfrontends / Mini-Apps Catalog]

## 2. Self-Service Catalog
| Service | Category | Workflow | SLA |
| :--- | :--- | :--- | :--- |
| Employment Statement | HR | Request -> ERP Integration -> e-Document | Within 1 business day |
| Hot-Desk Booking | Facilities | Interactive Floor Map -> QR Check-in | Instant |
| PTO Request | HR | Date Selection -> Manager Approval -> Payroll | Up to 2 business days |

## 3. Engagement & Communication Flow
- **Newsfeed:** Targeted by office location and business unit.
- **AI Assistant:** Instant answers on benefits, time-off policies, and internal workflows.
- **Pulse Surveys:** 2-click monthly team pulse checks.

## 4. Key Metrics
- **Employee DAU / MAU:** Active adoption of the digital workplace.
- **Self-Service Adoption Rate:** Share of requests handled self-service vs manual HR tickets.
- **Time-to-Resolve:** Average duration from request to fulfillment.
- **Employee eNPS:** Satisfaction score for internal tooling.
```

## Guardrails

- Focus on tangible employee workflows rather than generic features.
- Do not use em-dashes. Use colons, periods, or standard hyphens.
- Every metric must answer the 5-question test (Owner, Frequency, Event triggers, Action threshold, Gaming risks).
