"""Telegram interface: onboarding, shop connection, approve/edit/skip cards, settings, admin stats."""
from __future__ import annotations

import asyncio
import html
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Kb, Message

from ..ai import DraftError
from ..config import Settings
from ..crypto import Vault
from ..db import DB, Account, Item
from ..marketplaces import TITLES, AuthError, MarketplaceError, make_client, parse_credentials
from ..service import Engine, QuotaError
from .texts import SELLER_LANGS, t

log = logging.getLogger(__name__)
router = Router()
_background: set[asyncio.Task] = set()  # keep references so tasks are not garbage-collected
NOT_COMMAND = ~F.text.startswith("/")


class Connect(StatesGroup):
    creds = State()


class Edit(StatesGroup):
    text = State()


class Signature(StatesGroup):
    text = State()


def esc(s: object) -> str:
    return html.escape(str(s))


def cut(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def stars(n: int | None) -> str:
    return "★" * n + "☆" * (5 - n) if n else ""


# ---------------------------------------------------------------- item card
def render_card(item: Item, acc: Account, lang: str) -> tuple[str, Kb | None]:
    same = item.buyer_lang == lang
    head = f"<b>{TITLES[acc.marketplace]} · {t(lang, item.kind)}</b> {stars(item.rating)}"
    lines = [head]
    if item.product or item.sku:
        lines.append("📦 " + esc(item.product or f"SKU {item.sku}") + (f" · {esc(item.sku)}" if item.product and item.sku else ""))
    lines.append(f"\n💬 <b>{t(lang, 'original')}:</b>\n<i>{esc(cut(item.text, 1200)) if item.text else t(lang, 'no_text')}</i>")
    if item.translation and not same:
        lines.append(f"🌐 <b>{t(lang, 'translation')}:</b>\n{esc(cut(item.translation, 1200))}")
    lines.append(f"\n✍️ <b>{t(lang, 'draft', bl=esc(item.buyer_lang))}:</b>\n{esc(item.draft)}")
    if item.draft_translation and not same:
        lines.append(f"🌐 <b>{t(lang, 'draft_tr')}:</b>\n<i>{esc(item.draft_translation)}</i>")
    if item.status in ("sent", "auto_sent", "skipped"):
        lines.append("\n" + t(lang, "st_" + item.status))
        return "\n".join(lines), None
    if item.needs_input:
        lines.append("\n" + t(lang, "needs_input"))
    if item.error:
        lines.append(f"\n❗ {esc(cut(item.error, 300))}")
    kb = Kb(inline_keyboard=[
        [Btn(text=t(lang, "btn_send"), callback_data=f"it:send:{item.id}"),
         Btn(text=t(lang, "btn_edit"), callback_data=f"it:edit:{item.id}")],
        [Btn(text=t(lang, "btn_regen"), callback_data=f"it:regen:{item.id}"),
         Btn(text=t(lang, "btn_skip"), callback_data=f"it:skip:{item.id}")],
    ])
    return "\n".join(lines), kb


class TelegramNotifier:
    def __init__(self, bot: Bot, db: DB):
        self.bot, self.db = bot, db

    async def _send(self, chat_id: int, text: str, kb: Kb | None = None) -> None:
        for _ in range(3):
            try:
                await self.bot.send_message(chat_id, text, reply_markup=kb)
                await asyncio.sleep(0.3)  # stay far below Telegram per-chat limits
                return
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)
            except TelegramForbiddenError:
                log.info("user %s blocked the bot", chat_id)
                return

    async def item(self, tg_id: int, item: Item, account: Account) -> None:
        user = self.db.get_user(tg_id)
        await self._send(tg_id, *render_card(item, account, user.lang if user else "ru"))

    async def text(self, tg_id: int, key: str, **kw) -> None:
        user = self.db.get_user(tg_id)
        await self._send(tg_id, t(user.lang if user else "ru", key, **{k: esc(v) for k, v in kw.items()}))


# ---------------------------------------------------------------- helpers
def user_of(db: DB, settings: Settings, tg_id: int):
    return db.get_or_create_user(tg_id, settings.free_monthly_limit)


def lang_kb() -> Kb:
    items = list(SELLER_LANGS.items())
    return Kb(inline_keyboard=[[Btn(text=v, callback_data=f"lang:{k}") for k, v in items[i:i + 3]]
                               for i in range(0, len(items), 3)])


# ---------------------------------------------------------------- basic commands
@router.message(Command("cancel"))
async def cmd_cancel(m: Message, state: FSMContext, db: DB, settings: Settings):
    await state.clear()
    await m.answer(t(user_of(db, settings, m.from_user.id).lang, "cancelled"))


@router.message(CommandStart())
async def cmd_start(m: Message, state: FSMContext, db: DB, settings: Settings):
    await state.clear()
    user = user_of(db, settings, m.from_user.id)
    await m.answer(t(user.lang, "choose_lang"), reply_markup=lang_kb())


@router.callback_query(F.data.startswith("lang:"))
async def cb_lang(c: CallbackQuery, db: DB, settings: Settings):
    code = c.data.split(":", 1)[1]
    if code in SELLER_LANGS:
        user_of(db, settings, c.from_user.id)
        db.update_user(c.from_user.id, lang=code)
        await c.message.edit_text(t(code, "help"))
    await c.answer()


@router.message(Command("help"))
async def cmd_help(m: Message, db: DB, settings: Settings):
    await m.answer(t(user_of(db, settings, m.from_user.id).lang, "help"))


# ---------------------------------------------------------------- connecting a shop
@router.message(Command("connect"))
async def cmd_connect(m: Message, state: FSMContext, db: DB, settings: Settings):
    await state.clear()
    lang = user_of(db, settings, m.from_user.id).lang
    kb = Kb(inline_keyboard=[[Btn(text=TITLES[k], callback_data=f"mp:{k}")] for k in
                             ("wildberries", "ozon", "yandex_market", "demo")])
    await m.answer(t(lang, "connect_choose"), reply_markup=kb)


async def _finish_connect(msg: Message, tg_id: int, marketplace: str, creds: dict,
                          db: DB, vault: Vault, engine: Engine, lang: str) -> None:
    status = await msg.answer(t(lang, "checking"))
    client = make_client(marketplace, creds)
    try:
        await client.check()
    except (AuthError, MarketplaceError) as e:
        await status.edit_text(t(lang, "connect_failed", error=esc(e)))
        return
    finally:
        await client.close()
    acc_id = db.add_account(tg_id, marketplace, vault.encrypt(creds))
    await status.edit_text(t(lang, "connected", mp=TITLES[marketplace]))
    task = asyncio.create_task(engine.poll_account(db.get_account(acc_id)))
    _background.add(task)
    task.add_done_callback(_background.discard)


@router.callback_query(F.data.startswith("mp:"))
async def cb_marketplace(c: CallbackQuery, state: FSMContext, db: DB, settings: Settings, vault: Vault, engine: Engine):
    mp = c.data.split(":", 1)[1]
    lang = user_of(db, settings, c.from_user.id).lang
    await c.answer()
    if mp == "demo":
        await _finish_connect(c.message, c.from_user.id, "demo", {}, db, vault, engine, lang)
        return
    if mp not in TITLES:
        return
    await state.set_state(Connect.creds)
    await state.update_data(mp=mp)
    await c.message.answer(t(lang, f"ask_{mp}"))


@router.message(Connect.creds, F.text, NOT_COMMAND)
async def on_creds(m: Message, state: FSMContext, db: DB, settings: Settings, vault: Vault, engine: Engine):
    lang = user_of(db, settings, m.from_user.id).lang
    mp = (await state.get_data())["mp"]
    try:
        await m.delete()  # the message contains a secret key
    except TelegramBadRequest:
        pass
    try:
        creds = parse_credentials(mp, m.text.strip())
    except ValueError:
        await m.answer(t(lang, "bad_format"))
        return
    await state.clear()
    await _finish_connect(m, m.from_user.id, mp, creds, db, vault, engine, lang)


@router.message(Command("accounts"))
async def cmd_accounts(m: Message, db: DB, settings: Settings):
    lang = user_of(db, settings, m.from_user.id).lang
    accs = db.list_accounts(m.from_user.id)
    if not accs:
        await m.answer(t(lang, "no_accounts"))
        return
    lines = [t(lang, "accounts")]
    for a in accs:
        state = t(lang, "acc_ok") if a.active else t(lang, "acc_off", error=esc(cut(a.last_error, 200)))
        lines.append(t(lang, "acc_line", mp=TITLES[a.marketplace], id=a.id, state=state))
    kb = Kb(inline_keyboard=[[Btn(text=t(lang, "btn_remove", mp=TITLES[a.marketplace], id=a.id),
                                  callback_data=f"acc:del:{a.id}")] for a in accs])
    await m.answer("\n".join(lines), reply_markup=kb)


@router.callback_query(F.data.startswith("acc:del:"))
async def cb_acc_del(c: CallbackQuery, db: DB, settings: Settings):
    lang = user_of(db, settings, c.from_user.id).lang
    ok = db.delete_account(int(c.data.rsplit(":", 1)[1]), c.from_user.id)
    await c.answer(t(lang, "removed" if ok else "not_found"))
    if ok:
        await c.message.edit_reply_markup(reply_markup=None)


@router.message(Command("sync"))
async def cmd_sync(m: Message, db: DB, settings: Settings, engine: Engine):
    lang = user_of(db, settings, m.from_user.id).lang
    if not db.list_accounts(m.from_user.id, active_only=True):
        await m.answer(t(lang, "no_accounts_sync"))
        return
    await m.answer(t(lang, "sync_started"))
    n = await engine.poll_user(m.from_user.id)
    await m.answer(t(lang, "sync_done", n=n))


# ---------------------------------------------------------------- settings
def settings_view(db: DB, tg_id: int) -> tuple[str, Kb]:
    u = db.get_user(tg_id)
    auto = t(u.lang, "auto_off") if not u.auto_min_rating else t(u.lang, "auto_n", n=u.auto_min_rating)
    text = t(u.lang, "settings", lang=SELLER_LANGS.get(u.lang, u.lang), signature=esc(u.signature or "—"),
             auto=auto, used=u.used, limit=u.monthly_limit)
    kb = Kb(inline_keyboard=[
        [Btn(text=t(u.lang, "btn_auto_off"), callback_data="set:auto:0"),
         Btn(text=t(u.lang, "btn_auto_5"), callback_data="set:auto:5"),
         Btn(text=t(u.lang, "btn_auto_4"), callback_data="set:auto:4")],
        [Btn(text=t(u.lang, "btn_signature"), callback_data="set:sig"),
         Btn(text=t(u.lang, "btn_lang"), callback_data="set:lang")],
    ])
    return text, kb


@router.message(Command("settings"))
async def cmd_settings(m: Message, db: DB, settings: Settings):
    user_of(db, settings, m.from_user.id)
    text, kb = settings_view(db, m.from_user.id)
    await m.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("set:"))
async def cb_settings(c: CallbackQuery, state: FSMContext, db: DB, settings: Settings):
    user = user_of(db, settings, c.from_user.id)
    parts = c.data.split(":")
    await c.answer()
    if parts[1] == "auto" and parts[2] in ("0", "4", "5"):
        db.update_user(c.from_user.id, auto_min_rating=int(parts[2]))
        text, kb = settings_view(db, c.from_user.id)
        try:
            await c.message.edit_text(text, reply_markup=kb)
        except TelegramBadRequest:  # "message is not modified"
            pass
    elif parts[1] == "sig":
        await state.set_state(Signature.text)
        await c.message.answer(t(user.lang, "ask_signature"))
    elif parts[1] == "lang":
        await c.message.answer(t(user.lang, "choose_lang"), reply_markup=lang_kb())


@router.message(Signature.text, F.text, NOT_COMMAND)
async def on_signature(m: Message, state: FSMContext, db: DB, settings: Settings):
    user = user_of(db, settings, m.from_user.id)
    sig = m.text.strip()
    db.update_user(m.from_user.id, signature="" if sig == "-" else cut(sig, 100))
    await state.clear()
    await m.answer(t(user.lang, "saved"))


# ---------------------------------------------------------------- item actions
@router.callback_query(F.data.startswith("it:"))
async def cb_item(c: CallbackQuery, state: FSMContext, db: DB, settings: Settings, engine: Engine):
    lang = user_of(db, settings, c.from_user.id).lang
    _, action, raw_id = c.data.split(":")
    item_id = int(raw_id)
    if db.item_owner(item_id) != c.from_user.id:
        await c.answer(t(lang, "not_found"), show_alert=True)
        return
    try:
        if action == "send":
            await c.answer()
            item = await engine.send(item_id, c.from_user.id)
        elif action == "skip":
            await c.answer()
            item = engine.skip(item_id, c.from_user.id)
        elif action == "regen":
            await c.answer("…")
            item = await engine.regenerate(item_id, c.from_user.id)
        elif action == "edit":
            await state.set_state(Edit.text)
            await state.update_data(item_id=item_id)
            await c.answer()
            await c.message.answer(t(lang, "ask_edit"))
            return
        else:
            await c.answer()
            return
    except MarketplaceError as e:
        await c.message.answer(t(lang, "send_failed", error=esc(e)))
        return
    except DraftError as e:
        await c.message.answer(t(lang, "ai_failed", error=esc(e)))
        return
    except QuotaError:
        u = db.get_user(c.from_user.id)
        await c.message.answer(t(lang, "quota_exceeded", limit=u.monthly_limit))
        return
    text, kb = render_card(item, db.get_account(item.account_id), lang)
    try:
        await c.message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        pass


@router.message(Edit.text, F.text, NOT_COMMAND)
async def on_edit(m: Message, state: FSMContext, db: DB, settings: Settings, engine: Engine):
    lang = user_of(db, settings, m.from_user.id).lang
    item_id = (await state.get_data()).get("item_id")
    await state.clear()
    try:
        item = await engine.set_seller_text(item_id, m.from_user.id, m.text.strip())
    except DraftError as e:
        await m.answer(t(lang, "ai_failed", error=esc(e)))
        return
    except PermissionError:
        await m.answer(t(lang, "not_found"))
        return
    text, kb = render_card(item, db.get_account(item.account_id), lang)
    await m.answer(text, reply_markup=kb)


# ---------------------------------------------------------------- admin
@router.message(Command("stats"))
async def cmd_stats(m: Message, db: DB, settings: Settings):
    if m.from_user.id not in settings.admin_ids:
        return
    s = db.stats()
    await m.answer("<b>Stats</b>\n" + "\n".join(f"{k}: {esc(v)}" for k, v in s.items()))


@router.message(Command("grant"))
async def cmd_grant(m: Message, command: CommandObject, db: DB, settings: Settings):
    """/grant <tg_id> <monthly_limit> — e.g. after a crowdfunding backer pays for a plan."""
    if m.from_user.id not in settings.admin_ids:
        return
    try:
        tg_id, limit = (int(x) for x in (command.args or "").split())
    except ValueError:
        await m.answer("Usage: /grant <tg_id> <monthly_limit>")
        return
    db.get_or_create_user(tg_id, settings.free_monthly_limit)
    db.update_user(tg_id, monthly_limit=limit, quota_warned="")
    await m.answer(f"OK: {tg_id} → {limit}/month")
