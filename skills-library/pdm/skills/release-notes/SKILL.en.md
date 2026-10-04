---
name: release-notes
description: Turn git commits, tickets, or raw notes into user-oriented release notes. Tone setting (formal B2B, friendly B2C, internal).
argument-hint: [insert commits/tickets or file path]
allowed-tools: Read, Write, Bash
preset: core
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Release Notes Generator

Turn raw development artifacts (git commits, Jira tickets, changelogs, draft notes) into polished release notes for users. Write for people, not for engineers.

## Process

1. Read the input data — either from the specified file or from commits/tickets pasted into the argument.
2. If a path to a git repository is specified, use `git log --oneline` (in read-only mode) to retrieve the latest commits.
3. Group the changes by categories: New features, Improvements, Bug fixes.
4. Translate each technical change into user-friendly language.
5. Determine the tone from the context. If it is unclear, use the default 'Formal B2B'.
6. Write release notes.
7. Save the result in the current working directory as `release-notes-[version-or-date].md`.
8. **Save the output** in the current working directory as `release-notes-[context].md`.

## Output Format

### [Release name — descriptive, not just version number]
**Version:** [if applicable]
**Date:** [release date]

---

#### New features
For each feature:
- **[Feature Name]** — What it does and why it is important for the user. Not how it was arranged internally.

#### Improvements
For each improvement:
- **[What has improved]** — What exactly the user will notice in a better way. Be specific.

#### Bug Fixes
For each correction:
- **[What was fixed]** — Describe the problem the user encountered, not the technical root cause.

---

#### Internal notes (optional, only upon request)
- Technical details important for support, account managers, or internal stakeholders.
- Migration instructions, feature flags, rollout percentage.
- Known issues that were not fixed in this release.

## Tone Guide

**Formal B2B:**
- Professional, clear, concise.
- 'We added...' / 'This release contains...'
- Suitable for corporate clients, official changelog pages.

**Friendly B2C:**
- Warm, conversational, focused on benefits.
- "Now you can..." / "We fixed a bug that caused..."
- Suitable for mass products, in-app changelogs.

**Internal:**
- Direct, contains technical context.
- Can refer to ticket numbers, feature flags, team names.
- Suitable for updates in Slack, internal knowledge base.

## Rules

- Write for USERS, not for engineers. Translate every change into the language of benefit for the person.
- 'Fixed null pointer exception in the authorization service' turns into 'Fixed an issue that prevented some users from logging in.'
- 'Refactoring the payment module' becomes an Improvement only if users notice a difference (for example, payment processing speed) — otherwise, drop it.
- Internal refactorings without a visible effect for the user should be excluded from external notes (if necessary, move them to Internal notes).
- Group related commits into one release notes item. Five commits for one feature = one bullet.
- Never disclose internal system names, error codes, or infrastructure details in user-facing sections.
- If the tone is not specified, use the default Formal B2B.
- Each point should answer the question: 'Why should the user care?'
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?