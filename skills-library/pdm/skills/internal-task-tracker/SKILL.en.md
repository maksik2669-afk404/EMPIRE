---
name: internal-task-tracker
description: Specification for enterprise task tracking and project management system (Jira / Kaiten alternative).
argument-hint: [concept of internal issue tracker or agile project management tool]
allowed-tools: Read, Write
preset: internal-products
lifecycle: any
business-model: internal
domain: enterprise
stage: any
output-artifact: document
---

# Enterprise Task Tracker & Project Management (internal-task-tracker)

Design an internal task tracking and agile project management system (alternative to Jira, Kaiten, YouTrack): board views, customizable workflows, SLA timers, work logging, and team velocity reporting.

## Process

1. **Design Hierarchy & Workspaces:**
   - Hierarchy: Team Workspace -> Project -> Epic -> Task / Bug -> Subtask.
   - Views: Kanban boards with WIP limits, Scrum sprint backlogs, timeline / Gantt views.

2. **Design Workflow Builder:**
   - Customizable statuses (Backlog -> In Progress -> Code Review -> QA -> Done).
   - Transition rules, required fields on state change (rejection reason, PR link).
   - Automation triggers: auto-assignee, parent status sync, messenger notifications.

3. **Design SLA Timers & Work Logging:**
   - SLA tracking per stage: first response time, resolution time limit.
   - Work time logging tied to budget accounts and Git commit integrations.
   - Visual alerts for tasks approaching SLA breach.

4. **Design Reporting & Analytics:**
   - Team Velocity, Sprint Burndown charts, work distribution (Features vs Bugs vs Tech Debt).
   - Cumulative Flow Diagrams (CFD) for bottleneck detection.

5. **Formulate Team Delivery Metrics:**
   - Apply the mandatory 5-question test to every metric.

## Output Format

```markdown
# Enterprise Task Tracker Specification: [Company / Project Name]

## 1. Entity Hierarchy & Board Modes
- **Issue Types:** Epic, Story, Task, Bug, Incident.
- **Board Views:** Scrum sprints with backlog grooming, Kanban with WIP limits.

## 2. Workflow Model
| Status | Allowed Transitions | Required Actions |
| :--- | :--- | :--- |
| To Do | In Progress | Assignee selection |
| In Progress | Code Review, Blocked | Pull Request link / Blocker explanation |
| QA Testing | Done, In Progress | QA sign-off / Defect reason comment |

## 3. SLA & Time Tracking
- **Incident SLA:** Critical bugs: 15 min response, 4 hour resolution target.
- **Work Logging:** Time spent logging with Git commit hooks.

## 4. Key Metrics
- **Cycle Time:** Average duration from In Progress to Done.
- **Lead Time:** Total time from creation to deployment.
- **SLA Compliance Rate:** Share of issues resolved within target threshold.
- **WIP Limit Discipline:** Compliance with maximum concurrent task limits.
```

## Guardrails

- Focus on workflow ergonomics and engineering velocity.
- Do not use em-dashes. Use colons, periods, or standard hyphens.
- Every metric must pass the 5-question rule.
