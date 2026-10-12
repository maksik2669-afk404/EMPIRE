"""Mini App API: Telegram signature checks, ownership, every route."""
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiohttp.test_utils import TestClient, TestServer

from smeta.catalog import Catalog
from smeta.context import Deps
from smeta.materials import OfferBook
from smeta.store import Store
from smeta.webapp import create_app
from tests.test_smeta_bot import FakeSession

TOKEN = "42:TEST-TOKEN"


def init_data(user_id: int, *, token: str = TOKEN, auth_date: int | None = None) -> str:
    """Signed exactly as Telegram does it (HMAC-SHA256 with key HMAC('WebAppData', token))."""
    fields = {
        "query_id": "AAH",
        "user": json.dumps({"id": user_id, "first_name": "Игорь"}, ensure_ascii=False, separators=(",", ":")),
        "auth_date": str(auth_date or int(time.time())),
    }
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


@pytest.fixture
async def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SMETA_FREE_ESTIMATES", "100")
    session = FakeSession()
    bot = Bot(TOKEN, session=session, default=DefaultBotProperties(parse_mode="HTML"))
    deps = Deps(store=Store(tmp_path / "w.db"), catalog=Catalog.load(), offers=OfferBook.load("data/suppliers/demo.csv"),
                export_dir=tmp_path / "e", logo_dir=tmp_path / "l")
    app = create_app(deps, bot, TOKEN)
    async with TestClient(TestServer(app)) as test_client:
        test_client.session_fake = session
        yield test_client
    deps.store.close()
    await bot.session.close()


async def call(client, path, body=None, user=1, data=None):
    headers = {"X-Init-Data": data if data is not None else init_data(user)}
    response = await client.post(path, json=body or {}, headers=headers)
    return response.status, await response.json()


async def test_page_is_served(client):
    response = await client.get("/")
    text = await response.text()
    assert response.status == 200 and "telegram-web-app.js" in text and "BackButton" in text
    assert (await client.get("/health")).status == 200


@pytest.mark.parametrize("data,reason", [
    ("", "из Телеграма"),
    (init_data(1, token="99:OTHER"), "подпись"),
    (init_data(1, auth_date=int(time.time()) - 3 * 24 * 3600), "устарела"),
    ("user=%7B%22id%22%3A1%7D&hash=deadbeef", "подпись"),
])
async def test_bad_signatures_are_rejected(client, data, reason):
    status, body = await call(client, "/api/state", data=data)
    assert status == 401 and reason in body["error"]


async def test_full_api_flow(client):
    status, state = await call(client, "/api/state")
    assert status == 200 and state["estimates"] == [] and state["templates"]

    status, estimate = await call(client, "/api/estimates", {"object": "ул. Ленина 5", "customer": "ООО Ромашка"})
    assert status == 200 and estimate["number"].startswith("СМ-")
    eid = estimate["id"]

    status, estimate = await call(client, f"/api/estimates/{eid}/works",
                                  {"text": "штукатурка стен 120 м2\nподшив сайдингом 30 м2\nмат: керамогранит 22 м2"})
    assert len(estimate["positions"]) == 3
    assert [m["status"] for m in estimate["matches"]] == ["matched", "needs_price", "price_list"]
    assert estimate["positions"][1]["needs_price"]

    status, estimate = await call(client, f"/api/estimates/{eid}/positions/2", {"price": "900"})
    assert estimate["positions"][1]["price"] == 900
    status, error = await call(client, f"/api/estimates/{eid}/positions/2", {"qty": "-5"})
    assert status == 400
    status, estimate = await call(client, f"/api/estimates/{eid}/positions/1", {"done": "50%", "crew_price": "450"})
    assert estimate["positions"][0]["done"] == 60 and estimate["positions"][0]["crew_price"] == 450

    before = estimate["totals"]["total"]
    status, estimate = await call(client, f"/api/estimates/{eid}/adjust", {"percent": -10})
    assert estimate["totals"]["total"] < before and estimate["discount"] == -10
    status, estimate = await call(client, f"/api/estimates/{eid}/adjust", {"fit": "300000"})
    assert estimate["totals"]["total"] == 300000
    status, estimate = await call(client, f"/api/estimates/{eid}/adjust", {"reset": True})
    assert estimate["totals"]["total"] == before

    status, estimate = await call(client, f"/api/estimates/{eid}/materials")
    assert any(p["name"].startswith("Штукатурка гипсовая") for p in estimate["positions"])

    status, estimate = await call(client, f"/api/estimates/{eid}/status", {"status": "sent"})
    assert estimate["status"] == "sent"

    for kind in ("xlsx", "pdf", "kp", "naryad", "margin"):
        status, result = await call(client, f"/api/estimates/{eid}/document", {"kind": kind})
        assert status == 200 and result["ok"], kind
    sent = [m for m in client.session_fake.sent if type(m).__name__ == "SendDocument"]
    assert len(sent) == 5 and all(m.chat_id == 1 for m in sent)

    status, estimate = await call(client, f"/api/estimates/{eid}/positions/2", {"delete": True})
    assert len(estimate["positions"]) == len([p for p in estimate["positions"]])


async def test_other_users_estimates_are_invisible(client):
    _, estimate = await call(client, "/api/estimates", {}, user=1)
    status, body = await call(client, f"/api/estimates/{estimate['id']}", user=2)
    assert status == 404
    status, body = await call(client, f"/api/estimates/{estimate['id']}/works", {"text": "штукатурка 10 м2"}, user=2)
    assert status == 404
    status, body = await call(client, f"/api/estimates/{estimate['id']}/document", {"kind": "xlsx"}, user=2)
    assert status == 404


async def test_obmer_templates_tax_rates(client):
    rooms = [{"name": "Кухня", "length": "4.2", "width": "3.1", "height": "2.7", "doors": 1, "windows": 1},
             {"name": "Спальня", "length": "4", "width": "3.5", "height": "2.7", "doors": 1, "windows": 1}]
    status, result = await call(client, "/api/obmer", {"rooms": rooms})
    assert result["summary"]["S"] == 27.02
    status, error = await call(client, "/api/obmer", {"rooms": [{"length": "x"}]})
    assert status == 400
    status, estimate = await call(client, "/api/obmer/apply", {"rooms": rooms, "works": ["laminate", "plaster"], "new": True})
    assert len(estimate["positions"]) == 2

    params = {"code": "capital", "area": "56", "height": "2.7", "rooms": "2", "baths": "1"}
    status, preview = await call(client, "/api/templates/preview", params)
    assert preview["total"] > 0 and len(preview["positions"]) > 15 and preview["notes"]
    status, estimate = await call(client, "/api/templates/apply", {**params, "estimate_id": estimate["id"]})
    assert len(estimate["positions"]) > 17

    status, taxes = await call(client, "/api/tax", {"estimate_id": estimate["id"], "ip": False, "staff": True})
    assert status == 200 and taxes["results"][0]["net"] > 0
    status, taxes = await call(client, "/api/tax", {"revenue": "1000000", "materials": "300000", "payroll": "200000"})
    assert {r["regime"] for r in taxes["results"]} >= {"usn6", "usn15", "osno_ooo"}
    status, target = await call(client, "/api/tax/target", {"revenue": "1000000", "materials": "300000", "net": "200000"})
    assert all(r["revenue"] > 0 for r in target["results"] if not r["blocked"])
    status, error = await call(client, "/api/tax", {})
    assert status == 400

    status, rates = await call(client, "/api/rates", {"q": "плитка"})
    assert rates["results"]


async def test_paywall_in_webapp(client, monkeypatch):
    monkeypatch.setenv("SMETA_FREE_ESTIMATES", "1")
    monkeypatch.delenv("SMETA_ADMIN_IDS", raising=False)
    monkeypatch.delenv("ADMIN_IDS", raising=False)
    assert (await call(client, "/api/estimates", {}, user=7))[0] == 200
    status, body = await call(client, "/api/estimates", {}, user=7)
    assert status == 402 and "подписку" in body["error"]
