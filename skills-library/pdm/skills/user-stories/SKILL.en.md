---
name: user-stories
description: Turn the feature description into structured user stories with acceptance criteria, edge cases, and dependencies.
argument-hint: [feature description]
allowed-tools: Read, Write
preset: core
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Custom Story Generator

Turn a feature description into a complete set of user stories ready for sprint planning. Each story is independently deliverable and has testable acceptance criteria.

## Process

1. Read and analyze the feature description.
2. Identify the epic and break it down into independently deliverable user stories.
3. For each story, write acceptance criteria in the Given/When/Then format.
4. Identify boundary cases and negative scenarios for each story.
5. Describe the dependencies between the stories and external systems.
6. Clearly define what goes out of scope.
7. Save the result in the current working directory as `stories-[feature-name].md`.
8. **Save the output** in the current working directory as `user-stories-[context].md`.

## Output Format

### Epic Description
- Epic title
- Goal (one sentence — what does this epic give to the user?)
- Context (why now, what initiated this work)

### User Stories

For each story:

#### History [number]: [short title]

**Story:** As a [specific type of user], I want to [specific action] so that [measurable or observable result].

**Priority:** Must-have / Should-have / Nice-to-have

**Acceptance Criteria:**
- Given [precondition], When [action], Then [expected result]
- Given [precondition], When [action], Then [expected result]

**Boundary cases:**
- What happens under [non-standard condition]?
- What happens in case of an [error]?
- What happens at the [boundary value]?

**Notes:** Any implementation hints or context needed by the team.

### Dependencies
- Between stories (which stories should be completed before others)
- External dependencies (APIs, services, teams, approvals)
- Technical prerequisites

### Out of scope
- Features or behaviors explicitly excluded from the epic
- Related work that may arise in discussions but belongs to another epic

## Rules

- Each story must be independently deliverable. If a story cannot be delivered without another — either combine them or explicitly indicate the dependency.
- Acceptance criteria must be testable — the QA engineer should check each one without unnecessary questions.
- Always include negative scenarios: what happens in case of an error, timeout, invalid input, or lack of permissions.
- User stories are written from the user's perspective, not the system's. 'The system validates input' is not a user story.
- Be specific about the type of user. 'As a user' is too vague. 'As a workspace administrator with billing access' is specific.
- The benefit in 'in order to' must be real. 'In order to use the feature' is a closed loop. 'In order to add new participants without creating a support ticket' is a real benefit.
- If the feature description is too vague, list clarifying questions before writing the stories.
- Add a story size estimate (S/M/L) only if there is enough context for evaluation.
- Write in English.

## Metrics

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**