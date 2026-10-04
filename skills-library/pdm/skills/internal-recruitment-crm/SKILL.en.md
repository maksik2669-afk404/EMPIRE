---
name: internal-recruitment-crm
description: Specification for internal HR CRM and ATS for hiring pipeline and candidate management.
argument-hint: [concept of internal recruiting CRM or Applicant Tracking System]
allowed-tools: Read, Write
preset: internal-products
lifecycle: any
business-model: internal
domain: enterprise
stage: any
output-artifact: document
---

# Internal HR CRM & Recruitment ATS (internal-recruitment-crm)

Design an internal Applicant Tracking System (ATS) and recruiting CRM: candidate pipeline, hiring manager portal, offer approval workflows, and talent acquisition analytics.

## Process

1. **Design Hiring Pipeline:**
   - Stages: Job Requisition -> Resume Screening -> HR Screen -> Technical Interview -> Final Leadership Sync -> Offer Approval -> Offer Accepted.
   - Candidate Talent Pool with skill tagging, interaction history, and GDPR / data privacy compliance.
   - Job board integrations (LinkedIn, HeadHunter, career pages, referral bots).

2. **Design Hiring Manager Portal:**
   - Job requisition request: role profile, seniority level, salary band, timeline.
   - Structured candidate scorecards (Hard & Soft skills rubric) with post-interview feedback templates.
   - 1-click offer term approvals.

3. **Design Candidate Communication Automations:**
   - Email and messenger templates triggered by pipeline stage changes.
   - Calendar booking links synced with hiring managers' Free/Busy availability.
   - Automated personalized rejection notices.

4. **Design Talent Acquisition Analytics:**
   - Funnel conversion rates across candidate sources (Direct, Referrals, Sourcing).
   - Time-in-Stage and bottleneck tracking.
   - Reason for rejection breakdown (Candidate decline vs Company decline).

5. **Formulate Hiring Performance Metrics:**
   - Apply the mandatory 5-question test to every metric.

## Output Format

```markdown
# Internal HR CRM / ATS Specification: [Company / Project Name]

## 1. Hiring Funnel Structure
- **Pipeline Stages:** Requisition -> Sourcing -> Screen -> Tech Sync -> Offer -> Onboard.
- **Scorecards:** Standardized competence evaluation forms per stage.

## 2. Hiring Manager Portal
- **Headcount Requisition:** Budget and headcount approval workflows.
- **Interview Scheduling:** Automated calendar slot coordination.

## 3. Integrations & Hand-off
- **Candidate Ingestion:** Automated resume import from job boards.
- **Handoff:** Seamless data transfer of hired candidates to the Employee SuperApp.

## 4. Key Metrics
- **Time-to-Hire:** Average calendar days from job opening to accepted offer.
- **Cost-per-Hire:** Total acquisition cost per closed role.
- **Offer Acceptance Rate:** Percentage of extended offers accepted.
- **Quality of Hire:** Share of hires successfully passing the 90-day mark.
```

## Guardrails

- Focus on reducing recruiter friction and increasing hiring speed.
- Do not use em-dashes. Use colons, periods, or standard hyphens.
- Every metric must pass the 5-question test.
