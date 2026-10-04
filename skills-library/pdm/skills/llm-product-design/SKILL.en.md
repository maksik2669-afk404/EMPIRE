---
name: llm-product-design
description: 
argument-hint: [LLM product or function concept]
allowed-tools: Read, Write
preset: platforms-tech
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Design of LLM products

Create a detailed requirements specification for integrating generative artificial intelligence based on LLM (Large Language Models) into the product. The skill helps the product design a reliable user experience, choose the right architecture for working with context, balance the cost of requests and generation speed, and set up a system for evaluating the results of the model (LLM Eval).

## Process



3. **Calculate economics and productivity (Cost vs. Latency).**
- Which model is selected (proprietary GPT-4/Claude vs. local Llama/YandexGPT)?

- Design UX to compensate for high latency (Stream text output by tokens, loaders).
4. **Describe the Prompt strategy and system prompt.** What is the role of the (Persona) model? What restrictions (System Instructions) and response format (JSON/Markdown) are specified.



## Output Format

```
## LLM Product Specification: [Name]

### 
- **Method of enriching knowledge:** RAG (search for relevant pieces from the vector database before generation) / Fine-tuning (additional training of weights).

- **Vector database and chunking:** [how we break texts into parts (chunks) and where we store vector representations (embeddings)].

### 
- **System Prompt:**
- *Role (Persona):* [for example, “You are a polite bank support assistant...”]
- *Response Rules:* [“Answer only based on the context provided. If the information is not in context, answer “I don’t know.”]
- *Security restrictions:* [prohibition on discussing competitors, disclosing system prompts, political topics].
- **Output formatting:** [Markdown markup, lists, links to original sources of docs].

### 
- **Generation model:** [for example, GPT-4o-mini / YandexGPT Pro]
- **Calculation of request cost:** [average tokenage at the input (Input Tokens) + output (Output Tokens) × cost of 1M tokens = cost of one session].


### 


| Evaluation Metric | What does it measure | How is it measured | Target value |
|----------------|--------------|----------------|------------------|
| **Factuality/Groundedness** | Presence of hallucinations (corresponding to the context) | LLM-as-a-judge / Manual Review | >= 95% |



### 5. UI/UX Scripts and Feedback Loop



```

## Rules

- Prohibit the use of LLM without strict restrictions in the System Prompt. The unrestricted model will begin to come up with non-existent tariffs or laws (hallucination). The instruction “Answer only based on the context provided” is required.
- Streaming (streaming output by tokens) is required for any user chat interface based on LLM. Waiting 5-8 seconds for a blank screen while the model generates the entire answer is a critical UX defect.

- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?