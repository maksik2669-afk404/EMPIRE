"""Sales bot end to end with a fake Telegram: deep link -> invoice in Stars -> payment -> link, plus admin tools."""
import datetime

from aiogram import Bot, Dispatcher
from aiogram.methods import AnswerPreCheckoutQuery, RefundStarPayment, SendInvoice, SendMessage, SendVideo
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery, SuccessfulPayment, Update

from salesbot.bot import PAYLOAD, Config, Store, router
from tests.test_bot_flow import CHAT, USER, FakeSession

ADMIN = 7
BOTS: list = []


def upd(uid: int, **kw) -> Update:
    return Update.model_validate({"update_id": uid, **kw}, context={"bot": BOTS[0]})


def msg(text: str, uid: int, **extra) -> Update:
    m = Message(message_id=uid, date=datetime.datetime.now(), chat=CHAT, from_user=USER, text=text, **extra)
    return upd(uid, message=m.model_dump())


def setup(price=149, video=""):
    session = FakeSession()
    bot = Bot("123456:" + "A" * 35, session=session)
    BOTS[:] = [bot]
    cfg = Config(token="x", table_url="https://docs.google.com/spreadsheets/d/T/copy", price=price,
                 admins=frozenset({ADMIN}), db_path=":memory:", welcome_video=video, support="@help")
    store = Store(":memory:")
    dp = Dispatcher(store=store, cfg=cfg)
    router._parent_router = None  # module-level router: detach from the previous test's dispatcher
    dp.include_router(router)
    return session, bot, dp, store, cfg


def sent(session, cls):
    return [m for m in session.sent if isinstance(m, cls)]


async def test_purchase_flow():
    session, bot, dp, store, cfg = setup(video="https://cdn.example/reel01.mp4")
    await dp.feed_update(bot, msg("/start reel01", 1))
    assert store.source(USER.id) == "reel01"
    assert sent(session, SendVideo)[0].caption.count("149 ⭐") == 1  # the reel works as the welcome screen

    cbq = CallbackQuery(id="1", from_user=USER, chat_instance="c", data="buy",
                        message=Message(message_id=5, date=datetime.datetime.now(), chat=CHAT, text="x"))
    await dp.feed_update(bot, upd(2, callback_query=cbq.model_dump()))
    inv = sent(session, SendInvoice)[0]
    assert inv.currency == "XTR" and inv.prices[0].amount == 149 and inv.payload == PAYLOAD

    q = PreCheckoutQuery(id="pc", from_user=USER, currency="XTR", total_amount=149, invoice_payload=PAYLOAD)
    await dp.feed_update(bot, upd(3, pre_checkout_query=q.model_dump()))
    assert sent(session, AnswerPreCheckoutQuery)[-1].ok is True
    bad = PreCheckoutQuery(id="pc2", from_user=USER, currency="XTR", total_amount=99, invoice_payload=PAYLOAD)
    await dp.feed_update(bot, upd(4, pre_checkout_query=bad.model_dump()))
    assert sent(session, AnswerPreCheckoutQuery)[-1].ok is False  # stale price is rejected

    pay = SuccessfulPayment(currency="XTR", total_amount=149, invoice_payload=PAYLOAD,
                            telegram_payment_charge_id="ch_1", provider_payment_charge_id="")
    await dp.feed_update(bot, msg(None, 5, successful_payment=pay))
    assert store.has_access(USER.id)
    access = [m for m in sent(session, SendMessage) if m.chat_id == CHAT.id][-1]
    assert access.reply_markup.inline_keyboard[0][0].url == cfg.table_url
    assert any(m.chat_id == ADMIN and "reel01" in m.text for m in sent(session, SendMessage))  # sale alert

    await dp.feed_update(bot, msg(None, 6, successful_payment=pay))  # duplicate update: no second alert
    assert sum(m.chat_id == ADMIN for m in sent(session, SendMessage)) == 1

    await dp.feed_update(bot, msg("/start", 7))  # returning buyer gets the link, not the pitch
    assert sent(session, SendMessage)[-1].reply_markup.inline_keyboard[0][0].url == cfg.table_url


async def test_admin_tools_and_access_rules():
    session, bot, dp, store, cfg = setup()
    await dp.feed_update(bot, msg("/start", 1))
    assert "149 ⭐" in sent(session, SendMessage)[-1].text  # no video configured -> text
    await dp.feed_update(bot, msg("/stats", 2))  # not an admin -> silence
    assert "Статистика" not in sent(session, SendMessage)[-1].text
    await dp.feed_update(bot, msg("/mytable", 3))
    assert "Доступа пока нет" in sent(session, SendMessage)[-1].text

    store.add_purchase("ch_9", USER.id, 149, "XTR")
    admin = USER.model_copy(update={"id": ADMIN})
    as_admin = lambda text, uid: upd(uid, message=Message(  # noqa: E731
        message_id=uid, date=datetime.datetime.now(), chat=CHAT, from_user=admin, text=text).model_dump())

    await dp.feed_update(bot, as_admin("/stats", 4))
    assert "Покупателей: 1" in sent(session, SendMessage)[-1].text and "149 ⭐" in sent(session, SendMessage)[-1].text
    await dp.feed_update(bot, as_admin(f"/refund {USER.id}", 5))
    r = sent(session, RefundStarPayment)[-1]
    assert (r.user_id, r.telegram_payment_charge_id) == (USER.id, "ch_9") and not store.has_access(USER.id)
    await dp.feed_update(bot, as_admin(f"/give {USER.id}", 6))
    assert store.has_access(USER.id)
    await dp.feed_update(bot, as_admin("/broadcast Winter arc стартует завтра", 7))
    assert "доставлено 1" in sent(session, SendMessage)[-1].text
    for cmd in ("/terms", "/paysupport"):
        await dp.feed_update(bot, msg(cmd, 8))
    assert "@help" in sent(session, SendMessage)[-1].text
