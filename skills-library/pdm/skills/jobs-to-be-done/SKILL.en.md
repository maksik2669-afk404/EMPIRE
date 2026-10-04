---
name: jobs-to-be-done
description: Apply Jobs-to-be-Done (JTBD) methodology for user needs research and product design. The input is a product or hypothesis of the problem, the output is formulated “jobs” (Jobs), a Switch interview script, force analysis (Push/Pull, Anxiety/Habit) and Job Map.
argument-hint: [product or behavior scenario under study]
allowed-tools: Read, Write
preset: discovery
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# JTBD research (Jobs-to-be-done)

Create a detailed requirements specification for user needs research based on the Jobs-to-be-Done (JTBD) methodology. Helps the product to understand the deep motivation of customers (what “job” they “hire” the product for), design questions for Switch interviews, decompose the forces of influence on the purchase decision and create a map of user steps (Job Map).

## Process

1. **Define the Core Job.** Formulate the main problem that the user is trying to solve (not through the functions of the product, but through his progress in life).
2. **Design the structure of the Switch interview.** Prepare questions to identify the user’s path from the first thought to the purchase and changing the old solution to a new one.
3. **Analyze the forces of influence (4 Forces Framework).**
- *Push:* problems with the current solution.
- *Pull:* attractiveness of a new solution.
- *Anxiety:* fears of a new decision.
- *Habit:* attachment to an old decision.
4. **Formulate the formulas for “Job Statements”.**
- Template: `When [situation/context], I want [action/decision] to make [desired outcome/progress]`.
5. **Build a Job Map.** (Define the goal → Search for options → Preparation → Launch → Execution → Control → Completion).
6. **Save the output** in the current working directory as `jtbd-spec-[context].md`.

## Output Format

```
## JTBD Product Analysis: [Product Name]

### 1. Core Job to be Done






### 
Script of questions for interviews with customers who recently bought/changed a product:
- **Starting Point (Timeline):** “Remember the moment when you first thought about buying... What happened on that day?”
- **Search for alternatives:** “What options did you consider? What have you tried before our product?”
- **Moment of purchase:** “Describe the day you made the purchase. Where were you? What prompted you?
- **Usage experience:** “How did the first transaction go? Were there any moments of doubt?”

### 3. Model of four forces (Forces of Progress)
Analysis of factors influencing the transition to our product:


|------------------------|--------------------------------|
| **Push (Pushes the old):**<br>- [dissatisfaction with the current bank]<br>- [manual paperwork] | **Anxiety (Anxiety before the new):**<br>- [fear of failure in digital escrow]<br>- [distrust of online collateral assessment] |


### 4. Job Stories / Statements
- **Job Story 1 (Beginners):**
- *When:* [description of the situation]
- *I want:* [action]
- *To:* [desired result]


- *I want:* [action]


### 
The stages that the user goes through to solve his problem (regardless of our product):


3. **Preparation:** [collection of down payment, documents].

5. **Execute:** [carrying out a transaction through the SBR].
6. **Result monitoring (Monitor):** [monitoring the disclosure of the escrow account].

```

## Rules




- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?