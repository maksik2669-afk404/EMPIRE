"""WINTER ARC sales bot: Telegram Stars checkout -> link to copy the Google Sheet.

Run: python -m salesbot.bot   (settings in .env.salesbot, see salesbot/README.md)
"""
from __future__ import annotations

import asyncio
import html
import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import BotCommand, CallbackQuery
from aiogram.types import InlineKeyboardButton as Btn
from aiogram.types import InlineKeyboardMarkup as Kb
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery

from app.config import load_dotenv
from app.main import resolve_telegram_route, wait_for_telegram

ENV_FILE = ".env.salesbot"
PAYLOAD = "winter_arc_2026"
log = logging.getLogger("salesbot")
router = Router()


@dataclass(frozen=True)
class Config:
    token: str
    table_url: str
    price: int = 149
    admins: frozenset = frozenset()
    db_path: str = "data/sales.db"
    welcome_video: str = ""
    support: str = ""
    proxy: str = ""

    @classmethod
    def from_env(cls, path: str = ENV_FILE) -> "Config":
        load_dotenv(path)
        e = os.environ.get
        if not e("SALES_BOT_TOKEN") or not e("TABLE_URL"):
            raise SystemExit(f"Заполните SALES_BOT_TOKEN и TABLE_URL в {path}")
        return cls(
            token=e("SALES_BOT_TOKEN", ""), table_url=e("TABLE_URL", ""), price=int(e("PRICE_STARS", "149")),
            admins=frozenset(int(x) for x in e("ADMIN_IDS", "").replace(" ", "").split(",") if x),
            db_path=e("SALES_DB", "data/sales.db"), welcome_video=e("WELCOME_VIDEO_URL", ""),
            support=e("SUPPORT_CONTACT", ""), proxy=e("TELEGRAM_PROXY", ""),
        )


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class Store:
    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.c = sqlite3.connect(path, check_same_thread=False)
        self.c.executescript("""
            CREATE TABLE IF NOT EXISTS users (tg_id INTEGER PRIMARY KEY, username TEXT, source TEXT,
                                              created_at TEXT, blocked INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS purchases (charge_id TEXT PRIMARY KEY, tg_id INTEGER, amount INTEGER,
                                                  currency TEXT, created_at TEXT, refunded INTEGER NOT NULL DEFAULT 0);
        """)

    def _x(self, sql: str, args: tuple = ()) -> sqlite3.Cursor:
        cur = self.c.execute(sql, args)
        self.c.commit()
        return cur

    def touch(self, tg_id: int, username: str, source: str) -> None:
        """First touch wins: the source is the deep link (t.me/bot?start=reel01) that brought the user."""
        self._x("INSERT OR IGNORE INTO users (tg_id, username, source, created_at) VALUES (?, ?, ?, ?)",
                (tg_id, username, source, now()))
        self._x("UPDATE users SET username=?, blocked=0 WHERE tg_id=?", (username, tg_id))

    def source(self, tg_id: int) -> str:
        row = self.c.execute("SELECT source FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        return row[0] if row else "?"

    def has_access(self, tg_id: int) -> bool:
        return self.c.execute("SELECT 1 FROM purchases WHERE tg_id=? AND refunded=0", (tg_id,)).fetchone() is not None

    def add_purchase(self, charge_id: str, tg_id: int, amount: int, currency: str) -> bool:
        return self._x("INSERT OR IGNORE INTO purchases (charge_id, tg_id, amount, currency, created_at) "
                       "VALUES (?, ?, ?, ?, ?)", (charge_id, tg_id, amount, currency, now())).rowcount == 1

    def last_charge(self, tg_id: int) -> str | None:
        row = self.c.execute("SELECT charge_id FROM purchases WHERE tg_id=? AND refunded=0 AND currency='XTR' "
                             "ORDER BY created_at DESC LIMIT 1", (tg_id,)).fetchone()
        return row[0] if row else None

    def mark_refunded(self, charge_id: str) -> None:
        self._x("UPDATE purchases SET refunded=1 WHERE charge_id=?", (charge_id,))

    def audience(self) -> list[int]:
        return [r[0] for r in self.c.execute("SELECT tg_id FROM users WHERE blocked=0")]

    def set_blocked(self, tg_id: int) -> None:
        self._x("UPDATE users SET blocked=1 WHERE tg_id=?", (tg_id,))

    def stats(self) -> dict:
        q = lambda sql: self.c.execute(sql).fetchone()[0] or 0  # noqa: E731
        by_source = self.c.execute("""
            SELECT u.source, COUNT(DISTINCT u.tg_id), COUNT(DISTINCT p.tg_id)
            FROM users u LEFT JOIN purchases p ON p.tg_id=u.tg_id AND p.refunded=0
            GROUP BY u.source ORDER BY 2 DESC LIMIT 15""").fetchall()
        return {
            "users": q("SELECT COUNT(*) FROM users"),
            "buyers": q("SELECT COUNT(DISTINCT tg_id) FROM purchases WHERE refunded=0"),
            "stars": q("SELECT SUM(amount) FROM purchases WHERE refunded=0 AND currency='XTR'"),
            "gifts": q("SELECT COUNT(*) FROM purchases WHERE currency='GIFT' AND refunded=0"),
            "refunds": q("SELECT COUNT(*) FROM purchases WHERE refunded=1"),
            "today": q("SELECT COUNT(*) FROM purchases WHERE refunded=0 AND created_at >= date('now')"),
            "by_source": by_source,
        }


# ---------------------------------------------------------------- texts
def welcome(cfg: Config) -> str:
    return ("❄ <b>WINTER ARC 2026</b>\n"
            "92 дня · 01.10 — 31.12\n\n"
            "Трекер привычек в Google Таблицах, который превращает зиму в систему:\n"
            "• две версии — <b>HIM</b> и <b>HER</b>\n"
            "• 8 привычек с галочками — переименуй под себя\n"
            "• прогресс дня, серия без пропусков и общий % считаются сами\n"
            "• сон, вес, настроение и заметка дня\n"
            "• работает с телефона, копия твоя навсегда\n\n"
            f"Цена: <b>{cfg.price} ⭐</b> — оплата внутри Telegram, таблица сразу после оплаты.")


ABOUT = ("<b>Как это работает</b>\n\n"
         "1. Жмёшь «Купить» и платишь звёздами Telegram — 10 секунд, без карт и сайтов.\n"
         "2. Бот сразу присылает кнопку «Скопировать таблицу».\n"
         "3. Google предложит «Создать копию» — таблица появится на твоём Google Диске.\n"
         "4. Открываешь лист ❄ HIM или ❄ HER, вписываешь свои привычки — и каждый вечер ставишь галочки.\n\n"
         "Нужен Google-аккаунт. С телефона — в приложении Google Таблицы.\n"
         "Звёзды можно купить прямо в Telegram: Настройки → Мои звёзды.")

ACCESS = ("✅ <b>Доступ открыт!</b>\n\n"
          "1. Нажми кнопку ниже → «Создать копию».\n"
          "2. Таблица появится на твоём Google Диске — она твоя навсегда.\n"
          "3. Открой лист ❄ HIM или ❄ HER и впиши свои привычки.\n\n"
          "Winter arc стартует 1 октября. Не рви серию ❄\n"
          "Потерял ссылку — /mytable")

TERMS = ("<b>Условия</b>\n\nТы покупаешь цифровой товар — ссылку для копирования таблицы WINTER ARC 2026 "
         "в свой Google Диск. Ссылка выдаётся автоматически сразу после оплаты. Если таблица не открылась "
         "или не работает — напиши в /paysupport, поможем или вернём звёзды.")


def paysupport(cfg: Config) -> str:
    contact = html.escape(cfg.support) if cfg.support else "ответь на это сообщение"
    return ("<b>Помощь с оплатой</b>\n\nПроблема с оплатой или доступом — напиши: " + contact
            + ". Опиши, что случилось; ответим в течение 24 часов. Возврат звёзд — если таблица не работает.")


def kb_main(cfg: Config) -> Kb:
    return Kb(inline_keyboard=[[Btn(text=f"❄ Купить за {cfg.price} ⭐", callback_data="buy")],
                               [Btn(text="Как это работает", callback_data="about")]])


def kb_access(cfg: Config) -> Kb:
    return Kb(inline_keyboard=[[Btn(text="❄ Скопировать таблицу", url=cfg.table_url)]])


# ---------------------------------------------------------------- buyer flow
@router.message(CommandStart())
async def cmd_start(m: Message, command: CommandObject, store: Store, cfg: Config):
    store.touch(m.from_user.id, m.from_user.username or "", (command.args or "direct")[:32])
    if store.has_access(m.from_user.id):
        await m.answer(ACCESS, reply_markup=kb_access(cfg))
        return
    if cfg.welcome_video:
        try:
            await m.answer_video(cfg.welcome_video, caption=welcome(cfg), reply_markup=kb_main(cfg))
            return
        except TelegramBadRequest as e:  # video URL unavailable -> plain text still sells
            log.warning("welcome video failed: %s", e)
    await m.answer(welcome(cfg), reply_markup=kb_main(cfg))


@router.callback_query(F.data == "about")
async def cb_about(c: CallbackQuery, cfg: Config):
    await c.answer()
    await c.message.answer(ABOUT, reply_markup=kb_main(cfg))


@router.callback_query(F.data == "buy")
async def cb_buy(c: CallbackQuery, store: Store, cfg: Config):
    await c.answer()
    if store.has_access(c.from_user.id):
        await c.message.answer(ACCESS, reply_markup=kb_access(cfg))
        return
    await c.message.answer_invoice(
        title="WINTER ARC 2026 — трекер привычек",
        description="Google-таблица на 92 дня: версии HIM и HER, галочки, серия, прогресс. "
                    "Ссылка на копию — сразу после оплаты.",
        payload=PAYLOAD, currency="XTR", prices=[LabeledPrice(label="WINTER ARC 2026", amount=cfg.price)],
    )


@router.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery, cfg: Config):
    ok = q.invoice_payload == PAYLOAD and q.currency == "XTR" and q.total_amount == cfg.price
    await q.answer(ok=ok, error_message=None if ok else "Цена обновилась — нажми /start и оплати снова.")


@router.message(F.successful_payment)
async def on_paid(m: Message, bot: Bot, store: Store, cfg: Config):
    sp = m.successful_payment
    fresh = store.add_purchase(sp.telegram_payment_charge_id, m.from_user.id, sp.total_amount, sp.currency)
    await m.answer(ACCESS, reply_markup=kb_access(cfg))
    if fresh:
        who = html.escape(m.from_user.full_name) + (f" @{m.from_user.username}" if m.from_user.username else "")
        await notify_admins(bot, cfg, f"💸 Продажа: {who} · {sp.total_amount} ⭐ · источник: "
                                      f"{html.escape(store.source(m.from_user.id))}")


@router.message(Command("mytable"))
async def cmd_mytable(m: Message, store: Store, cfg: Config):
    if store.has_access(m.from_user.id):
        await m.answer(ACCESS, reply_markup=kb_access(cfg))
    else:
        await m.answer("Доступа пока нет.\n\n" + welcome(cfg), reply_markup=kb_main(cfg))


@router.message(Command("paysupport"))
async def cmd_paysupport(m: Message, cfg: Config):
    await m.answer(paysupport(cfg))


@router.message(Command("terms"))
async def cmd_terms(m: Message):
    await m.answer(TERMS)


# ---------------------------------------------------------------- admin
async def notify_admins(bot: Bot, cfg: Config, text: str) -> None:
    for admin in cfg.admins:
        try:
            await bot.send_message(admin, text)
        except (TelegramBadRequest, TelegramForbiddenError):
            pass


def is_admin(m: Message, cfg: Config) -> bool:
    return m.from_user.id in cfg.admins


@router.message(Command("stats"))
async def cmd_stats(m: Message, store: Store, cfg: Config):
    if not is_admin(m, cfg):
        return
    s = store.stats()
    lines = ["<b>Статистика</b>", f"Пользователей: {s['users']}", f"Покупателей: {s['buyers']}",
             f"Звёзд: {s['stars']} ⭐", f"Продаж сегодня: {s['today']}", f"Подарено: {s['gifts']} · возвратов: {s['refunds']}",
             "", "<b>Источники</b> (пришли → купили):"]
    lines += [f"{html.escape(src or '?')}: {u} → {b}" for src, u, b in s["by_source"]]
    await m.answer("\n".join(lines))


@router.message(Command("give"))
async def cmd_give(m: Message, command: CommandObject, bot: Bot, store: Store, cfg: Config):
    """/give <tg_id> — выдать доступ вручную (оплатили переводом, блогер, розыгрыш)."""
    if not is_admin(m, cfg):
        return
    try:
        uid = int((command.args or "").strip())
    except ValueError:
        await m.answer("Формат: /give 123456789")
        return
    store.add_purchase(f"gift-{uid}-{now()}", uid, 0, "GIFT")
    try:
        await bot.send_message(uid, ACCESS, reply_markup=kb_access(cfg))
        await m.answer(f"Готово: доступ выдан {uid}.")
    except (TelegramBadRequest, TelegramForbiddenError):
        await m.answer(f"Доступ записан, но написать {uid} нельзя: он ещё не запускал бота.")


@router.message(Command("refund"))
async def cmd_refund(m: Message, command: CommandObject, bot: Bot, store: Store, cfg: Config):
    """/refund <tg_id> — вернуть звёзды за последнюю покупку и закрыть доступ."""
    if not is_admin(m, cfg):
        return
    try:
        uid = int((command.args or "").strip())
    except ValueError:
        await m.answer("Формат: /refund 123456789")
        return
    charge = store.last_charge(uid)
    if not charge:
        await m.answer("Оплаченных звёздами покупок у этого пользователя нет.")
        return
    try:
        await bot.refund_star_payment(user_id=uid, telegram_payment_charge_id=charge)
    except TelegramBadRequest as e:
        await m.answer(f"Telegram отказал в возврате: {html.escape(str(e))}")
        return
    store.mark_refunded(charge)
    await m.answer(f"Звёзды возвращены пользователю {uid}.")


@router.message(Command("broadcast"))
async def cmd_broadcast(m: Message, command: CommandObject, bot: Bot, store: Store, cfg: Config):
    """/broadcast <текст> или ответом на любое сообщение — разослать всем, кто запускал бота."""
    if not is_admin(m, cfg):
        return
    src = m.reply_to_message
    if not src and not command.args:
        await m.answer("Напиши /broadcast текст — или ответь командой /broadcast на сообщение (фото, видео, текст).")
        return
    sent = failed = 0
    for uid in store.audience():
        try:
            if src:
                await bot.copy_message(uid, m.chat.id, src.message_id, reply_markup=None if store.has_access(uid)
                                       else kb_main(cfg))
            else:
                await bot.send_message(uid, command.args, reply_markup=None if store.has_access(uid) else kb_main(cfg))
            sent += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            failed += 1
        except TelegramForbiddenError:
            store.set_blocked(uid)
            failed += 1
        except TelegramBadRequest:
            failed += 1
        await asyncio.sleep(0.05)  # ~20 messages/s, below Telegram's broadcast limit
    await m.answer(f"Рассылка: доставлено {sent}, не доставлено {failed}.")


# ---------------------------------------------------------------- entry point
async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = Config.from_env()
    route = await resolve_telegram_route(cfg.token, cfg.proxy, ENV_FILE)
    session = AiohttpSession(proxy=route) if route else None
    bot = Bot(cfg.token, session=session, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(store=Store(cfg.db_path), cfg=cfg)
    dp.include_router(router)
    try:
        me = await wait_for_telegram(bot)
        await bot.set_my_commands([BotCommand(command="start", description="Главное меню"),
                                   BotCommand(command="mytable", description="Моя таблица"),
                                   BotCommand(command="paysupport", description="Помощь с оплатой"),
                                   BotCommand(command="terms", description="Условия")])
        log.info("sales bot @%s started · price %s ⭐ · ссылка для профиля: https://t.me/%s?start=ig",
                 me.username, cfg.price, me.username)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
