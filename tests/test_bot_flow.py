"""End-to-end bot flow with a fake Telegram session: /start -> language -> /connect Demo -> cards -> send."""
import asyncio
import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import SendMessage
from aiogram.types import CallbackQuery, Chat, Message, Update, User
from cryptography.fernet import Fernet

from app.bot.handlers import TelegramNotifier, router
from app.config import Settings
from app.crypto import Vault
from app.db import DB
from app.llm import MockLLM
from app.service import Engine

CHAT = Chat(id=42, type="private")
USER = User(id=42, is_bot=False, first_name="Seller")


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.sent: list = []

    async def make_request(self, bot, method, timeout=None):
        self.sent.append(method)
        if isinstance(method, SendMessage):
            return Message(message_id=len(self.sent), date=datetime.datetime.now(), chat=CHAT, text=method.text,
                           reply_markup=method.reply_markup).as_(bot)
        if method.__returning__ is bool:
            return True
        return Message(message_id=len(self.sent), date=datetime.datetime.now(), chat=CHAT, text="x").as_(bot)

    async def stream_content(self, *a, **k):  # pragma: no cover
        yield b""

    async def close(self):
        pass


def msg(text: str, mid: int = 1) -> Update:
    return Update.model_validate({"update_id": mid, "message": Message(
        message_id=mid, date=datetime.datetime.now(), chat=CHAT, from_user=USER, text=text).model_dump()},
        context={"bot": BOT[0]})


def cb(data: str, uid: int) -> Update:
    m = Message(message_id=999, date=datetime.datetime.now(), chat=CHAT, text="card")
    return Update.model_validate({"update_id": uid, "callback_query": CallbackQuery(
        id=str(uid), from_user=USER, chat_instance="c", message=m, data=data).model_dump()}, context={"bot": BOT[0]})


BOT: list = []


async def test_full_flow():
    session = FakeSession()
    bot = Bot("123456:" + "A" * 35, session=session, default=DefaultBotProperties(parse_mode="HTML"))
    BOT[:] = [bot]
    db = DB(":memory:")
    settings = Settings(bot_token="x", fernet_key=Fernet.generate_key().decode(), llm_provider="mock",
                        admin_ids=frozenset({42}))
    vault = Vault(settings.fernet_key)
    engine = Engine(db, vault, MockLLM(), TelegramNotifier(bot, db))
    dp = Dispatcher(storage=MemoryStorage(), engine=engine, db=db, vault=vault, settings=settings)
    dp.include_router(router)

    await dp.feed_update(bot, msg("/start", 1))
    await dp.feed_update(bot, cb("lang:zh", 2))
    assert db.get_user(42).lang == "zh"

    await dp.feed_update(bot, msg("/connect", 3))
    await dp.feed_update(bot, cb("mp:demo", 4))
    for _ in range(100):  # background poll after connecting
        await asyncio.sleep(0.05)
        cards = [m for m in session.sent if isinstance(m, SendMessage) and m.reply_markup and "it:send" in str(m.reply_markup)]
        if len(cards) == 5:
            break
    assert len(cards) == 5, [getattr(m, "text", m) for m in session.sent]
    assert "评价" in cards[0].text  # Chinese UI

    first_id = int(cards[0].reply_markup.inline_keyboard[0][0].callback_data.split(":")[2])
    await dp.feed_update(bot, cb(f"it:send:{first_id}", 5))
    assert db.get_item(first_id).status == "sent"

    # edit flow: seller writes own text -> new card with the translated reply
    second_id = first_id + 1
    await dp.feed_update(bot, cb(f"it:edit:{second_id}", 6))
    await dp.feed_update(bot, msg("谢谢您的评价", 7))
    assert db.get_item(second_id).draft == "谢谢您的评价"  # MockLLM echoes the text

    # connecting WB with a malformed token is rejected and the secret message is deleted
    await dp.feed_update(bot, msg("/connect", 8))
    await dp.feed_update(bot, cb("mp:wildberries", 9))
    await dp.feed_update(bot, msg("short", 10))
    assert any(type(m).__name__ == "DeleteMessage" for m in session.sent)

    await dp.feed_update(bot, msg("/cancel", 11))
    await dp.feed_update(bot, msg("/stats", 12))
    assert "users_with_accounts" in session.sent[-1].text
    await dp.feed_update(bot, msg("/settings", 13))
    await dp.feed_update(bot, cb("set:auto:5", 14))
    assert db.get_user(42).auto_min_rating == 5
