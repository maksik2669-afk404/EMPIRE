"""Подписка: бесплатный лимит, тарифы, оплата через Telegram Payments (ЮKassa и др.) или Stars.

Telegram Payments не требует ни сайта, ни вебхука: провайдер подключается в @BotFather
(Payments → ЮKassa / Сбер / ...), бот получает токен провайдера — и всё. Если токена нет,
бот принимает оплату в Telegram Stars.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone

from . import datafiles
from .money import dec
from .store import Store

FREE_ESTIMATES_DEFAULT = 3


@dataclass
class Plan:
    code: str
    title: str
    days: int
    price_rub: int
    stars: int


def plans() -> list[Plan]:
    out = []
    for row in datafiles.plans():
        try:
            out.append(Plan(code=row["code"], title=row["title"], days=int(row["days"]),
                            price_rub=int(dec(row["price_rub"])), stars=int(dec(row["stars"]))))
        except (KeyError, ValueError):
            continue
    return out


def plan(code: str) -> Plan | None:
    return next((item for item in plans() if item.code == code), None)


def free_limit() -> int:
    try:
        return int(os.getenv("SMETA_FREE_ESTIMATES", FREE_ESTIMATES_DEFAULT))
    except ValueError:
        return FREE_ESTIMATES_DEFAULT


def free_unlimited() -> bool:
    """Режим «захват клиента»: бесплатный расчёт без лимита, деньги берём на выдаче документов.

    Выключить (вернуть старый лимит бесплатных смет): SMETA_FREE_UNLIMITED=0.
    """
    return os.getenv("SMETA_FREE_UNLIMITED", "1").strip() not in {"0", "off", "false", "нет"}


def free_exports() -> bool:
    """Разрешить бесплатным пользователям скачивать готовые документы. По умолчанию — нет."""
    return os.getenv("SMETA_FREE_EXPORTS", "0").strip() in {"1", "on", "true", "да"}


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def ref_days() -> int:
    """Дни Pro пригласившему — начисляются, когда приглашённый создаёт первую смету."""
    return _int_env("SMETA_REF_DAYS", 14)


def ref_welcome_days() -> int:
    """Дни Pro новому пользователю, пришедшему по реферальной ссылке."""
    return _int_env("SMETA_REF_WELCOME", 7)


def ref_cap_days() -> int:
    """Потолок суммарных дней Pro, которые один пользователь может заработать рефералами."""
    return _int_env("SMETA_REF_CAP_DAYS", 180)


def admins() -> set[int]:
    raw = os.getenv("SMETA_ADMIN_IDS") or os.getenv("ADMIN_IDS") or ""
    return {int(part) for part in raw.replace(" ", "").split(",") if part.strip().lstrip("-").isdigit()}


def provider_token() -> str:
    return os.getenv("SMETA_PAYMENT_TOKEN", "").strip()


def billing_enabled() -> bool:
    """Set SMETA_BILLING=0 to run the bot free for everyone (e.g. while testing with friends)."""
    return os.getenv("SMETA_BILLING", "1").strip() not in {"0", "off", "false", "нет"}


def is_active(store: Store, tg_id: int, now: datetime | None = None) -> bool:
    if tg_id in admins() or not billing_enabled():
        return True
    until = store.paid_until(tg_id)
    return bool(until and until > (now or datetime.now(timezone.utc)))


def can_create(store: Store, tg_id: int) -> tuple[bool, str]:
    """May this user start one more estimate?"""
    if is_active(store, tg_id):
        return True, ""
    if free_unlimited():
        return True, ""                       # захват клиента: считаем сколько угодно, платят за документы
    used = store.settings(tg_id)["estimates_created"]
    limit = free_limit()
    if used < limit:
        return True, f"бесплатно осталось смет: {limit - used - 1}" if limit - used - 1 >= 0 else ""
    return False, f"бесплатные {limit} сметы закончились"


def can_export(store: Store, tg_id: int) -> tuple[bool, str]:
    """Готовые документы — ядро платной ценности: бесплатно доступен только расчёт на экране."""
    if is_active(store, tg_id) or not billing_enabled() or free_exports():
        return True, ""
    return False, ("📄 Готовый документ — по подписке.\n"
                   "Расчёт сметы на экране бесплатен и без ограничений, а файлы для заказчика "
                   "(смета, КП, наряд, КС-2/КС-3) открываются с подпиской.")


def tribute_secret() -> str:
    return os.getenv("SMETA_TRIBUTE_SECRET", "").strip()


def tribute_enabled() -> bool:
    return bool(tribute_secret())


def tribute_pay_url(tg_id: int) -> str:
    """Ссылка на оплату в Tribute. Поддерживает плейсхолдер {tg} — подставит Telegram id плательщика."""
    url = os.getenv("SMETA_TRIBUTE_URL", "").strip()
    return url.replace("{tg}", str(tg_id)) if url else ""


def tribute_days(product: str, amount) -> int:
    """Сколько дней подписки начислить за оплату Tribute.

    SMETA_TRIBUTE_MAP='id_месяца:30,id_года:365' сопоставляет товар Tribute с днями;
    иначе берётся SMETA_TRIBUTE_DAYS (по умолчанию 30).
    """
    mapping: dict[str, int] = {}
    for chunk in os.getenv("SMETA_TRIBUTE_MAP", "").split(","):
        key, _, days = chunk.partition(":")
        if key.strip() and days.strip().isdigit():
            mapping[key.strip()] = int(days)
    if product and product in mapping:
        return mapping[product]
    try:
        return int(os.getenv("SMETA_TRIBUTE_DAYS", "30"))
    except ValueError:
        return 30


def invoice(plan_item: Plan) -> dict:
    """Arguments for Bot.send_invoice. RUB through the provider, or Telegram Stars without one."""
    from aiogram.types import LabeledPrice

    token = provider_token()
    description = f"Подписка на Сметчик: {plan_item.title.split(' ', 1)[-1].lower()}, {plan_item.days} дн. Все функции без ограничений."
    if token:
        params = {
            "title": f"Сметчик · {plan_item.title.split(' ', 1)[-1]}",
            "description": description,
            "payload": f"sub:{plan_item.code}",
            "currency": "RUB",
            "prices": [LabeledPrice(label=plan_item.title, amount=plan_item.price_rub * 100)],
            "provider_token": token,
        }
        if os.getenv("SMETA_PAYMENT_RECEIPT", "0").strip() in {"1", "true", "да"}:
            # ЮKassa с онлайн-кассой (54-ФЗ): чек требует e-mail покупателя и состав покупки
            params["need_email"] = True
            params["send_email_to_provider"] = True
            params["provider_data"] = json.dumps({"receipt": {"items": [{
                "description": description[:128],
                "quantity": "1.00",
                "amount": {"value": f"{plan_item.price_rub:.2f}", "currency": "RUB"},
                "vat_code": int(os.getenv("SMETA_RECEIPT_VAT_CODE", "1")),
                "payment_mode": "full_payment",
                "payment_subject": "service",
            }]}}, ensure_ascii=False)
        return params
    return {
        "title": f"Сметчик · {plan_item.title.split(' ', 1)[-1]}",
        "description": description,
        "payload": f"sub:{plan_item.code}",
        "currency": "XTR",
        "prices": [LabeledPrice(label=plan_item.title, amount=plan_item.stars)],
        "provider_token": "",
    }


def activate(store: Store, tg_id: int, payload: str, amount: int, currency: str, charge_id: str) -> datetime | None:
    """Turn a successful payment into subscription days. Idempotent by charge id."""
    if not payload.startswith("sub:") or store.charge_seen(charge_id):
        return store.paid_until(tg_id)
    item = plan(payload.split(":", 1)[1])
    if item is None:
        return None
    value = f"{amount / 100:.2f}" if currency != "XTR" else str(amount)
    store.add_billing(tg_id, item.code, value, currency, charge_id)
    return store.extend_subscription(tg_id, item.days)


def promo_codes() -> dict[str, int]:
    """SMETA_PROMO='START:14,FRIEND:30' -> {'START': 14, 'FRIEND': 30}"""
    out: dict[str, int] = {}
    for chunk in os.getenv("SMETA_PROMO", "").split(","):
        code, _, days = chunk.partition(":")
        if code.strip() and days.strip().isdigit():
            out[code.strip().upper()] = int(days.strip())
    return out


def redeem(store: Store, tg_id: int, code: str) -> tuple[bool, str]:
    key = (code or "").strip().upper()
    days = promo_codes().get(key)
    if not days:
        return False, "такого промокода нет"
    if store.promo_used(tg_id, key):
        return False, "этот промокод уже использован"
    store.use_promo(tg_id, key)
    until = store.extend_subscription(tg_id, days)
    return True, f"+{days} дн. подписки, до {until.strftime('%d.%m.%Y')}"


def status_text(store: Store, tg_id: int) -> str:
    if not billing_enabled():
        return "💳 Оплата отключена — все функции бесплатны."
    if tg_id in admins():
        return "👑 Вы администратор — доступ без ограничений."
    until = store.paid_until(tg_id)
    now = datetime.now(timezone.utc)
    if until and until > now:
        return f"✅ Подписка активна до {until.strftime('%d.%m.%Y')} (осталось {(until - now).days} дн.)"
    used = store.settings(tg_id)["estimates_created"]
    if free_unlimited():
        return (f"🆓 Бесплатно: расчёт смет без ограничений (создано: {used}).\n"
                "Готовые документы — XLSX, PDF, КП, наряд, КС-2/КС-3 — открываются по подписке.")
    left = max(free_limit() - used, 0)
    return f"🆓 Бесплатный режим: создано смет {used}, осталось бесплатных {left} из {free_limit()}."
