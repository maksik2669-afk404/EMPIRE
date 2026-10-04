---
name: supply-quality
description: Спроектировать систему контроля качества предложения (Supply Quality) и верификации на маркетплейсе.
argument-hint: [тип маркетплейса и описание проблемы с качеством товара/услуг]
allowed-tools: Read, Write
preset: marketplace
lifecycle: any
business-model: any
domain: marketplace
stage: any
output-artifact: document
---

# Качество предложения на маркетплейсе (supply-quality)

Спроектировать систему верификации мерчантов/партнеров и контроля качества каталога товаров или услуг на двустороннем маркетплейсе.

## Process
1. **Спроектируй онбординг-комплаенс (KYC/KYB).** Проверка юрлиц, лицензий, оригинальности брендов.
2. **Определи метрики качества продавца.** Listing Quality Score, скорость отгрузки, доля возвратов, рейтинг по отзывам.
3. **Разработай систему штрафов и бустинга.** Повышение в выдаче качественных продавцов и пессимизация/блокировка нарушителей.
4. **Сохрани вывод** в текущей рабочей директории как `supply-quality-[контекст].md`.

## Output Format
```
## Спецификация Supply Quality: [Название маркетплейса]

### 1. Правила верификации продавцов (KYB/KYC)
- Документы для старта: ОГРН, ИНН, сертификаты соответствия на бренды.
- Автоматическая проверка по реестрам ФНС.

### 2. Спецификация Seller Quality Score (SQS)
Как рассчитывается рейтинг качества продавца:
- **Рейтинг SQS (0-100%):** `0.4 * Rating + 0.3 * SLA_Shipment + 0.3 * (1 - Return_Rate)`.
- *Пессимизация:* снижение показов на 20% при SQS < 70%.
- *Блокировка:* отключение кабинета при SQS < 50%.
```

## Метрики (Marketplace / Classifieds)

### Outcome metric
**successful transactions/matches, GMV with healthy take rate, liquidity.** Главный результат и ценность.

### Input metrics
**supply coverage, demand coverage, search success, time-to-first-match, reply rate.** Управляемые рычаги outcome.

### Guardrails
**seller margin, dispute rate, cancellation rate, fraud rate, leakage/disintermediation.** Что нельзя ухудшить.

### Diagnostic metrics
**liquidity by geo/category/price/time, supply quality, buyer conversion, seller activation.** Где искать причину.

### Instrumentation
**buyer_id, seller_id, listing_id, category, geo, search_id, contact/match/transaction events.** Какие данные нужны.

### Decision rules
- Ship / Iterate / Kill

### Универсальное правило метрики
Если вы предлагаете метрику, ответьте на 5 вопросов:
1. **Кто владеет этой метрикой?**
2. **Как часто её смотрим?**
3. **Какие события её считают?**
4. **Какой порог решения?**
5. **Как её можно испортить или накрутить?**

## Rules

- Write in English.