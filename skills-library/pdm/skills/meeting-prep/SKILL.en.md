---
name: meeting-prep
description: Create a one-page meeting brief with context, objectives, key issues, background material, expected decisions and parking. The input is the topic or agenda of the meeting, the output is a structured preparation document.
argument-hint: 
allowed-tools: Read, Write
preset: core
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# 

Create a clear one-page brief so that everyone enters in sync and comes out with solutions. Meetings without preparation are simply group therapy.

## Process

1. **Understand the context of the meeting.** Understand the topic, who is likely to attend, and what initiated the meeting.
2. **Define the goal.** What should the group leave with? A decision, alignment, plan, or information conveyed.

4. **Decide preliminary material.** What participants need to know before the meeting so as not to waste time on introducing context.
5. **List expected decisions.** What choices will be made at this meeting and who has the final say.
6. **Set up parking.** What topics are related, but clearly outside the scope of this meeting.
7. **Save the output** in the current working directory as `meeting-prep-[context].md`.

## Output Format

```
## 


### Context


### 
Leave the meeting with: [specific outcome - decision on X, alignment on Y, plan on Z]

### Key Questions to Answer




5. [Specific, answerable question] (if necessary)

### 
Participants should familiarize themselves before the meeting with:
- [Document/data/context + why this is important]
- [Document/data/context + why this is important]


### 



| [What needs to be decided] | [A vs. B] | [Who has the final word] |

### 
- [Topic that will lead the meeting astray]



### Proposed agenda (if time specified)
| Time | Topic | Presenter |

| [5 min] | Context + purpose | [facilitator] |



| [5 min] | Results + action items | [facilitator] |
```

## Rules

- The goal must be specific. “Discuss the roadmap” is not the goal. “Resolve Q3 priorities and assign responsibility” is the goal.

- Every meeting should have at least one expected decision. If there are no solutions, question whether a meeting is needed at all or whether an email is better. Say it clearly.


- The entire brief is one page. If it’s longer, the scope of the meeting is too wide, offer to break it up.

- Offer time allocation only if the duration of the meeting is specified.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?