"""Telegram Mini App: JSON API + single-page interface, served by the bot process.

Every API call carries Telegram `initData` in the X-Init-Data header. It is checked with the
bot token (HMAC, as Telegram documents it) and must be fresh, so one user can never reach
another user's estimates even if they guess an id.

Telegram opens Mini Apps only over HTTPS: the installer puts Caddy in front of this server
and gets a certificate automatically (a domain, or <IP>.sslip.io without buying one).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from decimal import Decimal
from pathlib import Path

from aiohttp import web
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import FSInputFile
from aiogram.utils.web_app import safe_parse_webapp_init_data

from . import billing, consumption, docs, funnel, obmer, progress, tax, templates
from .builder import build, build_from_text
from .context import Deps, current, new_estimate, safe_name, save
from .export_pdf import estimate_to_pdf
from .export_xlsx import estimate_to_xlsx, margin_to_xlsx
from .model import MATERIAL, WORK, Estimate
from .money import ZERO, dec, money, rub
from .parser import DraftLine
from .profit import build_report

log = logging.getLogger(__name__)
STATIC = Path(__file__).resolve().parent / "webapp_static"
MAX_AGE = int(os.getenv("SMETA_WEBAPP_MAX_AGE", str(24 * 3600)))
DEPS_KEY = web.AppKey("deps", Deps)
BOT_KEY = web.AppKey("bot", Bot)
TOKEN_KEY = web.AppKey("token", str)


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _num(value) -> float:
    return float(value) if isinstance(value, Decimal) else value


# ---------------------------------------------------------------- serialisation


def estimate_json(estimate_id: int, estimate: Estimate) -> dict:
    totals = estimate.totals()
    positions = []
    for index, position in enumerate(estimate.positions, 1):
        positions.append({
            "index": index,
            "name": position.name,
            "code": position.code,
            "unit": position.unit,
            "kind": position.kind,
            "qty": _num(position.qty),
            "price": _num(position.unit_price_now(estimate.indices)),
            "total": _num(position.total(estimate.indices)),
            "done": _num(position.done),
            "acted": _num(position.acted),
            "crew_price": _num(position.crew_price) if position.crew_price is not None else None,
            "coef": position.k_basis,
            "note": position.note,
            "needs_price": position.total(estimate.indices) <= ZERO,
        })
    info = progress.progress(estimate)
    return {
        "id": estimate_id,
        "number": estimate.number,
        "customer": estimate.customer,
        "object": estimate.object_name,
        "contract": estimate.contract,
        "date": estimate.date.isoformat(),
        "status": estimate.status,
        "status_title": funnel.TITLES.get(estimate.status, estimate.status),
        "vat_pct": _num(estimate.vat_pct),
        "index": f"{estimate.indices.region} {estimate.indices.period}".strip(),
        "positions": positions,
        "totals": {
            "direct": _num(totals.direct), "nr": _num(totals.nr), "sp": _num(totals.sp),
            "smr": _num(totals.smr),
            "limited": [{"name": n, "pct": _num(p), "amount": _num(a)} for n, p, a in totals.limited],
            "subtotal": _num(totals.subtotal), "vat": _num(totals.vat), "total": _num(totals.total),
        },
        "discount": _num(estimate.discount_pct()),
        "warnings": estimate.warnings()[:8],
        "progress": {"done": _num(info.done), "acted": _num(info.acted), "paid": _num(info.paid),
                     "debt": _num(info.debt), "done_pct": _num(info.done_pct)},
    }


# ---------------------------------------------------------------- auth


def user_from_init_data(token: str, init_data: str, now: float | None = None) -> int:
    if not init_data:
        raise ApiError("откройте приложение из Телеграма", 401)
    try:
        parsed = safe_parse_webapp_init_data(token, init_data)
    except ValueError as error:
        raise ApiError("подпись Телеграма не сходится", 401) from error
    stamp = parsed.auth_date.timestamp() if hasattr(parsed.auth_date, "timestamp") else float(parsed.auth_date)
    if MAX_AGE and (now or time.time()) - stamp > MAX_AGE:
        raise ApiError("сессия устарела — закройте и откройте приложение заново", 401)
    if not parsed.user:
        raise ApiError("нет пользователя в данных Телеграма", 401)
    return int(parsed.user.id)


# ---------------------------------------------------------------- handlers


def _owned(deps: Deps, tg_id: int, estimate_id) -> tuple[int, Estimate]:
    try:
        estimate_id = int(estimate_id)
    except (TypeError, ValueError):
        raise ApiError("нет такой сметы", 404)
    estimate = deps.store.load_estimate(tg_id, estimate_id)
    if estimate is None:
        raise ApiError("нет такой сметы", 404)
    return estimate_id, estimate


async def api_state(request: web.Request, deps: Deps, tg_id: int, body: dict) -> dict:
    company = deps.store.company(tg_id)
    settings = deps.store.settings(tg_id)
    found = current(deps, tg_id)
    rows = deps.store.list_estimates(tg_id, limit=30)
    return {
        "company": {"name": company.name, "inn": company.inn, "filled": company.filled},
        "subscription": billing.status_text(deps.store, tg_id),
        "can_create": billing.can_create(deps.store, tg_id)[0],
        "settings": {"tax_ip": settings["tax_ip"], "tax_staff": settings["tax_staff"],
                     "tax_annual": _num(settings["tax_annual"]) if settings["tax_annual"] else None,
                     "vat_pct": _num(settings["vat_pct"])},
        "current_id": found[0] if found else None,
        "estimates": [{"id": r["id"], "number": r["number"], "total": float(dec(r["total"])),
                       "status": r["status"], "status_title": funnel.TITLES.get(r["status"], r["status"]),
                       "updated": r["updated_at"][:10]} for r in rows],
        "statuses": [{"code": c, "title": f"{i} {t}"} for c, i, t in funnel.STATUSES],
        "templates": [{"code": k, "title": v["title"]} for k, v in templates.catalog_of_templates().items()],
        "obmer_works": [{"key": k, "label": label, "var": var, "unit": unit} for k, label, _, unit, var in obmer.WORKS],
    }


async def api_create(request, deps: Deps, tg_id: int, body: dict) -> dict:
    allowed, reason = billing.can_create(deps.store, tg_id)
    if not allowed:
        raise ApiError(f"{reason} — оформите подписку в боте", 402)
    estimate_id, estimate = new_estimate(deps, tg_id, object_name=str(body.get("object", ""))[:300],
                                         customer=str(body.get("customer", ""))[:300],
                                         contract=str(body.get("contract", ""))[:200])
    return estimate_json(estimate_id, estimate)


async def api_get(request, deps: Deps, tg_id: int, body: dict) -> dict:
    estimate_id, estimate = _owned(deps, tg_id, request.match_info["id"])
    deps.store.update_settings(tg_id, current_id=estimate_id)
    return estimate_json(estimate_id, estimate)


async def api_works(request, deps: Deps, tg_id: int, body: dict) -> dict:
    estimate_id, estimate = _owned(deps, tg_id, request.match_info["id"])
    catalog = deps.store.catalog(tg_id, deps.catalog)
    matches = build_from_text(str(body.get("text", ""))[:5000], catalog, offers=deps.store.offers(tg_id, deps.offers))
    for match in matches:
        estimate.add(match.position)
    save(deps, tg_id, estimate_id, estimate)
    result = estimate_json(estimate_id, estimate)
    result["matches"] = [{"name": m.position.name, "status": m.status, "comment": m.comment} for m in matches]
    return result


async def api_position(request, deps: Deps, tg_id: int, body: dict) -> dict:
    estimate_id, estimate = _owned(deps, tg_id, request.match_info["id"])
    index = int(request.match_info["index"])
    if not 1 <= index <= len(estimate.positions):
        raise ApiError("нет такой позиции", 404)
    if body.get("delete"):
        estimate.remove(index)
    else:
        position = estimate.positions[index - 1]
        if body.get("qty") not in (None, ""):
            value = dec(body["qty"], None)
            if value is None or value <= ZERO:
                raise ApiError("объём должен быть больше нуля")
            position.qty = value
        if body.get("price") not in (None, ""):
            value = dec(body["price"], None)
            if value is None or value < ZERO:
                raise ApiError("неверная цена")
            if value != position.unit_price_now(estimate.indices):
                position.unit_price = value
                position.adj = dec(1)
                position.ot = position.em = position.zpm = position.mat = ZERO
                position.nr_pct = position.sp_pct = ZERO
                position.code = ""
        if "crew_price" in body:
            raw = body.get("crew_price")
            position.crew_price = None if raw in (None, "") else money(dec(raw))
        if body.get("done") not in (None, ""):
            try:
                progress.set_done(estimate, index, str(body["done"]))
            except ValueError as error:
                raise ApiError(str(error))
    save(deps, tg_id, estimate_id, estimate)
    return estimate_json(estimate_id, estimate)


async def api_adjust(request, deps: Deps, tg_id: int, body: dict) -> dict:
    estimate_id, estimate = _owned(deps, tg_id, request.match_info["id"])
    try:
        if body.get("reset"):
            estimate.reset_adjustments()
        elif body.get("fit") not in (None, ""):
            estimate.fit_to(dec(body["fit"]))
        else:
            scope = {"work": WORK, "material": MATERIAL}.get(body.get("scope"), "all")
            estimate.adjust(dec(body.get("percent")), scope)
    except ValueError as error:
        raise ApiError(str(error))
    save(deps, tg_id, estimate_id, estimate)
    return estimate_json(estimate_id, estimate)


async def api_status(request, deps: Deps, tg_id: int, body: dict) -> dict:
    estimate_id, estimate = _owned(deps, tg_id, request.match_info["id"])
    code = str(body.get("status", ""))
    try:
        funnel.set_status(estimate, code, str(body.get("note", ""))[:200])
    except ValueError as error:
        raise ApiError(str(error))
    save(deps, tg_id, estimate_id, estimate)
    deps.store.set_reminder(tg_id, estimate_id, funnel.remind_at() if code == "sent" else None)
    if code == "sent":
        deps.store.save_version(tg_id, estimate_id, estimate, "отправлено заказчику")
    return estimate_json(estimate_id, estimate)


async def api_materials(request, deps: Deps, tg_id: int, body: dict) -> dict:
    estimate_id, estimate = _owned(deps, tg_id, request.match_info["id"])
    consumption.apply(estimate, deps.store.offers(tg_id, deps.offers))
    save(deps, tg_id, estimate_id, estimate)
    return estimate_json(estimate_id, estimate)


DOC_KINDS = {"xlsx", "pdf", "kp", "naryad", "margin"}


async def api_document(request, deps: Deps, tg_id: int, body: dict) -> dict:
    estimate_id, estimate = _owned(deps, tg_id, request.match_info["id"])
    allowed, reason = billing.can_export(deps.store, tg_id)
    if not allowed:
        raise ApiError(reason, 402)
    kind = str(body.get("kind", ""))
    if kind not in DOC_KINDS:
        raise ApiError("неизвестный документ")
    if not estimate.positions:
        raise ApiError("в смете нет позиций")
    bot: Bot = request.app[BOT_KEY]
    deps.export_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_name(estimate.number or estimate.date.isoformat())
    if kind == "xlsx":
        path, caption = estimate_to_xlsx(estimate, deps.export_dir / f"Смета_{stem}.xlsx"), f"📄 Смета {rub(estimate.total())} ₽"
    elif kind == "pdf":
        path, caption = estimate_to_pdf(estimate, deps.export_dir / f"Смета_{stem}.pdf"), f"📕 Смета {rub(estimate.total())} ₽"
    elif kind == "kp":
        logo = next((p for p in (deps.logo_dir / f"{tg_id}.png", deps.logo_dir / f"{tg_id}.jpg") if p.exists()), None)
        path, caption = docs.kp_pdf(estimate, deps.export_dir / f"КП_{stem}.pdf", logo), "💼 Коммерческое предложение"
    elif kind == "naryad":
        path, caption = docs.naryad_xlsx(estimate, deps.export_dir / f"Наряд_{stem}.xlsx"), "👷 Наряд-задание"
    else:
        report = build_report(estimate, deps.store.offers(tg_id, deps.offers))
        path, caption = margin_to_xlsx(report, deps.export_dir / f"Профит_{stem}.xlsx", estimate), "🔒 Маржа — только для вас"
    try:
        await bot.send_document(tg_id, FSInputFile(path), caption=caption)
    finally:
        path.unlink(missing_ok=True)
    return {"ok": True, "message": "Файл отправлен в чат с ботом"}


async def api_obmer(request, deps: Deps, tg_id: int, body: dict) -> dict:
    rooms = _rooms(body)
    values = obmer.summary(rooms)
    return {"rooms": [{"name": r.name, "floor": _num(r.floor), "walls": _num(r.walls), "perimeter": _num(r.perimeter)}
                      for r in rooms],
            "summary": {k: _num(v) for k, v in values.items()}}


def _rooms(body: dict) -> list[obmer.Room]:
    rooms = []
    for item in (body.get("rooms") or [])[:50]:
        try:
            room = obmer.Room(name=str(item.get("name") or f"Помещение {len(rooms) + 1}")[:60],
                              length=dec(item.get("length")), width=dec(item.get("width")),
                              height=dec(item.get("height")), doors=int(item.get("doors") or 0),
                              windows=int(item.get("windows") or 0))
        except (TypeError, ValueError):
            raise ApiError("размеры помещения — числа")
        if min(room.length, room.width, room.height) <= ZERO:
            raise ApiError(f"«{room.name}»: размеры должны быть больше нуля")
        rooms.append(room)
    return rooms


async def api_obmer_apply(request, deps: Deps, tg_id: int, body: dict) -> dict:
    rooms = _rooms(body)
    chosen = set(body.get("works") or [])
    if not rooms or not chosen:
        raise ApiError("добавьте помещения и отметьте работы")
    values = obmer.summary(rooms)
    drafts = [DraftLine(raw=q, name=q, qty=values[var], unit=unit)
              for key, _, q, unit, var in obmer.WORKS if key in chosen and values[var] > ZERO]
    estimate_id, estimate = _target(deps, tg_id, body)
    for match in build(drafts, deps.store.catalog(tg_id, deps.catalog), offers=deps.store.offers(tg_id, deps.offers),
                       section="По обмеру"):
        estimate.add(match.position)
    save(deps, tg_id, estimate_id, estimate)
    return estimate_json(estimate_id, estimate)


def _target(deps: Deps, tg_id: int, body: dict) -> tuple[int, Estimate]:
    if body.get("estimate_id") and not body.get("new"):
        return _owned(deps, tg_id, body["estimate_id"])
    allowed, reason = billing.can_create(deps.store, tg_id)
    if not allowed:
        raise ApiError(f"{reason} — оформите подписку в боте", 402)
    return new_estimate(deps, tg_id)


def _template_values(body: dict):
    code = str(body.get("code", ""))
    if code not in templates.catalog_of_templates():
        raise ApiError("нет такого шаблона")
    try:
        if code == "bath":
            values, notes = templates.bathroom_variables(body.get("area"), body.get("height"), body.get("perimeter") or None)
        else:
            values, notes = templates.variables(body.get("area"), body.get("height"), rooms=body.get("rooms") or 1,
                                                baths=body.get("baths") or 0, perimeter=body.get("perimeter") or None)
    except ValueError as error:
        raise ApiError(str(error))
    return code, values, notes


async def api_template_preview(request, deps: Deps, tg_id: int, body: dict) -> dict:
    code, values, notes = _template_values(body)
    matches = templates.build_template(code, values, deps.store.catalog(tg_id, deps.catalog), deps.store.offers(tg_id, deps.offers))
    sample = Estimate(indices=deps.store.catalog(tg_id, deps.catalog).index(deps.store.settings(tg_id)["index_name"] or None),
                      vat_pct=deps.store.settings(tg_id)["vat_pct"])
    for match in matches:
        sample.add(match.position)
    return {"notes": notes, "total": _num(sample.total()),
            "values": {k: _num(v) for k, v in values.items()},
            "positions": [{"name": m.position.name, "qty": _num(m.position.qty), "unit": m.position.unit,
                           "total": _num(m.position.total(sample.indices)), "status": m.status} for m in matches]}


async def api_template_apply(request, deps: Deps, tg_id: int, body: dict) -> dict:
    code, values, _ = _template_values(body)
    estimate_id, estimate = _target(deps, tg_id, body)
    for match in templates.build_template(code, values, deps.store.catalog(tg_id, deps.catalog), deps.store.offers(tg_id, deps.offers)):
        estimate.add(match.position)
    save(deps, tg_id, estimate_id, estimate)
    return estimate_json(estimate_id, estimate)


def _tax_inputs(deps: Deps, tg_id: int, body: dict) -> tax.Money:
    settings = deps.store.settings(tg_id)
    for key, field in (("ip", "tax_ip"), ("staff", "tax_staff")):
        if key in body:
            deps.store.update_settings(tg_id, **{field: bool(body[key])})
    if "annual" in body:
        deps.store.update_settings(tg_id, tax_annual=dec(body["annual"], None) if body["annual"] not in (None, "") else None)
    settings = deps.store.settings(tg_id)
    if body.get("estimate_id"):
        _, estimate = _owned(deps, tg_id, body["estimate_id"])
        totals = estimate.totals()
        report = build_report(estimate, deps.store.offers(tg_id, deps.offers))
        materials = money(sum((row.cost or ZERO) for row in report.materials))
        crew = sum((p.crew_price * p.qty for p in estimate.positions if p.crew_price is not None), ZERO)
        payroll = money(crew if crew else totals.ot + totals.zpm)
        return tax.Money(revenue=estimate.total(), vat_in_revenue=totals.vat, materials=materials, payroll=payroll,
                         other_costs=money(max(report.cost_total - materials - payroll, ZERO)),
                         employees=settings["tax_staff"], ip=settings["tax_ip"], annual_revenue=settings["tax_annual"])
    revenue = dec(body.get("revenue"), None)
    if revenue is None or revenue <= ZERO:
        raise ApiError("укажите сумму договора")
    return tax.Money(revenue=revenue, materials=dec(body.get("materials")), payroll=dec(body.get("payroll")),
                     employees=settings["tax_staff"], ip=settings["tax_ip"], annual_revenue=settings["tax_annual"])


def _result_json(result: tax.TaxResult, inputs: tax.Money) -> dict:
    return {"regime": result.regime, "title": result.title, "blocked": result.blocked,
            "items": [{"name": k, "amount": _num(v)} for k, v in result.items.items()],
            "total": _num(result.total), "net": _num(result.net(inputs)), "burden": _num(result.burden(inputs)),
            "notes": result.notes}


async def api_tax(request, deps: Deps, tg_id: int, body: dict) -> dict:
    inputs = _tax_inputs(deps, tg_id, body)
    rates = tax.TaxRates.load()
    results = tax.compare(inputs, rates)
    return {"year": rates.year, "revenue": _num(inputs.revenue), "results": [_result_json(r, inputs) for r in results]}


async def api_tax_target(request, deps: Deps, tg_id: int, body: dict) -> dict:
    base = _tax_inputs(deps, tg_id, body)
    target = dec(body.get("net"), None)
    if target is None or target <= ZERO:
        raise ApiError("сколько хотите получить на руки?")
    regimes = (tax.USN6, tax.USN15, tax.OSNO_IP, tax.NPD) if base.ip else (tax.USN6, tax.USN15, tax.OSNO_OOO)
    out = []
    for regime in regimes:
        vat = tax.current_vat() if regime in (tax.OSNO_OOO, tax.OSNO_IP) else ZERO
        revenue, result, _ = tax.price_for(target, regime, materials=base.materials, payroll=base.payroll,
                                           other_costs=base.other_costs, vat_pct=vat, employees=base.employees,
                                           ip=base.ip, annual_revenue=base.annual_revenue)
        out.append({"title": result.title, "blocked": result.blocked, "revenue": _num(revenue), "vat_pct": _num(vat)})
    return {"target": _num(target), "results": out}


async def api_rates(request, deps: Deps, tg_id: int, body: dict) -> dict:
    query = str(body.get("q") or request.query.get("q", ""))[:100]
    catalog = deps.store.catalog(tg_id, deps.catalog)
    return {"results": [{"code": r.code, "name": r.name, "unit": r.unit, "score": s} for r, s in catalog.search(query, 10)]}


ROUTES = [
    ("POST", "/api/state", api_state),
    ("POST", "/api/estimates", api_create),
    ("POST", "/api/estimates/{id}", api_get),
    ("POST", "/api/estimates/{id}/works", api_works),
    ("POST", "/api/estimates/{id}/positions/{index}", api_position),
    ("POST", "/api/estimates/{id}/adjust", api_adjust),
    ("POST", "/api/estimates/{id}/status", api_status),
    ("POST", "/api/estimates/{id}/materials", api_materials),
    ("POST", "/api/estimates/{id}/document", api_document),
    ("POST", "/api/obmer", api_obmer),
    ("POST", "/api/obmer/apply", api_obmer_apply),
    ("POST", "/api/templates/preview", api_template_preview),
    ("POST", "/api/templates/apply", api_template_apply),
    ("POST", "/api/tax", api_tax),
    ("POST", "/api/tax/target", api_tax_target),
    ("POST", "/api/rates", api_rates),
]


def _wrap(handler):
    async def endpoint(request: web.Request) -> web.Response:
        try:
            tg_id = user_from_init_data(request.app[TOKEN_KEY], request.headers.get("X-Init-Data", ""))
            body = {}
            if request.can_read_body:
                try:
                    body = await request.json()
                except (json.JSONDecodeError, UnicodeDecodeError):
                    raise ApiError("тело запроса — не JSON")
                if not isinstance(body, dict):
                    raise ApiError("тело запроса — не объект")
            request.app[DEPS_KEY].store.user(tg_id)
            return web.json_response(await handler(request, request.app[DEPS_KEY], tg_id, body))
        except ApiError as error:
            return web.json_response({"error": str(error)}, status=error.status)
        except Exception:                                   # noqa: BLE001 - never leak a traceback to the client
            log.exception("webapp api failed")
            return web.json_response({"error": "внутренняя ошибка, попробуйте ещё раз"}, status=500)
    return endpoint


# ---------------------------------------------------------------- Tribute (СБП) webhook
#
# Платёж проходит ВНУТРИ Tribute (он — merchant of record: сам выбивает чек по 54-ФЗ и
# платит нам). Мы лишь принимаем подписанный вебхук об успешной оплате и начисляем дни.
# Точные имена полей и схема подписи Tribute здесь заданы «с запасом» и логируются целиком
# при первом реальном вебхуке — по нему _tribute_extract/_tribute_signature_ok и фиксируются.

TRIBUTE_SIG_HEADERS = ("trbt-signature", "X-Tribute-Signature", "tribute-signature", "X-Signature")
TRIBUTE_PAID = {"", "paid", "success", "successful", "completed", "payment", "order.paid",
                "order_paid", "new_donation", "new_subscription", "subscription"}


def _tribute_signature_ok(raw: bytes, signature: str) -> bool:
    secret = billing.tribute_secret()
    if not secret or not signature:
        return False
    mac = hmac.new(secret.encode(), raw, hashlib.sha256)
    candidates = {mac.hexdigest(), base64.b64encode(mac.digest()).decode()}
    sig = signature.strip()
    if "=" in sig and sig.split("=", 1)[0].lower() in {"sha256", "hmac-sha256"}:
        sig = sig.split("=", 1)[1]
    return any(hmac.compare_digest(sig, c) or hmac.compare_digest(sig.lower(), c.lower())
               for c in candidates)


def _tribute_extract(payload: dict) -> dict:
    """Достаём из полезной нагрузки то, что нам нужно, пробуя разные имена полей."""
    data = payload.get("payload") or payload.get("data") or payload
    data = data if isinstance(data, dict) else {}

    def pick(*keys):
        for k in keys:
            value = data.get(k)
            if value in (None, ""):
                value = payload.get(k)
            if value not in (None, ""):
                return value
        return None

    tg = pick("telegram_user_id", "telegramUserId", "telegram_id", "telegramId",
              "user_telegram_id", "tg_id", "userId", "user_id")
    status = str(payload.get("name") or payload.get("event") or payload.get("type")
                 or pick("status", "state") or "").lower()
    return {
        "status": status,
        "charge_id": str(pick("order_id", "orderId", "uuid", "transaction_id", "payment_id", "id") or ""),
        "tg_id": int(tg) if tg is not None and str(tg).lstrip("-").isdigit() else 0,
        "product": str(pick("product_id", "productId", "product", "subscription_name", "name", "item") or ""),
        "amount": dec(pick("amount", "price", "sum", "total") or 0),
        "currency": str(pick("currency", "cur") or "RUB"),
    }


async def tribute_webhook(request: web.Request) -> web.Response:
    if not billing.tribute_enabled():
        return web.json_response({"error": "tribute disabled"}, status=503)
    raw = await request.read()
    signature = next((request.headers.get(h) for h in TRIBUTE_SIG_HEADERS if request.headers.get(h)), "")
    if not _tribute_signature_ok(raw, signature):
        log.warning("tribute webhook: подпись не сошлась")
        return web.json_response({"error": "bad signature"}, status=401)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return web.json_response({"error": "bad json"}, status=400)
    if not isinstance(payload, dict):
        return web.json_response({"error": "bad json"}, status=400)
    log.info("tribute webhook payload: %s", raw.decode("utf-8", "replace")[:2000])
    fields = _tribute_extract(payload)
    if fields["status"] and fields["status"] not in TRIBUTE_PAID:
        return web.json_response({"ok": True, "ignored": fields["status"]})
    tg_id, charge_id = fields["tg_id"], fields["charge_id"]
    if not tg_id or not charge_id:
        log.error("tribute webhook: не нашёл tg_id/charge_id — поправьте _tribute_extract под реальный payload")
        return web.json_response({"error": "no user or charge id"}, status=422)
    deps: Deps = request.app[DEPS_KEY]
    bot: Bot = request.app[BOT_KEY]
    if deps.store.charge_seen(charge_id):
        return web.json_response({"ok": True, "duplicate": True})
    days = billing.tribute_days(fields["product"], fields["amount"])
    deps.store.user(tg_id)
    until = deps.store.extend_subscription(tg_id, days)
    deps.store.add_billing(tg_id, f"tribute:{fields['product'] or 'onetime'}",
                           str(fields["amount"]), fields["currency"], charge_id)
    try:
        await bot.send_message(tg_id, f"✅ Оплата получена. Подписка активна до {until:%d.%m.%Y}. Спасибо!")
    except (TelegramForbiddenError, TelegramBadRequest):
        pass
    log.info("tribute: +%s дн. пользователю %s до %s", days, tg_id, until)
    return web.json_response({"ok": True})


async def index(request: web.Request) -> web.Response:
    return web.FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})


async def health(request: web.Request) -> web.Response:
    return web.json_response({"ok": True})


def create_app(deps: Deps, bot: Bot, token: str) -> web.Application:
    app = web.Application(client_max_size=2 * 1024 * 1024)
    app[DEPS_KEY], app[BOT_KEY], app[TOKEN_KEY] = deps, bot, token
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_post("/tribute/webhook", tribute_webhook)   # приём оплат Tribute (без initData)
    for method, path, handler in ROUTES:
        app.router.add_route(method, path, _wrap(handler))
    return app


async def start(deps: Deps, bot: Bot, token: str) -> web.AppRunner | None:
    """Start the Mini App server if SMETA_WEBAPP_URL is set. Returns the runner to clean up."""
    if not os.getenv("SMETA_WEBAPP_URL", "").strip():
        return None
    runner = web.AppRunner(create_app(deps, bot, token))
    await runner.setup()
    host = os.getenv("SMETA_WEBAPP_HOST", "127.0.0.1")
    port = int(os.getenv("SMETA_WEBAPP_PORT", "8080"))
    await web.TCPSite(runner, host, port).start()
    log.info("Мини-апп слушает %s:%s → %s", host, port, os.getenv("SMETA_WEBAPP_URL"))
    return runner


def webapp_url() -> str:
    url = os.getenv("SMETA_WEBAPP_URL", "").strip()
    return url if url.startswith("https://") else ""
