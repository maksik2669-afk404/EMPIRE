---
name: enterprise-discovery
description: Conduct a needs research (Discovery) for a large B2B Enterprise client. The input is a description of the product and the target company, the output is an interview script with the purchasing committee, a matrix of stakeholders, requirements for the pilot (PoC) and barriers of information security/lawyers.
argument-hint: [B2B product description and target corporate client profile]
allowed-tools: Read, Write
preset: b2b
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Research in Enterprise B2B (enterprise-discovery)

Conduct qualitative research (Discovery) for complex corporate products with long sales cycles. The skill helps the product to map the stakeholders of the target company, design an interview scenario with different roles (CFO, IT director, information security, business users), prescribe the criteria for a successful pilot project (Proof of Concept - PoC) and bypass formal regulatory barriers.

## Process

1. **Draw a map of the client’s purchasing committee.** Highlight the roles: Business customer (Champion), Financial director (Economic Buyer), Information security (Blocker/Security gatekeeper), End users.
2. **Develop an interview guide by role.** Questions for an Enterprise client should differ from regular B2C:
- *For the Business Customer:* about the pains of the current process, loss of time, department KPIs.
- *For IT and information security:* about system architecture, requirements for On-premise / SaaS, integration with AD/SSO, requirements of 152-FZ.
- *For CFO:* about IT budgets, current losses, procurement approval process.
3. **Design the parameters of the Pilot (Proof of Concept - PoC).** What are the minimum technical and business criteria for the success of the pilot for the client to upgrade to a paid annual license? (for example, reducing the time for preparing estimates from 5 days to 2 hours on a sample of 10 objects).
4. **Save the output** in your current working directory as `enterprise-discovery-[product-name].md`.

## Output Format

```
## Enterprise B2B Discovery: [Product Name]

### 1. Map of stakeholders of a corporate client (Target Enterprise)
- **Target organization:** [description of the company structure, for example: a large developer of suburban real estate with 500+ employees]
- **Business customer (Champion):** [head of the individual housing construction department. Pain: slow accreditation of contractors].
- **Technical stakeholder (IT/Security Blocker):** [Director of Information Security. Pain: fear of leaks of clients’ personal data to the cloud service].

### 2. Interview guide by role (Customized Interview Script)
- **Block for Business customer (Champion):**
- “How does the contractor accreditation process work now? How long does it take for one candidate?
- “What are your personal KPIs for this year for bringing new houses onto the site?”
- **Block for information security and IT (Blocker):**
- “What are your requirements for storing personal data of contractors (152-FZ)?”
- “Do you need an On-premise installation in your company’s circuit, or is a secure cloud circuit (Yandex Cloud) with encryption acceptable?”

### 3. Specification of the pilot project (Proof of Concept - PoC Design)
- **Pilot scope:** testing of the accreditation cabinet on 10 selected contractors in one branch for 30 days.
- **Pilot success criteria (for promotion to contract):**
- *Technical:* 100% of applications are successfully verified by TIN through the Dadata API within 5 minutes.
- *Business:* The time required to complete accreditation from sending the application to the decision is reduced from 14 days to 2 days.
- *Security:* Passed a basic information security audit for the absence of OWASP Top-10 vulnerabilities in the API.
```

## Rules

- Forbid ignoring the requirements of information security and IT architects in the early stages of Discovery. If a product is designing a “beautiful cloud dashboard”, but the client has a strict requirement for On-premise installation due to state secrets or a strict security policy, the project will die at the contract approval stage.
- Pilots (PoC) must have clear, digitized success criteria agreed upon with the client “on shore”. A pilot “for the pilot’s sake” without fixed purchase conditions if successful is a waste of developers’ time.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?