---
name: corp-communication-suite
description: Specification for enterprise communication tools: secure messenger, email, video conferencing, and PBX telephony.
argument-hint: [concept of enterprise messenger, video conferencing, or telephony system]
allowed-tools: Read, Write
preset: internal-products
lifecycle: any
business-model: internal
domain: enterprise
stage: any
output-artifact: document
---

# Enterprise Communication Suite (corp-communication-suite)

Design a secure internal communication infrastructure: enterprise instant messaging, corporate email and calendar, video conferencing (VCS), and cloud PBX telephony.

## Process

1. **Design Enterprise Messenger:**
   - Public and private channels, focused threads, direct 1-on-1 chats.
   - Deep org-chart integration: find colleagues by department, title, and project.
   - Bot & webhook ecosystem for CI/CD, issue tracking, and system alerts.
   - Enterprise security: DLP rules, file transfer controls, two-factor authentication.

2. **Design Video Conferencing System:**
   - 1-on-1 calls and large meetings up to 100+ attendees.
   - Screen sharing, noise suppression, virtual backgrounds, breakout rooms.
   - Cloud recording with automated AI transcription and meeting notes summary.

3. **Design Mail & Calendar Scheduling:**
   - Multi-attendee Free/Busy calendar slot discovery.
   - Automated video conference link generation.
   - Anti-phishing protection and smart inbox sorting.

4. **Design Cloud PBX & Enterprise Telephony:**
   - Multi-branch call routing and hunt groups.
   - Call logs, call recording, and CRM integration for contact centers.

5. **Formulate Quality & Reliability Metrics:**
   - Apply the mandatory 5-question test to every metric.

## Output Format

```markdown
# Enterprise Communications Specification: [Company / Project Name]

## 1. Corporate Messenger
- **Hierarchy:** Company-wide channels -> Project rooms -> Message threads.
- **Integrations:** Service Desk tickets, deploy bots, monitoring alerts.
- **Security:** End-to-end encryption in transit, session audit logs.

## 2. Video Conferencing
- **Capacity:** High-def video meetings for up to 150 participants.
- **Features:** In-browser WebRTC support, cloud recording, AI meeting notes.

## 3. Cloud Telephony / PBX
- **Use Cases:** Customer support hotline, internal extension dialing.
- **Routing:** Skill-based and queue-based load balancing.

## 4. Key Metrics
- **Service Uptime:** 99.95% availability SLA.
- **Call Quality CSAT:** Post-meeting user ratings.
- **Message Latency:** Under 200ms end-to-end delivery time.
- **Active Communication MAU:** Monthly active team engagement.
```

## Guardrails

- Focus on data protection, low latency, and enterprise reliability.
- Do not use em-dashes. Use colons, periods, or standard hyphens.
- Every metric must answer the 5-question rule.
