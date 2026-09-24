"""Entry point: python -m app.main"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError, TelegramUnauthorizedError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from .bot.handlers import TelegramNotifier, router
from .config import Settings
from .crypto import Vault
from .db import DB
from .llm import make_llm
from .netcheck import find_route, save_env_value
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


async def wait_for_telegram(bot: Bot, first_delay: float = 10, max_delay: float = 300):
    """Blocks until api.telegram.org answers, with a clear hint instead of a crash loop."""
    delay = first_delay
    while True:
        try:
            return await bot.get_me()
        except TelegramUnauthorizedError:
            raise SystemExit("BOT_TOKEN неверный или отозван: получите токен у @BotFather и исправьте .env")
        except TelegramNetworkError as e:
            log.error("Нет связи с api.telegram.org (%s). Если Telegram заблокирован в вашей сети — укажите в .env "
                      "TELEGRAM_PROXY=socks5://127.0.0.1:ПОРТ (локальный порт VPN-клиента) и перезапустите. "
                      "Повтор через %d с.", e, delay)
            await asyncio.sleep(delay)
            delay = min(delay * 2, max_delay)


async def resolve_telegram_route(token: str, configured: str, env_path: str = ".env") -> str:
    """Picks direct / proxy automatically and remembers it in .env; waits (and re-checks) while Telegram is unreachable."""
    delay = 15
    while True:
        route = await find_route(token, configured)
        if route is not None:
            if route != configured:
                log.info("Маршрут к Telegram: %s — сохраняю в .env", route or "напрямую")
                if Path(env_path).exists():
                    save_env_value(env_path, "TELEGRAM_PROXY", route)
            return route
        log.error("api.telegram.org недоступен ни напрямую, ни через системный прокси, ни через VPN-клиент на этом "
                  "компьютере. Включите VPN-клиент (v2rayN, Hiddify, NekoBox, Clash) — бот найдёт его сам. "
                  "Проверю снова через %d с.", delay)
        await asyncio.sleep(delay)
        delay = min(delay * 2, 300)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    s = Settings.from_env()
    db = DB(s.db_path)
    vault = Vault(s.fernet_key)
    llm = make_llm(s)
    route = await resolve_telegram_route(s.bot_token, s.telegram_proxy)
    session = AiohttpSession(proxy=route) if route else None
    bot = Bot(s.bot_token, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    engine = Engine(db, vault, llm, TelegramNotifier(bot, db), s.max_items_per_poll)
    dp = Dispatcher(storage=MemoryStorage(), engine=engine, db=db, vault=vault, settings=s)
    dp.include_router(router)

    poller = None
    try:
        me = await wait_for_telegram(bot)
        for lang, names in COMMANDS.items():
            cmds = [BotCommand(command=c, description=d)
                    for c, d in zip(("connect", "card", "facts", "accounts", "sync", "settings", "help"), names)]
            await bot.set_my_commands(cmds, language_code=None if lang == "ru" else lang)
        poller = asyncio.create_task(poll_loop(engine, s.poll_interval_sec))
        log.info("bot @%s started, LLM=%s, proxy=%s, poll every %ss",
                 me.username, s.llm_provider, route or "direct", s.poll_interval_sec)
        await dp.start_polling(bot)
    finally:
        if poller:
            poller.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
