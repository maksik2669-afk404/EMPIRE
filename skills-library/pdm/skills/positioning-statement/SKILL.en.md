---
name: positioning-statement
description: Design product positioning using the classic Geoffrey Moore framework. The input is a description of the product and its competitors, the output is a structured positioning template, defining a frame of reference, Points of Difference and Reason to Believe.
argument-hint: [description of product and key competitors]
allowed-tools: Read, Write
preset: discovery
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Product Positioning Statement

Create a detailed positioning of a product or a new product line based on the classic Geoffrey Moore's Crossing the Chasm framework. Helps the product to formulate what niche the product occupies in the minds of the target consumer, which competitors it differentiates from and how it proves its usefulness.

## Process

1. **Identify the target customer (Target Customer) and his pain (The Statement of Need).** Who is the product intended for and what acute problem does it solve?
2. **Define the product category (Product Category / Frame of Reference).** Which “box” in the user’s head should the product fit into? (For example: CRM for developers, ERP for small businesses, fitness tracker).

4. **Formulate a reason to believe (Reason to Believe - RTB).** What facts, technologies or cases prove that we can really deliver this value (for example, integration with State Services, availability of a license from the Central Bank of the Russian Federation, algorithm of our own development)?
5. **Assemble the final positioning using the Geoffrey Moore formula:**
* **For** [target client]
* **Which** [description of pain/need]
* **Product** [name] is [product category]
* **Which** [key value/pain solution]
* **Unlike** [main competitor/alternative]
* **Our Product** [Point of Difference].
6. **Save the output** in the current working directory as `positioning-[product-name].md`.

## Output Format

```
## Product Positioning: [Product Name]

### 1. Target Client and Context of Pain (Target & Need)
- **Target Segment:** [description of the segment, its characteristics]
- **Key need/problem:** [what hurts the client, why current solutions are not satisfactory]

### 
- **Product category:** [where we classify ourselves, for example: “Digital secure payment platform for real estate transactions”]
- **The closest alternatives in the client’s head:** [what we will be compared with by default: paper letters of credit in the bank, cash in a safe deposit box, intermediary lawyers].

### 3. Points of Difference & RTB
- **Points of Difference (POD):** [our key advantage that cannot be easily copied by competitors; for example: automatic verification of ownership through Gosuslugi without manual extracts].
- **Reasons to Believe (RTB):**
- *Technical proof:* direct integration with SMEV and Rosreestr.
- *Institutional evidence:* bank-escrow agent of the first level according to the classification of the Central Bank of the Russian Federation.
- *Social proof:* more than 50,000 individual housing construction transactions have already been carried out through the platform.

### 4. Geoffrey Moore's Positioning Formulation
- **For:** [target client]
- **Which:** [description of need/problem]
- **Our product [Name]:** is [product category]
- **Which:** [key value]
- **Unlike:** [main competitor/alternative]
- **Our solution:** [Point of Difference].


> **For** suburban real estate developers **who** lose weeks to receive money after handing over a house due to paperwork with opening escrow accounts, **our Escrow-Online** service is a digital platform for integrating the bank and developer, **which** automatically opens accounts 24 hours after registration of the transaction in Rosreestr. **Unlike** classic bank letters of credit, which require a personal visit of the parties and manual verification of documents by lawyers, **our solution** works completely remotely via API and SMEV without human intervention.

### 

- **Willingness to Pay:** conversion from acquaintance with the USP to an application for different price tariffs.
- **Competitor Win Rate:** share of deals won against key competitors after repositioning.
```

## Rules

- Prohibit the use of vague product categories. If the category is formulated as “an ecosystem for everything” or “innovative software for business,” the user will not understand what it is. The category should be clear and familiar (Frame of Reference).

- Reason to Believe must be based on verifiable facts or technologies, not on subjective assessments.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?