import asyncio
import socket

from aiohttp import web

from app import netcheck
from app.main import resolve_telegram_route


async def test_order_system_proxy_and_local_ports(monkeypatch):
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen()
    port = srv.getsockname()[1]
    monkeypatch.setattr(netcheck, "LOCAL_PORTS", (1, port))  # port 1 is closed
    monkeypatch.setattr(netcheck, "getproxies", lambda: {"https": "https://127.0.0.1:10809", "http": "127.0.0.1:10809"})
    got = list(netcheck.candidates("socks5h://10.0.0.1:1080"))
    srv.close()
    assert got == ["socks5://10.0.0.1:1080", "", "http://127.0.0.1:10809",
                   f"socks5://127.0.0.1:{port}", f"http://127.0.0.1:{port}"]


async def test_find_route_picks_first_working(monkeypatch):
    monkeypatch.setattr(netcheck, "getproxies", lambda: {"http": "http://127.0.0.1:7890"})
    monkeypatch.setattr(netcheck, "LOCAL_PORTS", ())
    tried = []

    async def fake_probe(token, proxy):
        tried.append(proxy)
        return proxy == "http://127.0.0.1:7890"

    assert await netcheck.find_route("t", "", fake_probe) == "http://127.0.0.1:7890"
    assert tried == [None, "http://127.0.0.1:7890"]  # direct first


async def _connect_proxy(reader, writer):
    """Minimal HTTP CONNECT proxy, like the local port of a VPN client."""
    line = await reader.readline()
    host, port = line.split()[1].decode().rsplit(":", 1)
    while (await reader.readline()) not in (b"\r\n", b""):
        pass
    r2, w2 = await asyncio.open_connection(host, int(port))
    writer.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
    await writer.drain()

    async def pipe(a, b):
        try:
            while data := await a.read(65536):
                b.write(data)
                await b.drain()
        finally:
            b.close()

    await asyncio.gather(pipe(reader, w2), pipe(r2, writer), return_exceptions=True)


async def test_real_probe_direct_and_through_http_proxy(tmp_path, monkeypatch):
    app = web.Application()
    async def get_me(request):
        return web.json_response({"ok": True})

    app.router.add_get("/bot{token}/getMe", get_me)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    api = f"http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}"
    proxy_srv = await asyncio.start_server(_connect_proxy, "127.0.0.1", 0)
    proxy = f"http://127.0.0.1:{proxy_srv.sockets[0].getsockname()[1]}"
    try:
        assert await netcheck.probe("1:x", None, api=api)
        assert await netcheck.probe("1:x", proxy, api=api)
        assert not await netcheck.probe("1:x", "http://127.0.0.1:1", api=api, timeout=2)  # dead proxy

        # end to end: direct is "blocked", the proxy works -> it is chosen and saved to .env
        async def probe_via_api(token, p):
            return p is not None and await netcheck.probe(token, p, api=api)
        monkeypatch.setattr("app.main.find_route", lambda t, c: netcheck.find_route(t, c, probe_via_api))
        monkeypatch.setattr(netcheck, "getproxies", lambda: {"http": proxy})
        env = tmp_path / ".env"
        env.write_text("BOT_TOKEN=1:x\nTELEGRAM_PROXY=\n", encoding="utf-8")
        assert await resolve_telegram_route("1:x", "", str(env)) == proxy
        assert f"TELEGRAM_PROXY={proxy}" in env.read_text(encoding="utf-8")
    finally:
        proxy_srv.close()
        await runner.cleanup()


def test_save_env_value_appends(tmp_path):
    env = tmp_path / ".env"
    env.write_bytes("\ufeffBOT_TOKEN=1\n".encode("utf-8"))
    netcheck.save_env_value(str(env), "TELEGRAM_PROXY", "socks5://127.0.0.1:10808")
    assert env.read_text(encoding="utf-8") == "BOT_TOKEN=1\nTELEGRAM_PROXY=socks5://127.0.0.1:10808\n"
