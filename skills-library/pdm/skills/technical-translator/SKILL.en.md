---
name: technical-translator
description: Translate a technical document (API specification, architectural diagram, RFC, technical proposal) into a language understandable to the product. What does this mean for the product and users.



lifecycle: any


stage: any

---



Read the technical document and translate it into the language of product solutions. Don’t simplify it to the point of being primitive—namely, translate it. The goal is to maintain depth and nuance while making the material useful for making product decisions.

## Process

1. Read the technical document at the specified file path.
2. Identify key technical concepts, solutions, and trade-offs.
3. Translate each point into the language of influence on the product and users.

5. Highlight the decisions that the PM must make or influence.




## Output Format


1-2 sentences. What is this document about and why is it important for a product manager?

### What does this mean for the product?
- How does this change what we can build?
- Does this open up new opportunities or, conversely, close some options?
- Does this affect our roadmap or timing?
- Is there an impact on product architecture or platform strategy?

### What does this mean for users
- Will users notice the changes? (Performance, interface changes, new features, breaking changes)
- Does it affect different user segments differently?
- Will there be migrations required, downtime or changes in system behavior that are important for users to be aware of?
- Is there an impact on user data, privacy or security?

### Key decisions the PM must make
For each solution:
- What is the essence of the decision?
- What options are there?
- What are the trade-offs (in product and business terms, not technical)?
- What is the development team's recommendation and why?

### Questions for the development team
- Clarifying questions that the PM should bring to the next meeting.
- “What if...” scenarios that are not described in the document.
- Questions regarding timing and resources for validation.

### Risks
- Technical risks translated into product impact language (“If the migration fails, users will experience X”).
- Timing risks.
- Risks of dependencies.
- Assumptions in the document that may prove incorrect.

### Glossary (if necessary)
- Technical terms from the document with simple definitions in human language.
- Include only terms that the PM will encounter in the future—skip throwaway jargon.

## Rules

- Don't simplify it to the point of primitiveness. Translate. The product must understand the engineering nuances, and not read a watered-down version.
- Clearly separate what the PM MUST understand (impacts decisions) from the reference context.
- When describing trade-offs, always frame them in terms of impact on users, timeline, or cost.
- If a technical document is ambiguous, highlight that ambiguity rather than trying to guess the meaning.
- Maintain links to the structure of the source document so that the PM can easily return to the original source if necessary.
- If there is code in the document, do not copy it, but explain what it does and why it is important.
- Never invent product implications that are not supported by the technical text.
- Write in English.

## Metrics

### Universal metric rule
If you are proposing a metric, answer 5 questions:
1. **Who owns this metric?**
2. **How ​​often do we watch it?**
3. **What events count it?**
4. **What is the decision threshold?**
5. **How ​​can it be spoiled or screwed up?**