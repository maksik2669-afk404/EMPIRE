
import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramNetworkError, TelegramUnauthorizedError
from aiogram.methods import GetMe
from aiogram.types import User

from app.main import wait_for_telegram
from tests.test_bot_flow import FakeSession


class FlakySession(FakeSession):
    def __init__(self, failures, error_cls=TelegramNetworkError):
        super().__init__()
        self.failures, self.error_cls = failures, error_cls

    async def make_request(self, bot, method, timeout=None):
        if self.failures:
            self.failures -= 1
            raise self.error_cls(method=method, message="Cannot connect to host api.telegram.org:443")
        assert isinstance(method, GetMe)
        return User(id=1, is_bot=True, first_name="b", username="MarketplaceBot")


async def test_waits_for_telegram_instead_of_crashing(caplog):
    bot = Bot("123456:" + "A" * 35, session=FlakySession(failures=2))
    me = await wait_for_telegram(bot, first_delay=0.01)
    assert me.username == "MarketplaceBot"
    assert "TELEGRAM_PROXY" in caplog.text


async def test_bad_token_exits_with_clear_message():
    bot = Bot("123456:" + "A" * 35, session=FlakySession(failures=1, error_cls=TelegramUnauthorizedError))
    with pytest.raises(SystemExit, match="BOT_TOKEN"):
        await wait_for_telegram(bot, first_delay=0.01)
