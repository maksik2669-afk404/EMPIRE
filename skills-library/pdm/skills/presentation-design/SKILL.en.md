---
name: presentation-design
description: Create a structure and storyboard for a pitch deck to defend a new product concept to investors, the board, or C-level. The input is an idea and context, the output is a 10-slide story with Action Titles, visualization and key numbers for each slide.
argument-hint: [description of product idea, audience, goal of defense]
allowed-tools: Read, Write
preset: core
lifecycle: discovery
business-model: any
domain: generic
stage: concept
output-artifact: document
---
## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?
## Process

1. **Specify the input data:**
- **Purpose of protection:** Go/No-go by Discovery, requesting resources, obtaining funding.
- **Audience:** Investors / C-level / Product committee / External commission.
- **Key Message:** One key message for the audience to take away (for example: “Problem validated, economics are converging, pilot needed”).

2. **Use the 10-slide Gold Standard framework:**

- **Slide 2: Concept Passport (Executive Summary).** Project type, audience, problem, monetization, key advantage, pilot parameters - all in one table.

- **Slide 4: Market and Alternatives.** TAM / SAM / SOM, average bill, competitor matrix and why they don’t solve the problem.
- **Slide 5: Solution and User Journey.** A visual funnel or Checkout diagram, how the product works, key screens.

- **Slide 7: MVP and Pilot.** Release 1 (what we are doing now) vs Release 2+ (backlog), specific KPIs of the pilot (conversion, number of transactions, NPS/CSI).
- **Slide 8: Economics.** Unit economics (ARPU, COGS, Contribution Margin, CAC), BEP, P&L forecast for 12 months.
- **Slide 9: GTM Strategy.** Channels with minimal CAC, viral mechanics, compliance restrictions, and licenses.
- **Slide 10: Summary and Recommendation.** Conclusions on the 4 blocks: Problem ✓ → Solution ✓ → Economics ✓ → GTM ✓ → **Launch a pilot**.

3. **For each slide, create:**
- **Action Title** — a descriptive headline with a takeaway, not a topic ('The Economy Converges' instead of 'Finance').
- **Visualization** — what exactly is depicted (funnel, table, P&L chart, 3 cards).
- **Content** — 3-5 specific bullets with numbers, without fluff.

4. **Sanity Check:**
- Read only the Action Titles in sequence — the story should be understandable without the rest of the text.
- The last slide must have a clear call to action (Go / No-go / Pilot).
5. **Save the output** in the current working directory as `presentation-design-[context].md`.

## Output Format

```
## Slide [N]: [Action Title]
- **Visualization:** [type of visual]
- **Content:**
- [fact / figure / thesis 1]
- [fact / figure / thesis 2]
- [fact / figure / thesis 3]
```

## Rules and Restrictions
- A maximum of 3-5 entities per slide — a wall of text is unacceptable.
- All data must be concrete: survey figures, conversion calculations, market volume in rubles/units.
- Vague wording like 'we will improve the experience' is prohibited — only 'conversion to registration ≥ 15%'.
- The structure is designed for a 15-20 minute presentation + Q&A.

## Skill Success Metrics
- The audience understands the essence just by reading the Action Titles (Headline Test).
- The last slide contains a clear recommendation with a specific next step.
- The slide on the economy includes the BEP and the projected P&L.

## Rules


- Write in English.