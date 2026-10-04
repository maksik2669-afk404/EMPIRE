---
name: hr-portal-growth
description: Specification for employee talent development portal, onboarding, IDP, and Performance Review.
argument-hint: [concept of talent development portal or employee review system]
allowed-tools: Read, Write
preset: internal-products
lifecycle: any
business-model: internal
domain: enterprise
stage: any
output-artifact: document
---

# Employee Growth & Talent Portal (hr-portal-growth)

Design an employee growth platform: end-to-end onboarding, Individual Development Plans (IDP), competency and grade matrices, Performance Review cycles, and 360-degree feedback.

## Process

1. **Design Onboarding Experience (Welcome 30-60-90):**
   - Interactive milestone roadmaps for the first 30, 60, and 90 days.
   - Actionable checklists for the newcomer and buddy/mentor.
   - Pulse surveys measuring onboarding experience at key checkpoints.

2. **Define Professional Growth Model (IDP & Skill Matrix):**
   - Hard & Soft skills competency rubric mapped across seniority tiers (Junior -> Middle -> Senior -> Lead).
   - IDP builder: SMART goals linked to internal courses, projects, and literature.
   - Bi-weekly 1-on-1 progress check-ins.

3. **Design Performance Review & 360 Feedback Cycles:**
   - Review stages: Self-evaluation, Peer reviews, Manager assessment.
   - Calibration sessions for fair grading across teams.
   - Actionable feedback reports with grade reviews and updated development paths.

4. **Design Internal Talent Mobility:**
   - Internal job openings showcase with skills-based matching.
   - Clear transfer protocols between business units.

5. **Formulate Success Metrics:**
   - Apply the mandatory 5-question rule to every metric.

## Output Format

```markdown
# Talent Development Portal Specification: [Company / Project Name]

## 1. Onboarding Framework (30-60-90)
- **Week 1:** Setup, buddy introduction, essential checklists.
- **Day 30:** First production deliverable, initial probation pulse check.
- **Day 90:** Probation review and first IDP setup.

## 2. Competency Framework & IDP
- **Skill Rubric:** Clear requirements and artifact examples per grade.
- **IDP Structure:** 3 focus growth areas, assigned mentors, target milestones.
- **Sync:** Regular 1-on-1 notes and progress tracking.

## 3. Performance Review Protocol (360 Feedback)
| Phase | Stakeholders | Duration | Deliverable |
| :--- | :--- | :--- | :--- |
| Peer Selection | Employee + Manager | 3 days | 3-5 reviewers approved |
| Feedback Submission | Peers, Lead, Employee | 7 days | Compiled competency report |
| Calibration | Department Directors | 2 days | Calibrated ratings & compensation updates |
| 1-on-1 Feedback | Manager + Employee | 5 days | Next cycle IDP agreement |

## 4. Key Metrics
- **Probation Retention Rate:** Share of newcomers passing 90 days.
- **Employee eNPS:** Willingness to recommend the company as an employer.
- **IDP Completion Rate:** Share of employees hitting their development targets.
- **Review Cycle Duration:** Total days from launch to final 1-on-1 delivery.
```

## Guardrails

- Focus on concrete steps, timelines, and deliverables.
- Do not use em-dashes. Use colons, periods, or standard hyphens.
- Every metric must pass the 5-question test.
