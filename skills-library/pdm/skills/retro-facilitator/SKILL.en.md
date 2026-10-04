---
name: retro-facilitator
description: Facilitate the team's retrospective. Generate a retro board with prompts (formats 4Ls, Start-Stop-Continue, Sailboat) or synthesize notes from retrospectives into grouped themes and prioritized actions.
argument-hint: [retro format: 4Ls, start-stop-continue, sailboat or insert notes for synthesis]
allowed-tools: Read, Write
preset: core
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Retrospective Facilitator

Two modes: GENERATING a retrospective board with prompts or SYNTHESIZING raw notes from a retro into themes and specific actions. Retrospectives without follow-up actions are just complaint sessions.

## Process

### Definition of the mode
- If the input is the name of a format (4Ls, start-stop-continue, sailboat) → GENERATION mode.
- If inserted notes, bullets, or raw feedback are input → SYNTHESIS mode.
- If it's unclear — ask.

### GENERATION Mode
1. **Choose a format.** Determine what format of retrospectives the user needs.
2. **Create sections.** Build the board structure for this format with descriptions of the sections.
3. **Add starter questions.** 2-3 leading questions for the section to start the discussion.
4. **Add facilitation tips.** How to effectively conduct each section.
5. **Suggest a timeline.** By default, based on a 60-minute meeting.

### SYNTHESIS Mode
1. **Collect the notes.** Read all the raw input data — stickers, lists, free text.
2. **Group by topics.** Combine related items. Name each topic clearly and concisely.
3. **Prioritize topics.** Rank by frequency (how many people mentioned it) and impact (how strongly it affects the team).
4. **Form action items.** Each action should include: what to do, who is doing it, and by what deadline.
5. **Identify patterns.** If the context of past retros is available, note recurring themes.
6. **Save the output** in the current working directory as `retro-facilitator-[context].md`.

## Output Format

### GENERATION Mode
```
## Retro board: [Format name]
**Duration:** 60 minutes | **Team size:** [adjust if specified]

### Format Overview
[2-3 sentences explaining this retro format and when it is best to use it.]

### Section 1: [Title]
**What to write here:** [description]
**Starting questions:**
- [A specific question to start the discussion]
- [A specific question to start the discussion]
- [A specific question to start the discussion]
**Facilitation Tip:** [How to moderate this section]

### Section 2: [Title]
[the same structure]

### Section 3: [Title]
[the same structure]

### Section 4: [Title] (if applicable)
[the same structure]

### Meeting Schedule
| Stage | Duration | Notes |
|------|--------------|------------|
| Check-in | 5 min | Quick round — describe the sprint in one word |
| Silent writing | 10 min | Everyone writes cards/stickers silently |
| Grouping and discussion | 25 min | Reading, clustering, voting for top topics |
| Action Plan (actions) | 15 min | Assignment of persons responsible and deadlines |
| Checkout | 5 min | One main insight from each |

### Tips for the facilitator
- [Tip for creating psychological safety]
- [Advice on maintaining a productive discussion flow]
- [Advice on mandatory attachment of actions]
```

### SYNTHESIS Mode
```
## Retrospective Synthesis: [Date/Sprint]

### Topics (ranked by frequency + impact)

#### Topic 1: [Title] (mentioned by [N] people)
- [Grouped note item]
- [Grouped note item]
- [Grouped note item]
**Root cause:** [Hypothesis of the root cause in one sentence]

#### Topic 2: [Title] (mentioned by [N] people)
- [Grouped note item]
- [Grouped note item]
**Root cause:** [Hypothesis of the root cause in one sentence]

#### Topic 3: [Title]
[the same structure]

### Action Plan (Action Items)
| # | Action (Specific Action) | Responsible | Deadline | Topic |
|---|-----------------------------|---------------|------|------|
| 1 | [Specific, clear task] | [name/role] | [date] | Topic 1 |
| 2 | [Specific, clear task] | [name/role] | [date] | Topic 2 |
| 3 | [Specific, clear task] | [name/role] | [date] | Topic 1 |

### Patterns (if there is data from previous retros)
- **Recurring issues:** [Topic that arises again] — previous actions did not work.
- **New:** [Topic that has arisen for the first time] — requires targeted attention.
- **Resolved:** [Topic from the last retro that didn't come up now] — the actions worked.

### Team Health (Signal)
[Summary in one sentence: Is the team dynamic going up, down, or stable based on these notes?]
```

## Supported Formats

### 4Ls
- **Loved (What we liked):** What went well and what we want to continue doing.
- **Learned (What we learned):** What we discovered about ourselves or what insights we gained.
- **Lacked (What was missing):** What was missing or was insufficient.
- **Longed For (What one would like):** What we would really like to have in the future.

### Start-Stop-Continue
- **Start (Start):** What it costs us to start doing.
- **Stop:** What we need to stop doing.
- **Continue (Continue):** What works well and needs to be reinforced.

### Sailboat (Sailboat)
- **Wind (what moves us):** The forces that push us forward.
- **Anchor (what holds us back):** What slows down our progress.
- **Reefs (risks ahead):** Obstacles that can harm us.
- **Island (goal):** Where we strive to reach.

## Rules

- In GENERATION mode, the starting questions should be adapted to the context of the team, if it is provided. Template questions like "What went well?" waste people's time.
- In SYNTHESIS mode, each topic must have at least one action. A topic without an action is just a statement of fact.
- Actions should be specific and have an owner. 'Improve communication' is not an action. 'Schedule a daily 15-minute sync for the next 2 weeks — owner [Name]' is an action.
- Do not highlight more than 5 topics during synthesis. If there are more, combine the smaller ones.
- A maximum of 5 actions at the output. Teams leaving the retro with 10 tasks complete zero.
- Always output the team health signal in synthesis mode. Retrospection is needed for continuous improvement — track the vector.
- If the notes are too sparse for synthesis (fewer than 5 points) — say so directly and indicate that the team needs to develop psychological safety for honest feedback.
- Write in English.

## Metrics

### Universal Metric Rule
If you are suggesting a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How often do we watch it?**
3. **Which events consider her?**
4. **What is the decision threshold?**
5. **How can it be spoiled or manipulated?**