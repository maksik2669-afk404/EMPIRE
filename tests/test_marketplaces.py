import json

import httpx
import pytest

from app.marketplaces import AuthError, MarketplaceError, make_client, parse_credentials
from app.marketplaces import base


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    async def _sleep(_):
        return None
    monkeypatch.setattr(base.asyncio, "sleep", _sleep)


def recorder(routes):
    """routes: {(method, path): json or callable(request)->Response}. Returns (client, calls)."""
    calls = []

    def handler(request: httpx.Request):
        calls.append(request)
        r = routes[(request.method, request.url.path)]
        return r(request) if callable(r) else httpx.Response(200, json=r)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler)), calls


async def test_wildberries_fetch_and_reply():
    http, calls = recorder({
        ("GET", "/api/v1/feedbacks"): {"data": {"feedbacks": [{
            "id": "fb1", "text": "Норм", "pros": "дешево", "cons": "", "productValuation": 4,
            "productDetails": {"nmId": 123, "productName": "Кружка"}, "userName": "Иван"}]}, "error": False},
        ("GET", "/api/v1/questions"): {"data": {"questions": [{
            "id": "q1", "text": "Размер?", "productDetails": {"nmId": 123, "productName": "Кружка"}}]}},
        ("POST", "/api/v1/feedbacks/answer"): {},
        ("PATCH", "/api/v1/questions"): {"data": None, "error": False},
    })
    c = make_client("wildberries", {"token": "T" * 30}, http)
    items = await c.fetch_new(20)
    assert [(i.kind, i.external_id, i.rating, i.sku) for i in items] == [("review", "fb1", 4, "123"), ("question", "q1", None, "123")]
    assert items[0].text == "Норм\nДостоинства: дешево"
    assert "Иван" not in items[0].text  # buyer names are not collected
    assert calls[0].headers["Authorization"] == "T" * 30
    assert calls[0].url.params["isAnswered"] == "false" and calls[0].url.params["take"] == "20"

    await c.reply("review", "fb1", "Спасибо!", {})
    await c.reply("question", "q1", "42", {})
    assert json.loads(calls[-2].content) == {"id": "fb1", "text": "Спасибо!"}
    assert json.loads(calls[-1].content) == {"id": "q1", "answer": {"text": "42"}, "state": "wbRu"}


async def test_ozon_fetch_and_reply():
    http, calls = recorder({
        ("POST", "/v1/review/list"): {"reviews": [{"id": "r1", "sku": 555, "text": "Супер", "rating": 5}], "has_next": False},
        ("POST", "/v1/question/list"): {"questions": [{"id": "q9", "sku": 555, "text": "Есть синий?"}], "last_id": ""},
        ("POST", "/v1/review/comment/create"): {"comment_id": "c1"},
        ("POST", "/v1/question/answer/create"): {"answer_id": "a1"},
    })
    c = make_client("ozon", {"client_id": "123", "api_key": "k"}, http)
    items = await c.fetch_new(10)
    assert [(i.kind, i.external_id) for i in items] == [("review", "r1"), ("question", "q9")]
    assert calls[0].headers["Client-Id"] == "123" and calls[0].headers["Api-Key"] == "k"
    assert json.loads(calls[0].content)["limit"] == 20  # Ozon minimum
    await c.reply("review", "r1", "Спасибо", {})
    await c.reply("question", "q9", "Да", items[1].extra)
    assert json.loads(calls[-2].content) == {"review_id": "r1", "text": "Спасибо", "mark_review_as_processed": True}
    assert json.loads(calls[-1].content) == {"question_id": "q9", "sku": 555, "text": "Да"}


async def test_ozon_without_premium_explains():
    http, _ = recorder({("POST", "/v1/review/list"): lambda r: httpx.Response(403, json={"message": "no access"})})
    with pytest.raises(AuthError, match="Premium"):
        await make_client("ozon", {"client_id": "1", "api_key": "k"}, http).check()


async def test_yandex_market_fetch_and_reply():
    http, calls = recorder({
        ("POST", "/businesses/777/goods-feedback"): {"status": "OK", "result": {"feedbacks": [{
            "feedbackId": 42, "description": {"comment": "Ок", "disadvantages": "шумит"},
            "statistics": {"rating": 3}, "identifiers": {"offerId": "SKU-1"}}]}},
        ("POST", "/businesses/777/goods-feedback/comments/update"): {"status": "OK"},
    })
    c = make_client("yandex_market", {"api_key": "ym", "business_id": "777"}, http)
    items = await c.fetch_new(10)
    assert (items[0].external_id, items[0].rating, items[0].sku) == ("42", 3, "SKU-1")
    assert items[0].text == "Ок\nНедостатки: шумит"
    assert calls[0].headers["Api-Key"] == "ym"
    assert json.loads(calls[0].content) == {"reactionStatus": "NEED_REACTION"}
    await c.reply("review", "42", "Спасибо", {})
    assert json.loads(calls[-1].content) == {"feedbackId": 42, "comment": {"text": "Спасибо"}}


async def test_retry_on_429_then_success():
    state = {"n": 0}

    def flaky(request):
        state["n"] += 1
        return httpx.Response(429) if state["n"] == 1 else httpx.Response(200, json={"data": {}})

    http, _ = recorder({("GET", "/api/v1/feedbacks"): flaky})
    await make_client("wildberries", {"token": "x" * 30}, http).check()
    assert state["n"] == 2


async def test_errors_are_mapped():
    http, _ = recorder({("GET", "/api/v1/feedbacks"): lambda r: httpx.Response(401, json={"title": "unauthorized"})})
    with pytest.raises(AuthError):
        await make_client("wildberries", {"token": "x" * 30}, http).check()
    http, _ = recorder({("GET", "/api/v1/feedbacks"): lambda r: httpx.Response(400, json={"errorText": "bad"})})
    with pytest.raises(MarketplaceError, match="bad"):
        await make_client("wildberries", {"token": "x" * 30}, http).check()


def test_parse_credentials():
    assert parse_credentials("wildberries", " " + "a" * 40 + "\n") == {"token": "a" * 40}
    assert parse_credentials("ozon", "12345\nkey-abc") == {"client_id": "12345", "api_key": "key-abc"}
    assert parse_credentials("yandex_market", "ACMA:key 999") == {"api_key": "ACMA:key", "business_id": "999"}
    assert parse_credentials("yandex_market", "999 ACMA:key") == {"api_key": "ACMA:key", "business_id": "999"}
    for mp, raw in [("wildberries", "short"), ("ozon", "abc key"), ("ozon", "onlyone"), ("yandex_market", "a b")]:
        with pytest.raises(ValueError):
            parse_credentials(mp, raw)
