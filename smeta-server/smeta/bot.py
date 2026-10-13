"""Telegram bot: main menu, screens with «Назад» everywhere, input wizards, files, payments, reminders."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from html import escape
from io import BytesIO
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    MenuButtonWebApp,
    WebAppInfo,
    FSInputFile,
    InlineKeyboardButton as Button,
    InlineKeyboardMarkup as Markup,
    Message,
    PreCheckoutQuery,
)

from . import (
    billing, consumption, datafiles, docs, funnel, importer, obmer, progress, render, tax, templates, ui, webapp,
)
from .audit import audit, report_xlsx
from .builder import build, build_from_text
from .catalog import Catalog
from .context import Ctx, Deps, current, new_estimate, safe_name, save
from .export_pdf import estimate_to_pdf
from .export_xlsx import estimate_to_xlsx, margin_to_xlsx
from .materials import OfferBook
from .model import MATERIAL, WORK, Company, Estimate
from .money import ZERO, dec, money, pct, rub
from .parser import DraftLine
from .profit import build_report
from .reprice import reprice
from .store import Store
from .versions import diff

log = logging.getLogger(__name__)
router = Router()
__all__ = ["Deps", "router", "build_deps", "main", "run_reminders"]


class Flow(StatesGroup):
    input = State()


# ================================================================== navigation


def _ctx(deps: Deps, tg_id: int, data: dict) -> Ctx:
    return Ctx(deps=deps, tg_id=tg_id, data=data)


async def _stack(state: FSMContext) -> list[str]:
    return list((await state.get_data()).get("nav") or ["home"])


async def _push(state: FSMContext, screen: str) -> None:
    stack = await _stack(state)
    if stack and stack[-1].split(":")[0] == screen.split(":")[0]:
        stack[-1] = screen                    # листание страниц и соседних позиций не копит «Назад»
    else:
        stack.append(screen)
    await state.update_data(nav=stack[-20:])


async def _paint(target: Message | CallbackQuery, text: str, markup: Markup, *, edit: bool = True) -> None:
    if isinstance(target, CallbackQuery):
        if edit and target.message is not None:
            try:
                await target.message.edit_text(text, reply_markup=markup)
                return
            except TelegramBadRequest as error:
                if "not modified" in str(error):
                    return
        await target.message.answer(text, reply_markup=markup)
        return
    await target.answer(text, reply_markup=markup)


async def show(target: Message | CallbackQuery, deps: Deps, state: FSMContext, screen: str | None = None,
               *, push: bool = True, edit: bool = True, user_id: int | None = None) -> None:
    """Draw a screen. Without `screen` - redraw the top of the back stack.

    `user_id` is required when `target` is a message sent by the bot itself (its author is the bot).
    """
    if screen is None:
        screen = (await _stack(state))[-1]
    elif screen == "home":
        await state.update_data(nav=["home"])
    elif push:
        await _push(state, screen)
    owner = user_id or target.from_user.id
    text, markup = ui.render_screen(screen, _ctx(deps, owner, await state.get_data()))
    await _paint(target, text, markup, edit=edit)


async def back(target: Message | CallbackQuery, deps: Deps, state: FSMContext) -> None:
    stack = await _stack(state)
    if len(stack) > 1:
        stack.pop()
    await state.update_data(nav=stack or ["home"])
    await show(target, deps, state, push=False)


# ================================================================== commands


@router.message(CommandStart())
@router.message(Command("menu"))
async def cmd_start(message: Message, deps: Deps, state: FSMContext, command: CommandObject, bot: Bot) -> None:
    ref_result = None
    payload = (command.args or "").strip()
    if payload.startswith("ref_"):
        raw = payload[4:]
        referrer_id = int(raw) if raw.lstrip("-").isdigit() else 0
        ref_result = deps.store.register_referral(message.from_user.id, referrer_id, billing.ref_welcome_days())
    deps.store.user(message.from_user.id)
    await state.set_state(None)
    await message.answer("👋 Сметчик на связи. Кнопка «🏠 Меню» внизу работает всегда.", reply_markup=ui.reply_keyboard())
    if ref_result:
        await message.answer(
            f"🎁 Вы пришли по приглашению — вам <b>+{ref_result['welcome_days']} дней Pro</b>, все документы открыты. "
            "Создайте первую смету — и пригласивший тоже получит бонус.")
    await show(message, deps, state, "home")


@router.message(Command("invite"))
async def cmd_invite(message: Message, deps: Deps, state: FSMContext) -> None:
    deps.store.user(message.from_user.id)
    await show(message, deps, state, "ref")


@router.message(Command("help"))
async def cmd_help(message: Message, deps: Deps, state: FSMContext) -> None:
    await show(message, deps, state, "help")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, deps: Deps, state: FSMContext) -> None:
    await state.set_state(None)
    await message.answer("Отменил.")
    await show(message, deps, state, "home")


@router.message(F.text.in_({ui.MENU_TEXT, "Меню", "меню"}))
async def menu_text(message: Message, deps: Deps, state: FSMContext) -> None:
    await state.set_state(None)
    await show(message, deps, state, "home")


@router.message(F.text == ui.ESTIMATE_TEXT)
async def estimate_text_button(message: Message, deps: Deps, state: FSMContext) -> None:
    await state.set_state(None)
    await show(message, deps, state, "est")


SCREEN_COMMANDS = {
    "smeta": "est", "obmer": "obm", "templates": "tpl", "audit": "aud", "nalog_menu": "tax", "company_info": "co",
    "refs": "refs", "sub": "sub", "list": "list:0", "stats": "stats", "docs": "docs", "progress": "prog",
}


@router.message(Command(*SCREEN_COMMANDS))
async def cmd_screen(message: Message, command: CommandObject, deps: Deps, state: FSMContext) -> None:
    await state.set_state(None)
    await show(message, deps, state, SCREEN_COMMANDS[command.command])


@router.message(Command("company"))
async def cmd_company(message: Message, deps: Deps, state: FSMContext) -> None:
    await state.update_data(nav=["home", "co"])
    await ask(message, state, "company")


@router.message(Command("new"))
async def cmd_new(message: Message, deps: Deps, state: FSMContext) -> None:
    await start_new(message, deps, state)


@router.message(Command("cut", "up"))
async def cmd_cut(message: Message, command: CommandObject, deps: Deps, state: FSMContext) -> None:
    found = current(deps, message.from_user.id)
    if not found:
        await show(message, deps, state, "est")
        return
    args = (command.args or "").split()
    if not args:
        await show(message, deps, state, "cut")
        return
    value = dec(args[0].replace("%", ""))
    scope = "all"
    if len(args) > 1:
        scope = {"работы": WORK, "работа": WORK, "материалы": MATERIAL, "материал": MATERIAL}.get(args[1].lower(), "all")
    estimate_id, estimate = found
    try:
        estimate.adjust(-value if command.command == "cut" else value, scope)
    except ValueError as error:
        await message.answer(f"⚠️ {error}")
        return
    save(deps, message.from_user.id, estimate_id, estimate)
    await show(message, deps, state, "est")


@router.message(Command("fit"))
async def cmd_fit(message: Message, command: CommandObject, deps: Deps, state: FSMContext) -> None:
    if not (command.args or "").strip():
        await ask(message, state, "fit")
        return
    await finish_value(message, deps, state, "fit", "", {"amount": command.args})


@router.message(Command("reset"))
async def cmd_reset(message: Message, deps: Deps, state: FSMContext) -> None:
    found = current(deps, message.from_user.id)
    if found:
        found[1].reset_adjustments()
        save(deps, message.from_user.id, *found)
    await show(message, deps, state, "est")


@router.message(Command("price", "qty", "del"))
async def cmd_position(message: Message, command: CommandObject, deps: Deps, state: FSMContext) -> None:
    args = (command.args or "").split()
    if not args or not args[0].isdigit() or (command.command != "del" and len(args) < 2):
        await message.answer("Формат: <code>/price 4 1500</code>, <code>/qty 4 85</code>, <code>/del 4</code>")
        return
    index = int(args[0])
    if command.command == "del":
        await act_delete(message, deps, state, index)
        return
    await finish_value(message, deps, state, command.command, str(index), {"value": args[1]})


@router.message(Command("vat"))
async def cmd_vat(message: Message, command: CommandObject, deps: Deps, state: FSMContext) -> None:
    value = dec((command.args or "").replace("%", "").strip())
    set_vat(deps, message.from_user.id, value)
    await show(message, deps, state, "est")


@router.message(Command("nr"))
async def cmd_nr(message: Message, command: CommandObject, deps: Deps, state: FSMContext) -> None:
    flag = (command.args or "").strip().lower() not in {"off", "нет", "0", "выкл"}
    set_nr(deps, message.from_user.id, flag)
    await message.answer("🏢 Накладные — часть себестоимости." if flag else "👷 Накладные в себестоимость не включаю.")


@router.message(Command("rates"))
async def cmd_rates(message: Message, command: CommandObject, deps: Deps, state: FSMContext) -> None:
    if not (command.args or "").strip():
        await ask(message, state, "rates_q")
        return
    catalog = deps.store.catalog(message.from_user.id, deps.catalog)
    await message.answer(render.rates_text(catalog.search(command.args.strip(), limit=5)))


@router.message(Command("index"))
async def cmd_index(message: Message, command: CommandObject, deps: Deps, state: FSMContext) -> None:
    argument = (command.args or "").strip()
    if not argument:
        await show(message, deps, state, "idx:0")
        return
    catalog = deps.store.catalog(message.from_user.id, deps.catalog)
    names = list(catalog.indices)
    if argument.isdigit():
        number = int(argument)
    else:
        matches = [i for i, name in enumerate(names, 1) if argument.lower() in name.lower()]
        if len(matches) > 1:
            await message.answer("Подходит несколько — уточните номером:\n" + "\n".join(
                f"{i}. {escape(names[i - 1])}" for i in matches[:10]))
            return
        number = matches[0] if matches else 0
    notice = choose_index(deps, message.from_user.id, number)
    await message.answer(notice)
    await show(message, deps, state, "est")


@router.message(Command("base"))
async def cmd_base(message: Message, command: CommandObject, deps: Deps, state: FSMContext) -> None:
    argument = (command.args or "").strip().lower()
    if argument in {"мои", "моя", "своя", "own"}:
        deps.store.update_settings(message.from_user.id, use_demo_rates=False)
    elif argument in {"оба", "все", "both", "демо", "demo"}:
        deps.store.update_settings(message.from_user.id, use_demo_rates=True)
    await show(message, deps, state, "refs")


@router.message(Command("import"))
async def cmd_import(message: Message, deps: Deps, state: FSMContext) -> None:
    await state.update_data(nav=["home", "refs"])
    await ask(message, state, "import")


@router.message(Command("import_clear"))
async def cmd_import_clear(message: Message, deps: Deps, state: FSMContext) -> None:
    removed = sum(deps.store.drop_imports(message.from_user.id, kind) for kind in ("rates", "offers", "indices"))
    await message.answer(f"🧹 Удалил загруженных файлов: {removed}.")


@router.message(Command("open"))
async def cmd_open(message: Message, command: CommandObject, deps: Deps, state: FSMContext) -> None:
    arg = (command.args or "").strip()
    if not arg.isdigit():
        await show(message, deps, state, "list:0")
        return
    await open_estimate(message, deps, state, int(arg))


@router.message(Command("xlsx", "excel", "pdf", "kp", "naryad"))
async def cmd_doc(message: Message, command: CommandObject, deps: Deps, state: FSMContext) -> None:
    kind = {"excel": "xlsx"}.get(command.command, command.command)
    await send_document(message, deps, kind)


@router.message(Command("profit"))
async def cmd_profit(message: Message, deps: Deps, state: FSMContext) -> None:
    await show(message, deps, state, "profit")


@router.message(Command("nalog", "налог", "tax"))
async def cmd_nalog(message: Message, command: CommandObject, deps: Deps, state: FSMContext) -> None:
    words = (command.args or "").lower().split()
    tg_id = message.from_user.id
    annual = next((dec(word) for word in words if word.replace(".", "").isdigit()), None)
    if annual is not None:
        deps.store.update_settings(tg_id, tax_annual=annual)
    if any(word in {"ип", "ip"} for word in words):
        deps.store.update_settings(tg_id, tax_ip=True)
    if any(word in {"ооо", "ooo"} for word in words):
        deps.store.update_settings(tg_id, tax_ip=False)
    if any(word in {"без", "один", "сам"} for word in words):
        deps.store.update_settings(tg_id, tax_staff=False)
    await show(message, deps, state, "tax")


@router.message(Command("nalog_rates", "ставки"))
async def cmd_nalog_rates(message: Message) -> None:
    await message.answer(f"<pre>{escape(tax.TaxRates.load().as_text())}</pre>")


@router.message(Command("grant"))
async def cmd_grant(message: Message, command: CommandObject, deps: Deps) -> None:
    if message.from_user.id not in billing.admins():
        return
    args = (command.args or "").split()
    if len(args) != 2 or not all(a.lstrip("-").isdigit() for a in args):
        await message.answer("Формат: <code>/grant TG_ID ДНЕЙ</code>")
        return
    until = deps.store.extend_subscription(int(args[0]), int(args[1]))
    await message.answer(f"👑 Подписка {args[0]} до {until.strftime('%d.%m.%Y')}")


# ================================================================== input wizards


async def ask(target: Message | CallbackQuery, state: FSMContext, kind: str, arg: str = "",
              step: int = 0, acc: dict | None = None) -> None:
    await state.set_state(Flow.input)
    await state.update_data(input={"kind": kind, "arg": arg, "step": step, "acc": acc or {}})
    text, markup = ui.wizard_prompt(kind, step)
    await _paint(target, text, markup)


@router.callback_query(F.data == "ib")
async def input_back(call: CallbackQuery, deps: Deps, state: FSMContext) -> None:
    data = await state.get_data()
    current_input = data.get("input") or {}
    step = int(current_input.get("step", 0))
    if await state.get_state() == Flow.input.state and step > 0:
        await ask(call, state, current_input["kind"], current_input.get("arg", ""), step - 1, current_input.get("acc"))
    else:
        await state.set_state(None)
        await show(call, deps, state, push=False)
    await call.answer()


@router.callback_query(F.data == "is")
async def input_skip(call: CallbackQuery, deps: Deps, state: FSMContext) -> None:
    await submit(call, deps, state, None, skip=True)
    await call.answer()


@router.callback_query(F.data.startswith("iv:"))
async def input_quick(call: CallbackQuery, deps: Deps, state: FSMContext) -> None:
    await submit(call, deps, state, call.data[3:])
    await call.answer()


@router.message(Flow.input, F.text, ~F.text.startswith("/"))
async def input_text(message: Message, deps: Deps, state: FSMContext) -> None:
    data = await state.get_data()
    if (data.get("input") or {}).get("kind") in ui.FILE_INPUTS:
        await message.answer("Жду файл — пришлите его документом. Или «⬅️ Назад».")
        return
    await submit(message, deps, state, message.text or "")


async def submit(target: Message | CallbackQuery, deps: Deps, state: FSMContext, raw: str | None, *, skip: bool = False) -> None:
    if await state.get_state() != Flow.input.state:
        return
    data = await state.get_data()
    current_input = data.get("input") or {}
    kind, arg = current_input.get("kind"), current_input.get("arg", "")
    if kind not in ui.WIZARDS:
        await state.set_state(None)
        return
    steps = ui.WIZARDS[kind]
    step_index = int(current_input.get("step", 0))
    step = steps[step_index]
    acc = dict(current_input.get("acc") or {})
    if skip:
        if not step.optional:
            return
        acc[step.key] = ""
    else:
        value = (raw or "").strip()
        if value in {"-", "—"} and step.optional:
            acc[step.key] = ""
        else:
            try:
                parsed = step.parse(value) if step.parse else value
            except ValueError as error:
                prompt, markup = ui.wizard_prompt(kind, step_index)
                await _paint(target, f"⚠️ {escape(str(error))}\n\n{prompt}", markup, edit=isinstance(target, CallbackQuery))
                return
            acc[step.key] = str(parsed)
    if step_index + 1 < len(steps):
        await ask(target, state, kind, arg, step_index + 1, acc)
        return
    await state.set_state(None)
    await state.update_data(input=None)
    await finish_value(target, deps, state, kind, arg, acc)


async def finish_value(target: Message | CallbackQuery, deps: Deps, state: FSMContext, kind: str, arg: str, acc: dict) -> None:
    """Apply a completed wizard. Errors go back to the user as a notice, never as a crash."""
    tg_id = target.from_user.id
    try:
        notice, screen = await apply_input(target, deps, state, kind, arg, acc)
    except ValueError as error:
        notice, screen = f"⚠️ {escape(str(error))}", None
    message = target.message if isinstance(target, CallbackQuery) else target
    if notice:
        await message.answer(notice)
    if screen == "":
        return
    where = message if notice else target
    if screen:
        await show(where, deps, state, screen, edit=not notice, user_id=tg_id)
    else:
        await show(where, deps, state, push=False, edit=not notice, user_id=tg_id)


async def apply_input(target, deps: Deps, state: FSMContext, kind: str, arg: str, acc: dict) -> tuple[str | None, str | None]:
    tg_id = target.from_user.id
    found = current(deps, tg_id)

    if kind == "company":
        signer = acc.get("signer", "")
        title, _, name = signer.partition(" ")
        company = Company(name=acc.get("name", ""), inn=acc.get("inn", ""), kpp=acc.get("kpp", ""),
                          address=acc.get("address", ""), phone=acc.get("phone", ""), email=acc.get("email", ""),
                          signer=name.strip() or signer, signer_title=title if name else "Директор")
        deps.store.save_company(tg_id, company)
        if found:
            found[1].company = company
            save(deps, tg_id, *found)
        return "✅ Шапка сохранена — она будет во всех документах.", None

    if kind == "new":
        allowed, reason = billing.can_create(deps.store, tg_id)
        if not allowed:
            return f"💳 {reason}. Оформите подписку, чтобы создавать сметы без ограничений.", "sub"
        estimate_id, estimate = new_estimate(deps, tg_id, object_name=acc.get("object_name", ""),
                                             customer=acc.get("customer", ""), contract=acc.get("contract", ""))
        hint = f" ({reason})" if reason else ""
        return (f"🧮 Смета {estimate.number} создана{hint}. Пишите работы текстом или выберите шаблон.", "est")

    if kind in {"tpl", "tpl_bath"}:
        if kind == "tpl_bath":
            values, notes = templates.bathroom_variables(acc["area"], acc["height"], acc.get("perimeter") or None)
        else:
            values, notes = templates.variables(acc["area"], acc["height"], rooms=acc.get("rooms") or 1,
                                                baths=acc.get("baths") or 0, perimeter=acc.get("perimeter") or None)
        await state.update_data(pending_tpl={"code": arg, "vars": {k: str(v) for k, v in values.items()}, "notes": notes})
        return None, "tplp"

    if kind == "coef_custom":
        if not found:
            return "Нет текущей сметы.", "est"
        touched = 0
        for position in found[1].positions:
            if position.kind == WORK:
                position.apply_coefficient(acc["name"], acc["k_ot"], acc["k_em"], acc.get("k_mat") or 1, "договорной")
                touched += 1
        save(deps, tg_id, *found)
        return f"⚙️ Коэффициент применён к {touched} работам.", None

    if kind == "lim_custom":
        if not found:
            return "Нет текущей сметы.", "est"
        found[1].limited.append({"name": acc["name"], "pct": acc["pct"], "basis": "договорной"})
        save(deps, tg_id, *found)
        return None, None

    if kind == "pay":
        if not found:
            return "Нет текущей сметы.", "est"
        progress.add_payment(found[1], acc["amount"], note=acc.get("note", ""))
        save(deps, tg_id, *found)
        return f"💵 Оплата {rub(dec(acc['amount']))} ₽ записана.", None

    if kind == "kp":
        if not found:
            return "Нет текущей сметы.", "est"
        found[1].kp.update({k: v for k, v in acc.items() if v})
        save(deps, tg_id, *found)
        return "✍️ Условия КП сохранены.", None

    if kind == "tax_manual":
        inputs = tax.Money(revenue=dec(acc["revenue"]), materials=dec(acc.get("materials") or 0),
                           payroll=dec(acc.get("payroll") or 0), employees=deps.store.settings(tg_id)["tax_staff"],
                           ip=deps.store.settings(tg_id)["tax_ip"], annual_revenue=deps.store.settings(tg_id)["tax_annual"])
        return f"<pre>{escape(tax.compare_text(inputs))}</pre>", None

    if kind == "works":
        if not found:
            allowed, reason = billing.can_create(deps.store, tg_id)
            if not allowed:
                return f"💳 {reason}.", "sub"
            found = new_estimate(deps, tg_id)
        estimate_id, estimate = found
        catalog = deps.store.catalog(tg_id, deps.catalog)
        matches = build_from_text(acc.get("text", ""), catalog, offers=deps.store.offers(tg_id, deps.offers))
        for match in matches:
            estimate.add(match.position)
        save(deps, tg_id, estimate_id, estimate)
        return render.matches_text(matches), "est"

    if kind == "fit":
        if not found:
            return "Нет текущей сметы.", "est"
        found[1].fit_to(dec(str(acc["amount"]).replace(" ", "")))
        save(deps, tg_id, *found)
        return None, None

    if kind in {"qty", "price", "crew", "done"}:
        if not found:
            return "Нет текущей сметы.", "est"
        estimate_id, estimate = found
        index = int(arg)
        if not 1 <= index <= len(estimate.positions):
            raise ValueError(f"нет позиции № {index}")
        position = estimate.positions[index - 1]
        value = acc.get("value", "")
        if kind == "qty":
            position.qty = dec(value)
        elif kind == "price":
            position.unit_price = dec(value)
            position.adj = dec(1)
            position.ot = position.em = position.zpm = position.mat = ZERO
            position.nr_pct = position.sp_pct = ZERO
            position.code = ""
        elif kind == "crew":
            position.crew_price = money(dec(value))
        else:
            progress.set_done(estimate, index, value)
        save(deps, tg_id, estimate_id, estimate)
        return None, None

    if kind == "contract":
        if not found:
            return "Нет текущей сметы.", "est"
        found[1].contract = acc["value"]
        save(deps, tg_id, *found)
        return None, None

    if kind == "crew_name":
        if not found:
            return "Нет текущей сметы.", "est"
        found[1].crew = acc["value"]
        save(deps, tg_id, *found)
        return None, None

    if kind == "room":
        room = obmer.parse_room(acc["value"], default_name=f"Помещение {len((await state.get_data()).get('rooms', [])) + 1}")
        rooms = list((await state.get_data()).get("rooms", [])) + [room.to_dict()]
        await state.update_data(rooms=rooms)
        return None, None

    if kind == "tax_annual":
        deps.store.update_settings(tg_id, tax_annual=dec(acc["value"]))
        return None, None

    if kind == "tax_target":
        if not found:
            return "Нет текущей сметы.", "tax"
        ctx = _ctx(deps, tg_id, await state.get_data())
        base = ui.tax_inputs(ctx, found[1])
        settings = deps.store.settings(tg_id)
        regimes = (tax.USN6, tax.USN15, tax.OSNO_IP, tax.NPD) if settings["tax_ip"] else (tax.USN6, tax.USN15, tax.OSNO_OOO)
        lines = [f"🎯 Чтобы получить на руки {rub(dec(acc['value']))} ₽ при текущих расходах", ""]
        for regime in regimes:
            vat_pct = found[1].vat_pct if regime in (tax.OSNO_OOO, tax.OSNO_IP) else ZERO
            revenue, result, _ = tax.price_for(acc["value"], regime, materials=base.materials, payroll=base.payroll,
                                               other_costs=base.other_costs, vat_pct=vat_pct,
                                               employees=base.employees, ip=base.ip,
                                               annual_revenue=base.annual_revenue)
            if result.blocked:
                lines.append(f"{result.title}: ❌ {result.blocked}")
            else:
                lines.append(f"{result.title}: ставить в смету {rub(revenue)} ₽"
                             + (f" (с НДС {vat_pct:g}%)" if vat_pct else ""))
        lines.append(f"\nСейчас смета на {rub(found[1].total())} ₽. Подогнать — «📉 Скидка / наценка» → «🎯».")
        return escape("\n".join(lines)), None

    if kind == "promo":
        ok, text = billing.redeem(deps.store, tg_id, acc["value"])
        return ("🎟 " if ok else "⚠️ ") + text, None

    if kind == "rates_q":
        catalog = deps.store.catalog(tg_id, deps.catalog)
        return render.rates_text(catalog.search(acc["value"], limit=6)), None

    if kind == "lost":
        if not found:
            return None, "est"
        funnel.set_status(found[1], "lost", acc.get("value", ""))
        save(deps, tg_id, *found)
        deps.store.set_reminder(tg_id, found[0], None)
        return "❌ Отметил как проигранную. Причины видны в «Воронке продаж».", "est"

    return None, None


# ================================================================== callbacks: navigation


@router.callback_query(F.data.startswith("go:"))
async def on_go(call: CallbackQuery, deps: Deps, state: FSMContext) -> None:
    await state.set_state(None)
    await show(call, deps, state, call.data[3:])
    await call.answer()


@router.callback_query(F.data == "bk")
async def on_back(call: CallbackQuery, deps: Deps, state: FSMContext) -> None:
    await state.set_state(None)
    await back(call, deps, state)
    await call.answer()


@router.callback_query(F.data == "hm")
async def on_home(call: CallbackQuery, deps: Deps, state: FSMContext) -> None:
    await state.set_state(None)
    await show(call, deps, state, "home")
    await call.answer()


# ================================================================== callbacks: actions


@router.callback_query(F.data.startswith("a:"))
async def on_action(call: CallbackQuery, deps: Deps, state: FSMContext, bot: Bot) -> None:
    parts = call.data.split(":")
    name, args = parts[1], parts[2:]
    tg_id = call.from_user.id
    try:
        notice, screen = await do_action(call, deps, state, bot, name, args)
    except ValueError as error:
        notice, screen = f"⚠️ {error}", None
    if screen == "":
        await call.answer()
        return
    if notice and len(notice) <= 190 and "\n" not in notice:
        await call.answer(notice, show_alert=notice.startswith("⚠️"))
    else:
        await call.answer()
        if notice:
            await call.message.answer(notice)
    await show(call, deps, state, screen, push=bool(screen), edit=not (notice and len(notice) > 190), user_id=tg_id)


async def do_action(call: CallbackQuery, deps: Deps, state: FSMContext, bot: Bot, name: str, args: list[str]) -> tuple[str | None, str | None]:
    tg_id = call.from_user.id
    found = current(deps, tg_id)

    if name == "new":
        await start_new(call, deps, state)
        return None, ""
    if name == "ask":
        kind, arg = args[0], ":".join(args[1:])
        if kind == "tpl" and arg == "bath":
            kind = "tpl_bath"
        if kind == "works" and not found:
            allowed, reason = billing.can_create(deps.store, tg_id)
            if not allowed:
                return f"💳 {reason}", "sub"
        await ask(call, state, kind, arg)
        return None, ""
    if name == "open":
        await open_estimate(call, deps, state, int(args[0]))
        return None, ""
    if name == "rs":                                        # ответ на напоминание
        return reminder_answer(deps, tg_id, int(args[0]), args[1])
    if name == "buy":
        item = billing.plan(args[0])
        if not item:
            return "⚠️ Тариф не найден", None
        await bot.send_invoice(chat_id=tg_id, **billing.invoice(item))
        return None, ""
    if name == "tax_ip":
        deps.store.update_settings(tg_id, tax_ip=not deps.store.settings(tg_id)["tax_ip"])
        return None, None
    if name == "tax_staff":
        deps.store.update_settings(tg_id, tax_staff=not deps.store.settings(tg_id)["tax_staff"])
        return None, None
    if name == "tax_rates":
        await call.message.answer(f"<pre>{escape(tax.TaxRates.load().as_text())}</pre>")
        return None, None
    if name == "vat":
        set_vat(deps, tg_id, ZERO if deps.store.settings(tg_id)["vat_pct"] else tax.current_vat())
        return None, None
    if name == "nr":
        set_nr(deps, tg_id, not deps.store.settings(tg_id)["floor_with_nr"])
        return None, None
    if name == "base":
        deps.store.update_settings(tg_id, use_demo_rates=not deps.store.settings(tg_id)["use_demo_rates"])
        return None, None
    if name == "import_clear":
        removed = sum(deps.store.drop_imports(tg_id, kind) for kind in ("rates", "offers", "indices"))
        return f"🧹 Удалено файлов: {removed}", None
    if name == "idx":
        return choose_index(deps, tg_id, int(args[0])), None
    if name == "obm_pop":
        rooms = list((await state.get_data()).get("rooms", []))[:-1]
        await state.update_data(rooms=rooms)
        return None, None
    if name == "obm_clear":
        await state.update_data(rooms=[], obm_works=[])
        return None, None
    if name == "obmt":
        chosen = set((await state.get_data()).get("obm_works", []))
        chosen ^= {args[0]}
        await state.update_data(obm_works=sorted(chosen))
        return None, None
    if name == "obm_add":
        return await obmer_to_estimate(call, deps, state)
    if name == "tplobm":
        rooms = [obmer.Room(**room) for room in (await state.get_data()).get("rooms", [])]
        values = obmer.summary(rooms)
        values["N"] = dec(1 if args[0] != "bath" else 0)
        await state.update_data(pending_tpl={"code": args[0], "vars": {k: str(v) for k, v in values.items()},
                                             "notes": ["размеры взяты из обмера"]})
        return None, "tplp"
    if name in {"tpl_add", "tpl_new"}:
        return await template_to_estimate(call, deps, state, new=name == "tpl_new")

    # --- everything below works on the current estimate
    if not found:
        return "⚠️ Нет текущей сметы", "est"
    estimate_id, estimate = found

    if name in {"cut", "cutw", "cutm"}:
        scope = {"cut": "all", "cutw": WORK, "cutm": MATERIAL}[name]
        estimate.adjust(dec(args[0]), scope)
        save(deps, tg_id, estimate_id, estimate)
        return f"Итого: {rub(estimate.total())} ₽", None
    if name == "reset":
        estimate.reset_adjustments()
        save(deps, tg_id, estimate_id, estimate)
        return "♻️ Корректировки сброшены", None
    if name == "del":
        removed = estimate.remove(int(args[0]))
        save(deps, tg_id, estimate_id, estimate)
        await state.update_data(nav=[s for s in await _stack(state) if not s.startswith("pos:")])
        return (f"🗑 Удалено: {removed.name[:60]}" if removed else "⚠️ Позиция не найдена"), "items:0"
    if name == "coef":
        row = next((r for r in datafiles.coefficients() if r["code"] == args[0]), None)
        if not row:
            return "⚠️ Коэффициент не найден", None
        touched = 0
        for position in estimate.positions:
            if position.kind == WORK:
                position.apply_coefficient(row["name"], row["k_ot"], row["k_em"], row["k_mat"], row["basis"])
                touched += 1
        save(deps, tg_id, estimate_id, estimate)
        return f"⚙️ Применено к {touched} работам", None
    if name == "pcoef":
        row = next((r for r in datafiles.coefficients() if r["code"] == args[1]), None)
        position = estimate.positions[int(args[0]) - 1]
        position.apply_coefficient(row["name"], row["k_ot"], row["k_em"], row["k_mat"], row["basis"])
        save(deps, tg_id, estimate_id, estimate)
        return "⚙️ Применено к позиции", None
    if name == "pcoef_clear":
        estimate.positions[int(args[0]) - 1].clear_coefficients()
        save(deps, tg_id, estimate_id, estimate)
        return "🧹 Коэффициенты позиции сняты", None
    if name == "coef_clear":
        for position in estimate.positions:
            position.clear_coefficients()
        save(deps, tg_id, estimate_id, estimate)
        return "🧹 Все коэффициенты сняты", None
    if name == "lim":
        row = next((r for r in datafiles.limited_presets() if r["code"] == args[0]), None)
        if row:
            names = [item["name"] for item in estimate.limited]
            if row["name"] in names:
                estimate.limited = [item for item in estimate.limited if item["name"] != row["name"]]
            else:
                estimate.limited.append({"name": row["name"], "pct": row["pct"], "basis": row.get("basis", "")})
            save(deps, tg_id, estimate_id, estimate)
        return None, None
    if name == "lim_clear":
        estimate.limited = []
        save(deps, tg_id, estimate_id, estimate)
        return None, None
    if name == "mat":
        added = consumption.apply(estimate, deps.store.offers(tg_id, deps.offers))
        save(deps, tg_id, estimate_id, estimate)
        return f"🧱 Материалов в смете: {len(added)}", "est"
    if name == "mat_rm":
        estimate.positions = [p for p in estimate.positions if p.source != consumption.SOURCE]
        save(deps, tg_id, estimate_id, estimate)
        return "🗑 Материалы по нормам убраны", "est"
    if name == "doc":
        await send_document(call.message, deps, args[0], tg_id=tg_id)
        return None, None
    if name == "act":
        act = progress.make_act(estimate)
        save(deps, tg_id, estimate_id, estimate)
        await send_act(call.message, deps, estimate, act)
        return f"📝 Акт № {act['number']} на {rub(dec(act['total']))} ₽", None
    if name == "actget":
        act = next((a for a in estimate.acts if a["number"] == int(args[0])), None)
        if act:
            await send_act(call.message, deps, estimate, act)
        return None, None
    if name == "done_all":
        for index in range(1, len(estimate.positions) + 1):
            progress.set_done(estimate, index, "всё")
        save(deps, tg_id, estimate_id, estimate)
        return "✅ Всё отмечено выполненным", "prog"
    if name == "sched":
        progress.set_schedule(estimate, args[0] if len(args) == 1 else "/".join(args))
        save(deps, tg_id, estimate_id, estimate)
        return "🗓 График задан", "prog"
    if name == "sched_clear":
        estimate.schedule = []
        save(deps, tg_id, estimate_id, estimate)
        return None, None
    if name == "status":
        code = args[0]
        if code == "lost":
            await ask(call, state, "lost")
            return None, ""
        funnel.set_status(estimate, code)
        save(deps, tg_id, estimate_id, estimate)
        if code == "sent":
            deps.store.set_reminder(tg_id, estimate_id, funnel.remind_at())
            deps.store.save_version(tg_id, estimate_id, estimate, "отправлено заказчику")
            return f"📤 Отправлено. Напомню через {funnel.REMIND_DAYS} дня, если не будет ответа", "est"
        deps.store.set_reminder(tg_id, estimate_id, None)
        return funnel.TITLES[code], "est"
    if name == "ver_save":
        number = deps.store.save_version(tg_id, estimate_id, estimate)
        return f"💾 Сохранена версия v{number}", None
    if name == "restore":
        old = deps.store.load_version(tg_id, estimate_id, int(args[0]))
        if old is None:
            return "⚠️ Версия не найдена", None
        deps.store.save_version(tg_id, estimate_id, estimate, "до восстановления")
        save(deps, tg_id, estimate_id, old)
        return f"↩️ Восстановлена v{args[0]} (прежняя сохранена отдельной версией)", "est"
    if name == "ds":
        old = deps.store.load_version(tg_id, estimate_id, int(args[0]))
        if old is None:
            return "⚠️ Версия не найдена", None
        change = diff(old, estimate)
        path = deps.export_dir / safe_name(f"ДС_{estimate.number}_v{args[0]}.xlsx")
        docs.ds_xlsx(estimate, change, len(deps.store.versions(tg_id, estimate_id)), path)
        await send_file(call.message, path, f"📎 Допсоглашение: {'+' if change.delta >= 0 else '−'}{rub(abs(change.delta))} ₽")
        return None, None
    if name == "rep":
        pending = {"offers": True} if args[0] == "offers" else {"index": int(args[0])}
        await state.update_data(pending_rep=pending)
        return None, "reppv"
    if name in {"rep_apply", "rep_files"}:
        pending = (await state.get_data()).get("pending_rep")
        if not pending:
            return "⚠️ Сначала выберите, по чему пересчитать", "rep"
        ctx = _ctx(deps, tg_id, await state.get_data())
        result = reprice(estimate, **ui.reprice_args(ctx, pending))
        if name == "rep_files":
            path = deps.export_dir / safe_name(f"Пересчёт_{estimate.number}.xlsx")
            docs.reprice_xlsx(result, path)
            await send_file(call.message, path, "🔁 Сравнение было/стало")
            await call.message.answer(f"✉️ Письмо заказчику — скопируйте:\n\n<code>{escape(result.letter(estimate))}</code>")
            return None, None
        deps.store.save_version(tg_id, estimate_id, estimate, "до пересчёта")
        save(deps, tg_id, estimate_id, result.estimate)
        await state.update_data(pending_rep=None)
        return f"✅ Пересчитано: {rub(result.new_total)} ₽", "est"
    if name == "crewpct":
        share = pct(args[0])
        for position in estimate.positions:
            if position.kind == WORK:
                position.crew_price = money(position.unit_price_now(estimate.indices) * share)
        save(deps, tg_id, estimate_id, estimate)
        return f"👷 Ставка бригады — {args[0]}% от цены работ", None
    if name == "crew_clear":
        for position in estimate.positions:
            position.crew_price = None
        save(deps, tg_id, estimate_id, estimate)
        return None, None
    return None, None


# ================================================================== flows used by several handlers


async def start_new(target: Message | CallbackQuery, deps: Deps, state: FSMContext) -> None:
    allowed, reason = billing.can_create(deps.store, target.from_user.id)
    if not allowed:
        await _paint(target, f"💳 {escape(reason)}. Оформите подписку — сметы без ограничений.",
                     ui.render_screen("sub", _ctx(deps, target.from_user.id, await state.get_data()))[1])
        await _push(state, "sub")
        return
    await ask(target, state, "new")


async def open_estimate(target, deps: Deps, state: FSMContext, estimate_id: int) -> None:
    if deps.store.load_estimate(target.from_user.id, estimate_id) is None:
        await _paint(target, "Такой сметы нет.", ui.kb([]))
        return
    deps.store.update_settings(target.from_user.id, current_id=estimate_id)
    await show(target, deps, state, "est")


async def act_delete(message: Message, deps: Deps, state: FSMContext, index: int) -> None:
    found = current(deps, message.from_user.id)
    if not found:
        await show(message, deps, state, "est")
        return
    removed = found[1].remove(index)
    if not removed:
        await message.answer(f"Нет позиции № {index}.")
        return
    save(deps, message.from_user.id, *found)
    await message.answer(f"🗑 Удалил: {escape(removed.name)}")
    await show(message, deps, state, "est")


def set_vat(deps: Deps, tg_id: int, value: Decimal) -> None:
    deps.store.update_settings(tg_id, vat_pct=value)
    found = current(deps, tg_id)
    if found:
        found[1].vat_pct = value
        save(deps, tg_id, *found)


def set_nr(deps: Deps, tg_id: int, flag: bool) -> None:
    deps.store.update_settings(tg_id, floor_with_nr=flag)
    found = current(deps, tg_id)
    if found:
        found[1].floor_with_nr = flag
        save(deps, tg_id, *found)


def choose_index(deps: Deps, tg_id: int, number: int) -> str:
    catalog = deps.store.catalog(tg_id, deps.catalog)
    names = list(catalog.indices)
    if not 1 <= number <= len(names):
        return "⚠️ Не нашёл такой индекс"
    chosen = names[number - 1]
    deps.store.update_settings(tg_id, index_name=chosen)
    found = current(deps, tg_id)
    if found:
        found[1].indices = catalog.indices[chosen]
        save(deps, tg_id, *found)
    return f"📈 Индекс «{chosen[:60]}» применён"


async def obmer_to_estimate(call: CallbackQuery, deps: Deps, state: FSMContext) -> tuple[str | None, str | None]:
    data = await state.get_data()
    rooms = [obmer.Room(**room) for room in data.get("rooms", [])]
    chosen = set(data.get("obm_works", []))
    if not rooms or not chosen:
        return "⚠️ Отметьте хотя бы одну работу", None
    values = obmer.summary(rooms)
    drafts = [DraftLine(raw=query, name=query, qty=values[var], unit=unit)
              for key, _, query, unit, var in obmer.WORKS if key in chosen and values[var] > ZERO]
    tg_id = call.from_user.id
    found = current(deps, tg_id)
    if not found:
        allowed, reason = billing.can_create(deps.store, tg_id)
        if not allowed:
            return f"💳 {reason}", "sub"
        found = new_estimate(deps, tg_id)
    estimate_id, estimate = found
    matches = build(drafts, deps.store.catalog(tg_id, deps.catalog), offers=deps.store.offers(tg_id, deps.offers),
                    section="По обмеру")
    for match in matches:
        estimate.add(match.position)
    save(deps, tg_id, estimate_id, estimate)
    await state.update_data(obm_works=[])
    return f"➕ Добавлено работ: {len(matches)}", "est"


async def template_to_estimate(call: CallbackQuery, deps: Deps, state: FSMContext, *, new: bool) -> tuple[str | None, str | None]:
    pending = (await state.get_data()).get("pending_tpl")
    if not pending:
        return "⚠️ Шаблон не рассчитан", "tpl"
    tg_id = call.from_user.id
    found = None if new else current(deps, tg_id)
    if found is None:
        allowed, reason = billing.can_create(deps.store, tg_id)
        if not allowed:
            return f"💳 {reason}", "sub"
        found = new_estimate(deps, tg_id)
    estimate_id, estimate = found
    values = {k: dec(v) for k, v in pending["vars"].items()}
    matches = templates.build_template(pending["code"], values, deps.store.catalog(tg_id, deps.catalog),
                                       deps.store.offers(tg_id, deps.offers))
    for match in matches:
        estimate.add(match.position)
    save(deps, tg_id, estimate_id, estimate)
    await state.update_data(pending_tpl=None, nav=["home", "est"])
    return f"🏗 Добавлено позиций: {len(matches)}", "est"


def reminder_answer(deps: Deps, tg_id: int, estimate_id: int, answer: str) -> tuple[str, str | None]:
    estimate = deps.store.load_estimate(tg_id, estimate_id)
    if estimate is None:
        return "⚠️ Смета не найдена", None
    if answer == "snooze":
        deps.store.set_reminder(tg_id, estimate_id, funnel.remind_at())
        return f"⏰ Напомню ещё через {funnel.REMIND_DAYS} дня", None
    funnel.set_status(estimate, answer)
    deps.store.save_estimate(tg_id, estimate, estimate_id)
    deps.store.set_reminder(tg_id, estimate_id, None)
    return funnel.TITLES.get(answer, answer), None


# ================================================================== files


async def send_file(message: Message, path: Path, caption: str = "") -> None:
    await message.answer_document(FSInputFile(path), caption=caption[:1000])
    path.unlink(missing_ok=True)


async def send_document(message: Message, deps: Deps, kind: str, *, tg_id: int | None = None) -> None:
    tg_id = tg_id or message.from_user.id
    found = current(deps, tg_id)
    if not found or not found[1].positions:
        await message.answer("В смете нет позиций.")
        return
    allowed, reason = billing.can_export(deps.store, tg_id)
    if not allowed:
        await message.answer(reason, reply_markup=Markup(inline_keyboard=[
            [Button(text="💳 Открыть подписку", callback_data="go:sub")]]))
        return
    _, estimate = found
    deps.export_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_name(f"{estimate.number or estimate.date.isoformat()}")
    caption = f"Итого по смете: {rub(estimate.total())} ₽"
    warnings = estimate.warnings()
    if kind == "xlsx":
        path = estimate_to_xlsx(estimate, deps.export_dir / f"Смета_{stem}.xlsx")
    elif kind == "pdf":
        path = estimate_to_pdf(estimate, deps.export_dir / f"Смета_{stem}.pdf")
    elif kind == "kp":
        logo = None
        for suffix in (".png", ".jpg"):
            candidate = deps.logo_dir / f"{tg_id}{suffix}"
            if candidate.exists():
                logo = candidate
        path = docs.kp_pdf(estimate, deps.export_dir / f"КП_{stem}.pdf", logo)
        caption = f"💼 Коммерческое предложение на {rub(estimate.total())} ₽"
        warnings = []
    elif kind == "naryad":
        rows, total, missing = docs.crew_rows(estimate)
        path = docs.naryad_xlsx(estimate, deps.export_dir / f"Наряд_{stem}.xlsx")
        caption = f"👷 К выплате бригаде: {rub(total)} ₽" + (f" · без ставки {missing} поз." if missing else "")
        warnings = []
    elif kind == "margin":
        report = build_report(estimate, deps.store.offers(tg_id, deps.offers))
        path = margin_to_xlsx(report, deps.export_dir / f"Профит_{stem}.xlsx", estimate)
        caption = "🔒 Только для вас — заказчику не отправлять."
        warnings = []
    else:
        await message.answer("Неизвестный документ.")
        return
    if warnings:
        caption += f"\n⚠️ {warnings[0]}"
    await send_file(message, path, caption)


async def send_act(message: Message, deps: Deps, estimate: Estimate, act: dict) -> None:
    allowed, reason = billing.can_export(deps.store, message.from_user.id)
    if not allowed:
        await message.answer(reason, reply_markup=Markup(inline_keyboard=[
            [Button(text="💳 Открыть подписку", callback_data="go:sub")]]))
        return
    deps.export_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_name(f"{estimate.number}_акт{act['number']}")
    await send_file(message, docs.ks2_xlsx(estimate, act, deps.export_dir / f"КС-2_{stem}.xlsx"),
                    f"📝 КС-2 № {act['number']} — {rub(dec(act['total']))} ₽")
    await send_file(message, docs.ks3_xlsx(estimate, act, deps.export_dir / f"КС-3_{stem}.xlsx"),
                    f"📝 КС-3 № {act['number']}")


@router.message(F.photo)
async def got_photo(message: Message, deps: Deps, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    if await state.get_state() == Flow.input.state and (data.get("input") or {}).get("kind") == "logo":
        deps.logo_dir.mkdir(parents=True, exist_ok=True)
        for old in deps.logo_dir.glob(f"{message.from_user.id}.*"):
            old.unlink()
        await bot.download(message.photo[-1], destination=deps.logo_dir / f"{message.from_user.id}.jpg")
        await state.set_state(None)
        await message.answer("🖼 Логотип сохранён — он будет в коммерческих предложениях.")
        await show(message, deps, state, push=False, edit=False)
        return
    await message.answer("Фото пока понимаю только как логотип: «🏢 Компания» → «🖼 Логотип для КП».")


@router.message(F.document)
async def got_document(message: Message, deps: Deps, state: FSMContext, bot: Bot) -> None:
    document = message.document
    name = document.file_name or "file"
    data = await state.get_data()
    waiting = (data.get("input") or {}).get("kind") if await state.get_state() == Flow.input.state else None
    if (document.file_size or 0) > 20 * 1024 * 1024:
        if message.from_user.id in billing.admins():
            await message.answer(
                "Телеграм отдаёт ботам файлы до 20 МБ, а этот больше. Полную ФСНБ загрузите на сервере:\n"
                "<code>python3 -m smeta.fgis load /путь/ФСНБ-2022.zip --kind rates</code>")
        else:
            await message.answer("Файл больше 20 МБ — Телеграм не передаёт такие боту. "
                                 "Пришлите файл поменьше или разбейте его на части.")
        return
    buffer = BytesIO()
    await bot.download(document, destination=buffer)
    raw = buffer.getvalue()
    tg_id = message.from_user.id

    if waiting == "logo":
        if not name.lower().endswith((".png", ".jpg", ".jpeg")):
            await message.answer("Нужна картинка PNG или JPG.")
            return
        deps.logo_dir.mkdir(parents=True, exist_ok=True)
        for old in deps.logo_dir.glob(f"{tg_id}.*"):
            old.unlink()
        (deps.logo_dir / f"{tg_id}{'.png' if name.lower().endswith('.png') else '.jpg'}").write_bytes(raw)
        await state.set_state(None)
        await message.answer("🖼 Логотип сохранён.")
        await show(message, deps, state, push=False, edit=False)
        return

    if waiting == "audit":
        catalog = deps.store.catalog(tg_id, deps.catalog)
        settings = deps.store.settings(tg_id)
        try:
            report = audit(raw, name, catalog, catalog.index(settings["index_name"] or None))
        except ValueError as error:
            await message.answer(f"⚠️ {escape(str(error))}")
            return
        await state.set_state(None)
        text = escape(report.as_text())
        for start in range(0, len(text), 3800):
            await message.answer(text[start:start + 3800])
        deps.export_dir.mkdir(parents=True, exist_ok=True)
        await send_file(message, report_xlsx(report, deps.export_dir / safe_name(f"Проверка_{name}.xlsx")),
                        "🔍 Отчёт: строки с замечаниями подсвечены")
        await show(message, deps, state, push=False, edit=False)
        return

    if not name.lower().endswith((".csv", ".txt", ".xlsx", ".xlsm", ".xml", ".dbf", ".zip")):
        await message.answer("Поддерживаю CSV, XLSX, XML, DBF и ZIP с ними.")
        return
    await message.answer("⏳ Читаю файл…")
    kind, body, report = run_import(raw, name)
    if not body:
        await message.answer(f"<pre>{escape(report)}</pre>")
        return
    first_rates = kind == "rates" and not deps.store.imports(tg_id, "rates")
    deps.store.add_import(tg_id, kind, name, body, max(len(body.strip().splitlines()) - 1, 0))
    await message.answer(f"<pre>{escape(report)}</pre>")
    if kind == "rates" and first_rates and deps.store.settings(tg_id)["use_demo_rates"]:
        deps.store.update_settings(tg_id, use_demo_rates=False)
        await message.answer("Считаю теперь только по вашей базе — демо-расценки отключил, чтобы они не попали "
                             "в смету. Вернуть: «📚 Справочники» → «🗂 Демо вкл/выкл».")
    elif kind == "indices":
        await message.answer("📈 Индексы загружены — выберите нужный в «📚 Справочники» → «📈 Индекс».")
    elif kind == "offers":
        await message.answer("🏪 Прайс загружен — материалы считаются по нему.")
    if waiting == "import":
        await state.set_state(None)
    await show(message, deps, state, "refs", edit=False)


def run_import(raw: bytes, name: str) -> tuple[str, str, str]:
    """Decide what the file is, convert it to canonical CSV and report what happened."""
    head = raw[:4096].decode("utf-8", "replace").lower()
    if any(word in head for word in ("скидка", "discount", "поставщик", "supplier", "розница", "retail")):
        book = OfferBook.from_csv(raw.decode("utf-8-sig", "replace"))
        if book.offers:
            return "offers", raw.decode("utf-8-sig", "replace"), f"Загрузил {len(book.offers)} строк прайса из «{name}»."
    looks_like_indices = any(word in name.lower() for word in ("индекс", "index", "ксмр"))
    if not looks_like_indices:
        rates, report = importer.import_rates(raw, name)
        if rates:
            return "rates", importer.rates_to_csv(rates), report.as_text()
    indices, index_report = importer.import_indices(raw, name)
    if indices:
        return "indices", importer.indices_to_csv(indices), index_report.as_text()
    if looks_like_indices:
        rates, report = importer.import_rates(raw, name)
        if rates:
            return "rates", importer.rates_to_csv(rates), report.as_text()
    return "", "", (
        "Не понял файл. Нужен один из вариантов:\n"
        "• расценки: «Шифр», «Наименование», «Ед. изм.», «Оплата труда», «Эксплуатация машин», «Материалы»;\n"
        "• индексы: «Субъект РФ», «ИОТ», «ИЭМ», «ИМАТ» или «Индекс СМР»;\n"
        "• прайс поставщика: столбцы material;unit;price;discount;retail;supplier "
        "(материал; ед.; цена; скидка; розница; поставщик).\n" + index_report.as_text())


# ================================================================== payments


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    payload = query.invoice_payload or ""
    ok = payload.startswith("sub:") and billing.plan(payload.split(":", 1)[1]) is not None
    await query.answer(ok=ok, error_message=None if ok else "Тариф не найден, попробуйте ещё раз из меню.")


@router.message(F.successful_payment)
async def paid(message: Message, deps: Deps, state: FSMContext) -> None:
    payment = message.successful_payment
    until = billing.activate(deps.store, message.from_user.id, payment.invoice_payload, payment.total_amount,
                             payment.currency, payment.telegram_payment_charge_id)
    when = until.strftime("%d.%m.%Y") if until else "—"
    await message.answer(f"✅ Оплата получена. Подписка активна до {when}. Спасибо!")
    await show(message, deps, state, "home")


# ================================================================== free text = new works


@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
async def add_positions(message: Message, deps: Deps, state: FSMContext) -> None:
    await finish_value(message, deps, state, "works", "", {"text": message.text or ""})


# ================================================================== reminders


async def run_reminders(bot: Bot, deps: Deps, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    sent = 0
    for row in deps.store.due_reminders(now):
        markup = Markup(inline_keyboard=[
            [Button(text="🤝 Согласовано", callback_data=f"a:rs:{row['id']}:agreed"),
             Button(text="❌ Проиграно", callback_data=f"a:rs:{row['id']}:lost")],
            [Button(text=f"⏰ Ещё {funnel.REMIND_DAYS} дня", callback_data=f"a:rs:{row['id']}:snooze")],
        ])
        try:
            await bot.send_message(row["tg_id"], f"⏰ Смета {escape(row['number'])} на {rub(dec(row['total']))} ₽ "
                                                 f"отправлена {funnel.REMIND_DAYS} дня назад — ответа нет. "
                                                 "Напомните заказчику или отметьте результат.", reply_markup=markup)
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            pass
        deps.store.set_reminder(row["tg_id"], row["id"], None)
    for row in deps.store.expiring_subscriptions(now):
        try:
            until = datetime.fromisoformat(row["paid_until"]).strftime("%d.%m.%Y")
            await bot.send_message(row["tg_id"], f"💳 Подписка заканчивается {until}.", reply_markup=Markup(
                inline_keyboard=[[Button(text="💳 Продлить", callback_data="go:sub")]]))
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            pass
        deps.store.update_settings(row["tg_id"], sub_reminded=row["paid_until"])
    for row in deps.store.pop_ref_rewards():
        try:
            await bot.send_message(
                row["referrer_id"],
                f"🎁 По вашей ссылке пришёл активный пользователь — вам <b>+{row['days']} дней Pro</b>! "
                "Спасибо, что делитесь.",
                reply_markup=Markup(inline_keyboard=[[Button(text="🎁 Пригласить ещё", callback_data="go:ref")]]))
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            pass
    return sent


async def reminder_loop(bot: Bot, deps: Deps, interval: int = 600) -> None:
    while True:
        try:
            await run_reminders(bot, deps)
        except Exception:                                   # noqa: BLE001 - loop must survive anything
            log.exception("reminders failed")
        await asyncio.sleep(interval)


# ================================================================== entry point


def build_deps() -> Deps:
    data = Path(os.getenv("SMETA_DATA_DIR", "data"))
    return Deps(
        store=Store(os.getenv("SMETA_DB_PATH", str(data / "smeta.db"))),
        catalog=Catalog.load(),
        offers=OfferBook.load(os.getenv("SMETA_OFFERS", str(data / "suppliers" / "demo.csv"))),
        export_dir=Path(os.getenv("SMETA_EXPORT_DIR", str(data / "export"))),
        logo_dir=data / "logos",
    )


COMMANDS = [
    ("menu", "🏠 Главное меню"), ("new", "🧮 Новая смета"), ("smeta", "📋 Текущая смета"),
    ("list", "📂 Мои сметы"), ("obmer", "📐 Обмер"), ("templates", "🏗 Смета по шаблону"),
    ("audit", "🔍 Проверить чужую смету"), ("nalog", "🧾 Налоги"), ("docs", "📄 Документы"),
    ("company", "🏢 Реквизиты компании"), ("sub", "💳 Подписка"),
    ("invite", "🎁 Пригласить друга"), ("help", "❓ Помощь"),
]


async def run() -> None:
    token = os.getenv("SMETA_BOT_TOKEN") or os.getenv("BOT_TOKEN") or ""
    if not token:
        raise SystemExit("Нет токена: впишите SMETA_BOT_TOKEN=... в файл .env (токен выдаёт @BotFather)")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    deps = build_deps()
    session = None
    proxy = os.getenv("TELEGRAM_PROXY", "").strip()
    if proxy:
        from aiogram.client.session.aiohttp import AiohttpSession

        session = AiohttpSession(proxy=proxy)
    bot = Bot(token, session=session, default=DefaultBotProperties(parse_mode="HTML"))
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(router)
    await bot.set_my_commands([BotCommand(command=c, description=d) for c, d in COMMANDS])
    try:
        deps.bot_username = (await bot.get_me()).username or ""
    except Exception:                                    # noqa: BLE001 — ссылки просто будут недоступны
        log.warning("не удалось получить имя бота для реферальных ссылок")
    runner = await webapp.start(deps, bot, token)
    url = webapp.webapp_url()
    if url:
        await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="📱 Сметчик", web_app=WebAppInfo(url=url)))
    elif os.getenv("SMETA_WEBAPP_URL"):
        log.warning("SMETA_WEBAPP_URL должен начинаться с https:// — Телеграм не откроет мини-апп по http")
    task = asyncio.create_task(reminder_loop(bot, deps))
    log.info("Сметчик запущен: расценок %s, прайс %s", len(deps.catalog.rates), len(deps.offers.offers))
    try:
        await dispatcher.start_polling(bot, deps=deps)
    finally:
        task.cancel()
        if runner is not None:
            await runner.cleanup()
        deps.store.close()
        await bot.session.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
