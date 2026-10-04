# Таксономия продуктовых метрик

> Единый стандарт метрик для доменных скиллов. Каждый скилл должен отличать outcome, inputs, guardrails, diagnostics и instrumentation.

---

## Базовая структура метрик

| Уровень | Что означает | Пример |
|---|---|---|
| Outcome / North Star | Главный результат и ценность | Активные подписчики, успешные сделки, retained accounts |
| Input metrics | Управляемые рычаги outcome | activation, fill rate, first delivery success |
| Guardrails | Что нельзя ухудшить | margin, complaints, latency, fraud, churn |
| Diagnostics | Где искать причину | сегменты, когорты, каналы, гео, устройства |
| Instrumentation | Какие данные нужны | events, properties, source of truth, data quality checks |
| Decision rules | Порог решения | ship / iterate / kill |

---

## SaaS

- **Outcome:** NRR, retained ARR/MRR, active paying accounts.
- **Inputs:** activation rate, time-to-value, feature adoption, seats used, integrations connected.
- **Guardrails:** GRR, logo churn, support load, gross margin, implementation time.
- **Diagnostics:** cohort retention by segment, churn reasons, expansion/contraction bridge, account health score.
- **Instrumentation:** account_id, plan, seats, feature events, billing events, CRM segment.

---

## Subscription / D2C

- **Outcome:** active subscribers, MRR, contribution margin.
- **Inputs:** first order success, delivery SLA, referral rate, content engagement, pause return rate.
- **Guardrails:** monthly churn, refund rate, late delivery rate, complaint rate, supplier margin, quality incidents.
- **Diagnostics:** churn reason, cohort retention, CAC by channel, NPS by delivery cohort, stockout/substitution rate.
- **Instrumentation:** subscription_id, delivery_id, pause/cancel events, SKU availability, channel, refund reason.

---

## Marketplace / Classifieds

- **Outcome:** successful transactions/matches, GMV with healthy take rate, liquidity.
- **Inputs:** supply coverage, demand coverage, search success, time-to-first-match, reply rate.
- **Guardrails:** seller margin, dispute rate, cancellation rate, fraud rate, leakage/disintermediation.
- **Diagnostics:** liquidity by geo/category/price/time, supply quality, buyer conversion, seller activation.
- **Instrumentation:** buyer_id, seller_id, listing_id, category, geo, search_id, contact/match/transaction events.

---

## E-commerce / Retail

- **Outcome:** contribution margin per order, repeat purchase, paid orders.
- **Inputs:** checkout conversion, add-to-cart, availability, delivery promise accuracy, promo conversion.
- **Guardrails:** gross margin after returns, refund rate, return abuse, stockout, payment failure.
- **Diagnostics:** funnel drop-off, category, device, payment method, delivery slot, promo dependency.
- **Instrumentation:** cart_id, order_id, SKU, inventory, payment events, return/refund reason.

---

## Fintech / Lending

- **Outcome:** risk-adjusted profit, approved good customers, portfolio margin.
- **Inputs:** KYC pass rate, approval rate by risk bucket, time-to-decision, utilization.
- **Guardrails:** NPL 30/60/90, fraud loss, complaints, regulatory breaches, manual review overload.
- **Diagnostics:** vintage analysis, PD/LGD, funnel by segment, false positives/negatives, channel quality.
- **Instrumentation:** application_id, risk bucket, decision, KYC steps, repayment/vintage data, fraud flags.

---

## AI / LLM / Data Products

- **Outcome:** successful task completion, business metric uplift, user trust.
- **Inputs:** groundedness, answer relevance, precision/recall/F1, coverage, latency, cost per task.
- **Guardrails:** hallucination severity, PII leakage, unsafe output, escalation rate, model downtime.
- **Diagnostics:** eval set slices, prompt versions, retrieval quality, human review samples, drift.
- **Instrumentation:** prompt_id, model_version, retrieved_context, user feedback, confidence, escalation outcome.

---

## GovTech / Enterprise / Internal Products

- **Outcome:** successful self-service completion, employee/citizen effort reduction, cost per transaction.
- **Inputs:** first-time-right, form completion, adoption, STP automation rate, training completion.
- **Guardrails:** legal SLA breach, accessibility failures, support contact rate, rework/appeal rate.
- **Diagnostics:** vulnerable groups success, department/region, device, assisted digital, error types.
- **Instrumentation:** request_id, user segment, step events, decision SLA, support ticket, back-office status.

---

## AdTech

- **Outcome:** sustainable ad revenue and advertiser ROI.
- **Inputs:** fill rate, auction density, bid win rate, campaign creation success, budget utilization.
- **Guardrails:** organic cannibalization, ad load, user engagement drop, low ROAS, policy violations.
- **Diagnostics:** advertiser segment, placement, auction type, attribution window, creative quality.
- **Instrumentation:** impression_id, auction_id, bid, click, conversion, campaign_id, placement, attribution.

---

## Универсальное правило

Если скилл предлагает метрику, он должен ответить на 5 вопросов:

1. **Кто владеет этой метрикой?**
2. **Как часто её смотрим?**
3. **Какие события её считают?**
4. **Какой порог решения?**
5. **Как её можно испортить или накрутить?**

