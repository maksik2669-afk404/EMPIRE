"""Bot flow against a fake Telegram session: шапка -> работы -> рез -> файлы -> профит."""
import datetime
from pathlib import Path

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import SendDocument, SendMessage
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from smeta.bot import Deps, router
from smeta.catalog import Catalog
from smeta.materials import OfferBook
from smeta.store import Store

CHAT = Chat(id=77, type="private")
USER = User(id=77, is_bot=False, first_name="Игорь")


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.sent: list = []

    async def make_request(self, bot, method, timeout=None):
        self.sent.append(method)
        if isinstance(method, SendMessage):
            return Message(message_id=len(self.sent), date=datetime.datetime.now(), chat=CHAT,
                           text=method.text).as_(bot)
        if getattr(method, "__returning__", None) is bool:
            return True
        return Message(message_id=len(self.sent), date=datetime.datetime.now(), chat=CHAT, text="ok").as_(bot)

    async def stream_content(self, *args, **kwargs):  # pragma: no cover
        yield b""

    async def close(self):
        pass

    def texts(self) -> str:
        return "\n".join(m.text for m in self.sent if isinstance(m, SendMessage))

    def documents(self) -> list:
        return [m for m in self.sent if isinstance(m, SendDocument)]


@pytest.fixture(scope="module")
def dispatcher() -> Dispatcher:
    """The router is a module-level singleton, so it is attached to one Dispatcher only."""
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    return dp


def message(bot: Bot, text: str, mid: int) -> Update:
    return Update.model_validate(
        {"update_id": mid, "message": Message(message_id=mid, date=datetime.datetime.now(), chat=CHAT,
                                              from_user=USER, text=text).model_dump()},
        context={"bot": bot},
    )


def callback(bot: Bot, data: str, mid: int) -> Update:
    carrier = Message(message_id=900 + mid, date=datetime.datetime.now(), chat=CHAT, text="смета")
    return Update.model_validate(
        {"update_id": mid, "callback_query": CallbackQuery(id=str(mid), from_user=USER, chat_instance="c",
                                                           message=carrier, data=data).model_dump()},
        context={"bot": bot},
    )


async def test_full_flow(tmp_path: Path, dispatcher: Dispatcher):
    session = FakeSession()
    bot = Bot("42:TEST", session=session, default=DefaultBotProperties(parse_mode="HTML"))
    deps = Deps(
        store=Store(tmp_path / "smeta.db"),
        catalog=Catalog.load(),
        offers=OfferBook.load("data/suppliers/demo.csv"),
        export_dir=tmp_path / "export",
    )
    async def feed(update: Update) -> None:
        await dispatcher.feed_update(bot, update, deps=deps)

    mid = 0

    async def say(text: str) -> None:
        nonlocal mid
        mid += 1
        await feed(message(bot, text, mid))

    async def tap(data: str) -> None:
        nonlocal mid
        mid += 1
        await feed(callback(bot, data, mid))

    await say("/start")
    assert "Сметчик" in session.texts()

    # шапка
    await say("/company")
    for answer in ["ООО «СтройПро»", "7707083893", "770701001", "г. Москва", "+7 999 000-00-00", "Директор Иванов И.И."]:
        await say(answer)
    assert deps.store.company(USER.id).inn == "7707083893"
    assert "Шапка сохранена" in session.texts()

    # новая смета
    await say("/new")
    await say("г. Москва, ул. Ленина, 5")
    await say("ООО «Ромашка»")
    estimate_id = deps.store.settings(USER.id)["current_id"]
    assert estimate_id

    # работы и материалы одним сообщением
    await say("штукатурка стен 120 м2\nстяжка пола 85 м2 по 700\nмат: керамогранит 22 м2\nподшив сайдингом 30 м2")
    estimate = deps.store.load_estimate(USER.id, estimate_id)
    assert len(estimate.positions) == 4
    assert estimate.positions[0].code == "ДЕМО-03.01"
    assert estimate.positions[2].unit_price == 1550          # розница из прайса
    full = estimate.total()
    assert "нет в справочнике" in session.texts()

    # цена для позиции, которой нет в справочнике
    await say("/price 4 900")
    estimate = deps.store.load_estimate(USER.id, estimate_id)
    assert estimate.positions[3].unit_price == 900
    assert estimate.total() > full

    # рез на 20 % кнопкой и подгон под сумму
    before = deps.store.load_estimate(USER.id, estimate_id).total()
    await tap("cut:20")
    after = deps.store.load_estimate(USER.id, estimate_id).total()
    assert after < before
    await say("/fit 500000")
    assert deps.store.load_estimate(USER.id, estimate_id).total() == 500000
    await say("/reset")
    assert deps.store.load_estimate(USER.id, estimate_id).total() == before

    # кнопка «под сумму»: следующее сообщение — число, а не новая позиция
    await tap("fit")
    await say("450000")
    estimate = deps.store.load_estimate(USER.id, estimate_id)
    assert estimate.total() == 450000
    assert len(estimate.positions) == 4
    await say("/reset")

    # файлы
    await tap("xlsx")
    await tap("pdf")
    assert len(session.documents()) == 2

    # профит виден только владельцу и не попадает в файл заказчика
    await tap("profit")
    assert "в карман" in session.texts()
    await tap("profit_file")
    assert len(session.documents()) == 3

    # удаление позиции и НДС
    await say("/del 4")
    assert len(deps.store.load_estimate(USER.id, estimate_id).positions) == 3
    await say("/vat 0")
    assert deps.store.settings(USER.id)["vat_pct"] == 0
    assert deps.store.load_estimate(USER.id, estimate_id).vat_pct == 0

    # справочник и список смет
    await say("/rates плитка")
    assert "Укладка керамической плитки" in session.texts()
    await say("/list")
    assert f"/open {estimate_id}" in session.texts()
    deps.store.close()
    await bot.session.close()


async def test_text_without_estimate_creates_one(tmp_path: Path, dispatcher: Dispatcher):
    session = FakeSession()
    bot = Bot("42:TEST", session=session, default=DefaultBotProperties(parse_mode="HTML"))
    deps = Deps(store=Store(tmp_path / "s.db"), catalog=Catalog.load(),
                offers=OfferBook(), export_dir=tmp_path / "e")
    await dispatcher.feed_update(bot, message(bot, "покраска стен 50 м2", 1), deps=deps)
    settings = deps.store.settings(USER.id)
    assert settings["current_id"]
    estimate = deps.store.load_estimate(USER.id, settings["current_id"])
    assert estimate.positions[0].code == "ДЕМО-03.06"
    assert estimate.number.startswith("СМ-")
    deps.store.close()
    await bot.session.close()
