---
name: platform-strategy
description: 
argument-hint: [description of platform product or API solution]
allowed-tools: Read, Write
preset: platforms-tech
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Platform Product Strategy

Create a product strategy for an infrastructure or platform product (API platform, system core, LLM gateway, MDM system, internal framework). The skill helps the product design the platform as a full-fledged product for developers (DX), build API Governance rules, minimize the risks of backward compatibility and measure the effectiveness of implementation.

## Process


2. **Determine the Value Proposition of the platform.** How does the platform help you release business features faster? (Reducing Time-to-Market, saving resources on writing duplicate code, standardizing security).
3. **Describe the rules of API Governance and versioning.** How does the platform manage changes to API contracts? How are breaking changes prevented, and how is the lifecycle of deprecated versions (sunset/deprecation policy) organized.
4. **Design Developer Experience (DX).** What are the requirements for documentation (Swagger/OpenAPI), sandbox (sandbox), SDK, new developer onboarding process (Time-to-first-hello-world).
5. **Define platform metrics.** Focus on Adoption Rate (what percentage of teams have switched to the platform), Latency (performance), uptime/SLA, and reducing time-to-market development of business features.
6. **Save the output** in the current working directory as `platform-strategy-[platform-name].md`.

## Output Format

```
## Platform Product Strategy: [Title]

### 1. Platform architecture and Value Proposition
- **Platform consumers:** [which teams/developers are using the platform, their tech stack and needs]
- **Product value (The "Why"):** what problem the platform solves (for example, it replaces disparate integrations with LLM with a single gateway with limits and logging).
- **Resource saving metric:** [how many man-hours does the platform save business teams by eliminating the need to write infrastructure code]

### 2. API Governance and Contracts (API Strategy)
- **API design standards:** [REST, gRPC, GraphQL - rationale for protocol choice]
- **Management of breaking changes:** backward compatibility rules, versioning (for example, semantic versioning SemVer).
- **Deprecation & Sunset Policy:**
- Duration of support for older API versions (for example, support for v1 for 6 months after the release of v2).
- Process for notification and automatic monitoring of the use of outdated endpoints.

### 3. Developer Experience (DX / Developer Experience)
- **Documentation and auto-generation:** requirements for OpenAPI/Swagger, availability of current code examples (code snippets).
- **Time-to-First-Hello-World:** Target SLA for a new developer to gain access, configure keys in the sandbox, and make the first successful test request.
- **Debugging tools:** request/response logging, clear error codes (API Error Codes) and sandbox (mock servers) for independent testing.

### 4. Migration and Implementation Strategy (Adoption Plan)
- **forced vs. organic adoption:** how we motivate teams to switch to the platform (through regulatory/security administrative requirements or through creating a super-convenient DX).
- **Rollout by cohort:** [team transition plan, starting from pilot to full scaling]
- **Legacy support scenario:** how long the platform continues to support old legacy integrations and when a complete shutdown occurs.

### 5. Platform metrics (Platform KPIs)


- **API Error Rate:** % of unsuccessful requests (4xx and 5xx errors) of the total traffic volume.
- **Developer CSAT:** assessment of developer satisfaction with the quality of the platform and DX.

### 6. Platform product risks
- **Single Point of Failure:** A platform crash stops all business features. Fault tolerance plan (redundancy, rate limiting).
- **Bottleneck:** the platform team does not have time to finalize the API to meet the needs of fast-moving business teams (self-service strategy).
```

## Rules

- Prohibit launching platforms without Developer Experience (DX). The developer is the same user. If the documentation is poor and the sandbox doesn't work, internal teams will sabotage the transition to the platform, and the project's ROI will be zero.
- The platform must have a strategy to avoid bottlenecks (Self-service). Describe how business teams can customize the features they need in the platform (for example, through plugins or internal open-source).
- Rate Limiting and circuit breaker protection are required for any common platform API.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?