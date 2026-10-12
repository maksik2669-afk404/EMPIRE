"""Bot flows against a fake Telegram session: menus, «Назад», wizards, documents, payments, reminders."""
import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import EditMessageText, GetFile, SendDocument, SendInvoice, SendMessage
from aiogram.types import (
    CallbackQuery, Chat, Document, File, Message, PreCheckoutQuery, SuccessfulPayment, Update, User,
)

from smeta import ui
from smeta.bot import Deps, router, run_reminders
from smeta.catalog import Catalog
from smeta.context import Ctx
from smeta.materials import OfferBook
from smeta.store import Store

CHAT = Chat(id=77, type="private")
USER = User(id=77, is_bot=False, first_name="Игорь")


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.sent: list = []
        self.file_bytes = b""

    async def make_request(self, bot, method, timeout=None):
        self.sent.append(method)
        if isinstance(method, GetFile):
            return File(file_id="f1", file_unique_id="u1", file_path="docs/file.bin", file_size=len(self.file_bytes))
        if isinstance(method, (SendMessage, EditMessageText)):
            return Message(message_id=len(self.sent), date=datetime.datetime.now(), chat=CHAT,
                           text=method.text).as_(bot)
        if getattr(method, "__returning__", None) is bool:
            return True
        return Message(message_id=len(self.sent), date=datetime.datetime.now(), chat=CHAT, text="ok").as_(bot)

    async def stream_content(self, *args, **kwargs):
        yield self.file_bytes

    async def close(self):
        pass

    def texts(self) -> str:
        return "\n".join(m.text for m in self.sent if isinstance(m, (SendMessage, EditMessageText)))

    def last_markup(self):
        for method in reversed(self.sent):
            if isinstance(method, (SendMessage, EditMessageText)) and method.reply_markup is not None \
                    and hasattr(method.reply_markup, "inline_keyboard"):
                return method.reply_markup
        return None

    def buttons(self) -> list[str]:
        markup = self.last_markup()
        return [b.callback_data for row in markup.inline_keyboard for b in row] if markup else []

    def documents(self) -> list:
        return [m for m in self.sent if isinstance(m, SendDocument)]


@pytest.fixture(scope="module")
def dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    return dp


class Client:
    """Drives the bot like a user: text, button taps, files."""

    def __init__(self, dispatcher: Dispatcher, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("SMETA_FREE_ESTIMATES", "100")
        monkeypatch.delenv("SMETA_PAYMENT_TOKEN", raising=False)
        self.session = FakeSession()
        self.bot = Bot("42:TEST", session=self.session, default=DefaultBotProperties(parse_mode="HTML"))
        self.deps = Deps(store=Store(tmp_path / "s.db"), catalog=Catalog.load(),
                         offers=OfferBook.load("data/suppliers/demo.csv"), export_dir=tmp_path / "e",
                         logo_dir=tmp_path / "logos")
        self.dp = dispatcher
        self.mid = 0

    async def feed(self, payload: dict) -> None:
        self.mid += 1
        payload["update_id"] = self.mid
        await self.dp.feed_update(self.bot, Update.model_validate(payload, context={"bot": self.bot}), deps=self.deps)

    async def say(self, text: str) -> None:
        msg = Message(message_id=self.mid + 1, date=datetime.datetime.now(), chat=CHAT, from_user=USER, text=text)
        await self.feed({"message": msg.model_dump()})

    async def tap(self, data: str) -> None:
        carrier = Message(message_id=900, date=datetime.datetime.now(), chat=CHAT, text="экран")
        query = CallbackQuery(id=str(self.mid), from_user=USER, chat_instance="c", message=carrier, data=data)
        await self.feed({"callback_query": query.model_dump()})

    async def upload(self, path: Path, size: int | None = None) -> None:
        self.session.file_bytes = path.read_bytes() if path.exists() else b""
        doc = Document(file_id="f1", file_unique_id="u1", file_name=path.name, file_size=size or len(self.session.file_bytes))
        msg = Message(message_id=self.mid + 1, date=datetime.datetime.now(), chat=CHAT, from_user=USER, document=doc)
        await self.feed({"message": msg.model_dump()})

    def estimate(self):
        settings = self.deps.store.settings(USER.id)
        return self.deps.store.load_estimate(USER.id, settings["current_id"])

    async def close(self):
        self.deps.store.close()
        await self.bot.session.close()


# ---------------------------------------------------------------- every screen has a way back


def test_every_screen_has_back_and_menu(tmp_path):
    deps = Deps(store=Store(tmp_path / "s.db"), catalog=Catalog.load(), offers=OfferBook(), export_dir=tmp_path)
    from smeta.context import new_estimate
    from smeta.builder import build_from_text

    estimate_id, estimate = new_estimate(deps, USER.id)
    for match in build_from_text("штукатурка стен 120 м2\nмат: керамогранит 22 м2 1550", deps.catalog):
        estimate.add(match.position)
    deps.store.save_estimate(USER.id, estimate, estimate_id)
    deps.store.save_version(USER.id, estimate_id, estimate)
    ctx = Ctx(deps=deps, tg_id=USER.id, data={
        "rooms": [{"name": "Кухня", "length": "4", "width": "3", "height": "2.7", "doors": 1, "windows": 1}],
        "pending_tpl": {"code": "cosmetic", "vars": {k: "10" for k in "SCPHWRNDOLK"}, "notes": []},
        "pending_rep": {"index": 2},
    })
    screens = ["est", "items:0", "pos:1", "cut", "coef", "pcoef:1", "lim", "mat", "docs", "prog", "pick:0",
               "sched", "acts", "stat", "ver", "vd:1", "rep", "reppv", "crew", "profit", "obm", "obmw", "tpl",
               "tpl1:capital", "tplp", "aud", "tax", "co", "refs", "idx:0", "sub", "list:0", "stats", "help"]
    assert set(name.split(":")[0] for name in screens) == set(ui.SCREENS) - {"home"}
    for screen in screens:
        text, markup = ui.render_screen(screen, ctx)
        data = [button.callback_data for row in markup.inline_keyboard for button in row]
        assert text, screen
        assert "bk" in data and "hm" in data, f"{screen}: нет кнопок «Назад» и «Меню»"
        assert all(len(item.encode()) <= 64 for item in data), screen
    text, markup = ui.render_screen("home", ctx)
    assert "bk" not in [b.callback_data for row in markup.inline_keyboard for b in row]
    for kind in ui.WIZARDS:
        for step in range(len(ui.WIZARDS[kind])):
            _, markup = ui.wizard_prompt(kind, step)
            data = [b.callback_data for row in markup.inline_keyboard for b in row]
            assert "ib" in data and "hm" in data, f"мастер {kind} шаг {step}"
    deps.store.close()


# ---------------------------------------------------------------- main flow


async def test_full_flow(tmp_path: Path, dispatcher: Dispatcher, monkeypatch):
    c = Client(dispatcher, tmp_path, monkeypatch)
    await c.say("/start")
    assert "Главное меню" in c.session.texts()
    assert "a:new" in c.session.buttons()

    # реквизиты: мастер с шагом назад посередине
    await c.tap("go:co")
    await c.tap("a:ask:company")
    await c.say("ООО «Ошибка»")
    await c.tap("ib")                                   # назад на шаг 1
    assert "Шаг 1 из 7" in c.session.texts().split("\n")[-2] or "Шаг 1 из 7" in c.session.texts()
    await c.say("ООО «СтройПро»")
    await c.say("1234567890")                           # неверный ИНН - бот переспрашивает
    assert "контрольной сумме" in c.session.texts()
    await c.say("7707083893")
    await c.tap("is")                                   # КПП пропущен
    for answer in ["г. Москва", "+7 999 000-00-00", "-", "Директор Иванов И.И."]:
        await c.say(answer)
    company = c.deps.store.company(USER.id)
    assert company.name == "ООО «СтройПро»" and company.inn == "7707083893" and company.kpp == ""
    assert company.signer == "Иванов И.И."

    # новая смета мастером
    await c.tap("hm")
    await c.tap("a:new")
    await c.say("г. Москва, ул. Ленина, 5")
    await c.say("ООО «Ромашка»")
    await c.tap("is")
    estimate = c.estimate()
    assert estimate.object_name.startswith("г. Москва") and estimate.customer == "ООО «Ромашка»"

    # работы текстом
    await c.say("штукатурка стен 120 м2\nстяжка пола 85 м2 по 700\nмат: керамогранит 22 м2\nподшив сайдингом 30 м2")
    estimate = c.estimate()
    assert len(estimate.positions) == 4
    assert estimate.positions[2].unit_price == 1550
    assert "go:items:0" in c.session.buttons()

    # карточка позиции → цена → назад к карточке
    await c.tap("go:items:0")
    await c.tap("go:pos:4")
    await c.tap("a:ask:price:4")
    await c.say("900")
    assert c.estimate().positions[3].unit_price == 900
    assert "Подшив сайдингом" in c.session.texts()

    # скидка кнопкой, подгон мастером, сброс
    await c.tap("go:cut")
    before = c.estimate().total()
    await c.tap("a:cut:-20")
    assert c.estimate().total() < before
    await c.tap("a:ask:fit")
    await c.say("450000")
    assert c.estimate().total() == 450000
    await c.tap("a:reset")
    assert c.estimate().total() == before

    # «Назад» идёт ровно по пути, которым пришли: скидка → карточка → список → смета
    await c.tap("bk")
    assert "a:ask:qty:4" in c.session.buttons()
    await c.tap("bk")
    assert "go:pos:1" in c.session.buttons()
    await c.tap("bk")
    assert "a:ask:works" in c.session.buttons()

    # коэффициент и лимитированные
    await c.tap("go:coef")
    await c.tap("a:coef:stesn")
    assert any(p.k_basis for p in c.estimate().positions)
    await c.tap("go:lim")
    await c.tap("a:lim:vzis")
    assert c.estimate().limited and c.estimate().totals().limited_total > 0

    # материалы по нормам
    await c.tap("go:mat")
    await c.tap("a:mat")
    assert any(p.source == "нормы расхода" for p in c.estimate().positions)

    # документы
    await c.tap("go:docs")
    for kind in ("xlsx", "pdf", "kp", "margin"):
        await c.tap(f"a:doc:{kind}")
    await c.tap("go:crew")
    await c.tap("a:crewpct:40")
    await c.tap("a:doc:naryad")
    assert len(c.session.documents()) == 5

    # выполнение → КС-2/КС-3, оплата, график
    await c.tap("go:prog")
    await c.tap("go:pick:0")
    await c.tap("a:ask:done:1")
    await c.tap("iv:всё")
    assert c.estimate().positions[0].done == c.estimate().positions[0].qty
    await c.tap("a:act")
    assert len(c.estimate().acts) == 1 and len(c.session.documents()) == 7
    await c.tap("a:ask:pay")
    await c.say("100000")
    await c.tap("is")
    assert c.estimate().payments
    await c.tap("a:sched:30/70")
    assert len(c.estimate().schedule) == 2

    # версии и допсоглашение
    await c.tap("go:ver")
    await c.tap("a:ver_save")
    await c.say("плинтус 40 м")
    await c.tap("go:vd:1")
    assert "Добавлено" in c.session.texts()
    await c.tap("a:ds:1")
    assert len(c.session.documents()) == 8

    # статус «отправлено» → напоминание через 3 дня
    await c.tap("go:stat")
    await c.tap("a:status:sent")
    assert c.estimate().status == "sent"
    later = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=4)
    assert await run_reminders(c.bot, c.deps, later) == 1
    assert "ответа нет" in c.session.texts()
    estimate_id = c.deps.store.settings(USER.id)["current_id"]
    await c.tap(f"a:rs:{estimate_id}:agreed")
    assert c.estimate().status == "agreed"

    # пересчёт по индексу: предпросмотр → применить
    await c.tap("go:rep")
    await c.tap("a:rep:2")
    assert "Было" in c.session.texts()
    old_total = c.estimate().total()
    await c.tap("a:rep_apply")
    assert c.estimate().total() != old_total

    # налоги и обратный расчёт
    await c.tap("go:tax")
    assert "Выгоднее всего" in c.session.texts()
    await c.tap("a:ask:tax_target")
    await c.say("300000")
    assert "ставить в смету" in c.session.texts()

    # воронка
    await c.tap("go:stats")
    assert "Воронка" in c.session.texts()
    await c.close()


async def test_obmer_and_template(tmp_path: Path, dispatcher: Dispatcher, monkeypatch):
    c = Client(dispatcher, tmp_path, monkeypatch)
    await c.say("/start")
    await c.tap("go:obm")
    await c.tap("a:ask:room")
    await c.say("кухня 4,2 3,1 2,7 д1 о1")
    await c.tap("a:ask:room")
    await c.say("спальня 4 3,5 2,7")
    assert "Итого по 2 пом." in c.session.texts()
    await c.tap("go:obmw")
    await c.tap("a:obmt:plaster")
    await c.tap("a:obmt:laminate")
    await c.tap("a:obm_add")
    estimate = c.estimate()
    assert len(estimate.positions) == 2
    assert estimate.positions[1].qty == Decimal("27.02")             # 13,02 + 14 м² пола

    # шаблон: мастер с кнопками быстрых ответов → предпросмотр → новой сметой
    await c.tap("go:tpl")
    await c.tap("go:tpl1:capital")
    await c.tap("a:ask:tpl:capital")
    await c.say("56")
    await c.tap("iv:2.7")
    await c.tap("iv:2")
    await c.tap("iv:1")
    await c.tap("is")                                   # периметр оценит сам
    assert "предварительно" in c.session.texts()
    await c.tap("a:tpl_new")
    assert len(c.estimate().positions) > 15
    await c.close()


async def test_import_audit_index(tmp_path: Path, dispatcher: Dispatcher, monkeypatch):
    from openpyxl import Workbook

    from tests.test_smeta_import import fsnb_xlsx, indices_xlsx

    c = Client(dispatcher, tmp_path, monkeypatch)
    await c.say("/start")
    await c.tap("go:refs")
    await c.tap("a:ask:import")
    await c.upload(fsnb_xlsx(tmp_path / "ФСНБ-2022_сборник15.xlsx"))
    assert "Импорт расценок: 3" in c.session.texts()
    await c.upload(indices_xlsx(tmp_path / "индексы_IV_кв_2026.xlsx"))
    assert "Импорт индексов: 2" in c.session.texts()

    await c.say("штукатурка стен 120 м2")
    assert c.estimate().positions[0].code == "ФЕР15-02-016-03"
    names = list(c.deps.store.catalog(USER.id, c.deps.catalog).indices)
    number = next(i for i, name in enumerate(names, 1) if name.startswith("Московская область"))
    await c.tap(f"a:idx:{number}")
    assert c.estimate().indices.ot == Decimal("1.38")

    # проверка чужой сметы файлом
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["№", "Наименование работ", "Ед. изм.", "Кол-во", "Цена", "Сумма"])
    sheet.append([1, "Штукатурка стен", "м2", 100, 5000, 400000])
    sheet.append([None, "Итого", None, None, None, 400000])
    path = tmp_path / "чужая.xlsx"
    workbook.save(path)
    await c.tap("go:aud")
    await c.tap("a:ask:audit")
    await c.upload(path)
    assert "арифметика" in c.session.texts()
    assert c.session.documents()

    # большой файл - подсказка про сервер
    await c.upload(tmp_path / "ФСНБ.zip", size=40 * 1024 * 1024)
    assert "smeta.fgis load" in c.session.texts()
    await c.close()


async def test_paywall_and_payment(tmp_path: Path, dispatcher: Dispatcher, monkeypatch):
    c = Client(dispatcher, tmp_path, monkeypatch)
    monkeypatch.setenv("SMETA_FREE_ESTIMATES", "1")
    monkeypatch.delenv("SMETA_ADMIN_IDS", raising=False)
    monkeypatch.delenv("ADMIN_IDS", raising=False)
    await c.say("/start")
    await c.say("штукатурка стен 10 м2")                # первая смета бесплатно
    assert c.estimate() is not None
    await c.tap("a:new")
    assert "закончились" in c.session.texts()
    await c.tap("a:buy:month")
    invoice = [m for m in c.session.sent if isinstance(m, SendInvoice)][-1]
    assert invoice.currency == "XTR" and invoice.payload == "sub:month"

    query = PreCheckoutQuery(id="q1", from_user=USER, currency="XTR", total_amount=500, invoice_payload="sub:month")
    await c.feed({"pre_checkout_query": query.model_dump()})
    payment = SuccessfulPayment(currency="XTR", total_amount=500, invoice_payload="sub:month",
                                telegram_payment_charge_id="ch1", provider_payment_charge_id="p1")
    msg = Message(message_id=500, date=datetime.datetime.now(), chat=CHAT, from_user=USER, successful_payment=payment)
    await c.feed({"message": msg.model_dump()})
    assert "Подписка активна" in c.session.texts()
    await c.feed({"message": msg.model_dump()})         # повторная доставка не продлевает дважды
    until = c.deps.store.paid_until(USER.id)
    assert 29 <= (until - datetime.datetime.now(datetime.timezone.utc)).days <= 30
    await c.tap("a:new")
    assert "Шаг 1 из 3" in c.session.texts()

    monkeypatch.setenv("SMETA_PROMO", "START:14")
    await c.tap("go:sub")
    await c.tap("a:ask:promo")
    await c.say("start")
    assert "+14 дн." in c.session.texts()
    await c.close()


async def test_legacy_commands_still_work(tmp_path: Path, dispatcher: Dispatcher, monkeypatch):
    c = Client(dispatcher, tmp_path, monkeypatch)
    await c.say("покраска стен 50 м2")
    assert c.estimate().positions[0].code == "ДЕМО-03.06"
    await c.say("/cut 10")
    await c.say("/price 1 700")
    assert c.estimate().positions[0].unit_price == 700
    await c.say("/vat 0")
    assert c.estimate().vat_pct == 0
    await c.say("/xlsx")
    await c.say("/nalog 18000000 ип")
    assert c.deps.store.settings(USER.id)["tax_ip"]
    await c.say("/del 1")
    assert not c.estimate().positions
    await c.say(ui.MENU_TEXT)
    assert "Главное меню" in c.session.texts()
    await c.close()
