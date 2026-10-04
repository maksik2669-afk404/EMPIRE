# PdM Skills Agent

![Skills](https://img.shields.io/badge/Skills-130-blue) ![E2E Tested](https://img.shields.io/badge/E2E-100%25_Tested-success) ![Antigravity](https://img.shields.io/badge/AI-Agent_Ready-purple)

Библиотека из 130 структурированных инструкций для LLM, заточенных под задачи продакт-менеджера: PRD, Roadmap, User Stories, CJM, юнит-экономика, OKR, конкурентный анализ и многое другое.

Каждая инструкция написана в Markdown, содержит строгую выходную структуру с BDD-сценариями и протестирована на реальных прогонах через LLM. Без воды, без «помоги мне написать промпт» - только конкретные артефакты.

**Каталог с поиском и экспортом:** https://anton-creates.github.io/pdm-skills-agent/

---

## Как использовать

### Вариант 1 — Antigravity IDE (полноавтоматический режим)

Конфигурация встроена в папку `.agents`. Клонируйте репозиторий и откройте его в Antigravity IDE — агент автоматически загружает все 130 скиллов через `.agents/skills.json` и системный промпт из `AGENTS.md`.

Просто пишите задачу в чат:
> *«Я запускаю B2B маркетплейс, подготовь PRD и Roadmap»*

Агент сам подберёт нужные скиллы и выдаст результат по заданной структуре.

### Вариант 2 — Cursor / Windsurf / Roo Code

1. Скопируйте содержимое `.agents/AGENTS.md` в `.cursorrules` (или аналог в вашем редакторе).
2. Добавьте нужные скиллы через `@Folder` или `@File`:

```
@skills/prd @skills/roadmap Подготовь документацию для фичи авторизации.
```

### Вариант 3 — Claude Projects / OpenAI Projects

1. Создайте новый проект.
2. В «Custom Instructions» вставьте текст из `.agents/AGENTS.md`.
3. Добавьте нужные `SKILL.md` файлы в базу знаний проекта.

### Вариант 4 — Copy-Paste в любой чат LLM-ки

1. Откройте `skills/<нужный_скилл>/SKILL.md`.
2. Скопируйте блок `instructions`.
3. Вставьте как системный промпт (или первым сообщением) и передайте задачу.

---

## Структура библиотеки

| Домен | Скиллы |
|---|---|
| Ядро PdM (Core) | PRD, Roadmap, User Stories, Prioritize, Launch Checklist, Decision Doc |
| Исследования (Discovery) | Persona, CJM, Market Sizing, JTBD, User Interview, Hypothesis Tree |
| Рост и воронки | Funnel Analysis, Onboarding Audit, Referral Mechanics, Retention Model |
| Стратегия | OKR, Business Model Canvas, Business Case, Competitor Scan, Tenets |
| SaaS / B2B | Subscription Economics, Pricing Model, Enterprise Discovery, RFP Response |
| Маркетплейсы / E-com | Marketplace Model, Seller Economics, Search Ranking, Loyalty, Checkout |
| Финтех | Credit Product Spec, Fintech Teardown, Finmarket Spec |
| Платформы | Platform Strategy, Data Product, DSP/SSP, Mini App Platform |
| HR-Tech / Internal | Internal Product Discovery, Admin UX, HR Portal, Task Tracker |
| GovTech | Public Service Design, Citizen Journey, GovTech Metrics |
| Телеком / EdTech / Retail | Telecom Subscriber, B2B Telecom, B2B EdTech, Dark Store Ops |

---

## Результаты аудита

Все 130 скиллов прошли автоматический E2E-аудит: каждый прогонялся через LLM с реальными вводными данными и оценивался по структуре, полноте и наличию расчётов.

- **130 / 130** — оценка `KEEP (MUST-HAVE)`
- Средний объём артефакта: 500–1100 слов
- Расчётных таблиц в одном ответе: 10–35
- Дубликатов: 0 (подтверждено семантическим анализом)

---

## Автор

[Антон Михайлов](https://www.linkedin.com/in/anton-mikhaylove/) · [Telegram](https://t.me/mikhaylove_anton)

---

## Структура репозиториев

Проект разделён на два репозитория:

| Репозиторий | Назначение |
|---|---|
| [pdm-skills-builder](https://github.com/Anton-Creates/pdm-skills-builder) | Рабочий репо: сайт-каталог, скрипты аудита, база данных скиллов. Для внутренней разработки. |
| [pdm-skills-agent](https://github.com/Anton-Creates/pdm-skills-agent) | Дистрибутив: только скиллы и конфигурация агента. Для скачивания и использования. |

Обновление скиллов выходит сначала в pdm-skills-builder, затем синхронизируется в pdm-skills-agent.

