"""Entry point: python -m app.main"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from .bot.handlers import TelegramNotifier, router
from .config import Settings
from .crypto import Vault
from .db import DB
from .llm import make_llm
from .service import Engine

log = logging.getLogger("app")

COMMANDS = {
    "ru": ["Подключить магазин", "Карточка товара на русском", "Факты о товарах", "Мои магазины",
           "Проверить сейчас", "Настройки", "Справка"],
    "en": ["Connect a shop", "Russian product card", "Product facts", "My shops", "Check now", "Settings", "Help"],
    "zh": ["连接店铺", "俄语商品卡", "商品信息", "我的店铺", "立即检查", "设置", "帮助"],
}


async def poll_loop(engine: Engine, interval: int) -> None:
    while True:
        try:
            await engine.poll_all()
        except Exception:
            log.exception("poll loop error")
        await asyncio.sleep(interval)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    s = Settings.from_env()
    db = DB(s.db_path)
    vault = Vault(s.fernet_key)
    llm = make_llm(s)
    session = AiohttpSession(proxy=s.telegram_proxy) if s.telegram_proxy else None
    bot = Bot(s.bot_token, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    engine = Engine(db, vault, llm, TelegramNotifier(bot, db), s.max_items_per_poll)
    dp = Dispatcher(storage=MemoryStorage(), engine=engine, db=db, vault=vault, settings=s)
    dp.include_router(router)

    for lang, names in COMMANDS.items():
        cmds = [BotCommand(command=c, description=d)
                for c, d in zip(("connect", "card", "facts", "accounts", "sync", "settings", "help"), names)]
        await bot.set_my_commands(cmds, language_code=None if lang == "ru" else lang)

    poller = asyncio.create_task(poll_loop(engine, s.poll_interval_sec))
    log.info("bot started, LLM=%s, poll every %ss", s.llm_provider, s.poll_interval_sec)
    try:
        await dp.start_polling(bot)
    finally:
        poller.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
