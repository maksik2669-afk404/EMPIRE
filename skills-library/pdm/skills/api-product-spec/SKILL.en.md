---
name: api-product-spec
description: Develop an API Product Specification. The input is an integration concept, the output is a structured product document: integration scenarios (developer use cases), SLA and availability requirements, rate limits, versioning and DX (Developer Experience) requirements.
argument-hint: [description of API product or integration scenario]
allowed-tools: Read, Write
preset: platforms-tech
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# API as a product (api-product-spec)

Create a product specification for an API or integration solution (B2B API, open banking API, partner integrations). The skill helps the product design a solution from the point of view of partner developers (Developer Experience - DX), determine availability levels and rate limits, specify versioning rules and documentation/sandbox requirements.

## Process

1. **Describe Developer Use Cases.** Why would external developers call our methods? What problem does this solve for their business?
2. **Define SLA and performance requirements.**
- *Uptime:* target (for example, 99.9%).
- *Response Time (Latency):* p95 / p99 response time requirements (eg < 200ms).
3. **Develop request limits (Rate Limits & Throttling).** How many requests can one client make per second/minute (RPS/RPM) to prevent DDOS and database overload. Write the logic for processing exceeding limits (error 429 Too Many Requests).
4. **Design versioning and backwards compatibility rules.** Versioning via URLs (e.g. `/v1/`, `/v2/`) or headers. Deprecation policy.
5. **Describe the requirements for Developer Experience (DX).** Requirements for an interactive sandbox (Sandbox), test data, SDK, auto-generation of Swagger / OpenAPI documentation.
6. **Save the output** in the current working directory as `api-spec-[product-name].md`.

## Output Format

```
## API Product Specification: [API Name]

### 1. Developer Use Cases
- **Main scenario:** [for example, auto-check of Rosreestr transaction status]
- *Who is calling:* external CRM of the developer.
- *Frequency:* every time the transaction status changes.
- *Value:* the developer sees the fact of registration online and automatically sends documents to open escrow accounts.

### 2. Performance metrics and SLA
- **Target availability (Uptime SLA):** 99.95% (no more than 22 minutes of downtime per month).
- **Latency:**
- p50: < 100 ms.
- p95: < 300 ms.
- p99: < 800 ms (maximum permissible friction).

### 3. Request limits and Tariffs (Rate Limits & Quotas)
- **Basic limit (Rate Limit):** up to 10 requests per second (RPS) per organization.
- **Action when exceeded:** return HTTP 429 Too Many Requests with the `Retry-After` header.
- **Quotas:** up to 100,000 calls per month are included in the Pro tariff, then 1.5 rub. for the challenge.

### 4. Versioning Policy
- **Version format:** Versioning via URL path (`https://api.bank.ru/v1/escrow/`).
- **Backwards compatibility:** adding new optional fields to a JSON response is not considered a breaking change. Removing fields or changing types is a breaking change (requires a new major version of `/v2/`).
- **Support period for older versions (Deprecation window):** 6 months from the date of release of the new major version.

### 5. Requirements for Developer Experience (DX)
- **Sandbox:** the presence of an isolated test environment with fictitious data (test TIN, test Rosreestr transactions) to test integration without real accounts.
- **Interactive Dock:** Auto-generated Swagger UI / Redoc based on the OpenAPI 3.0 specification.
- **Error codes:** standardized error response format:
  ```json
{
"error_code": "ESCROW_LOCKED",
"message": "The escrow account is blocked by a court decision",
"timestamp": "2026-07-09T15:12:00Z"
}
  ```
```

## Rules

- Prohibit launching the API without a test sandbox (Sandbox). Forcing developers to integrate and test queries immediately on real databases or money is a gross violation of DX, leading to failures and delaying integration for months.
- Always explicitly specify request limits (Rate Limits). Without them, any crooked loop in the partner's code will crash your database servers.
- Write in English.

## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?