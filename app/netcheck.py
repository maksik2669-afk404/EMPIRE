"""Finds a working route to api.telegram.org without the user editing anything:
configured proxy -> direct -> OS system proxy -> local ports of common VPN clients."""
from __future__ import annotations

import logging
import socket
from pathlib import Path
from urllib.request import getproxies

import aiohttp
from aiohttp_socks import ProxyConnector

log = logging.getLogger(__name__)
TELEGRAM_API = "https://api.telegram.org"
# v2rayN, NekoBox/Nekoray, Clash/Mihomo/Clash Verge, Hiddify, Shadowsocks, Tor, v2rayA
LOCAL_PORTS = (10808, 10809, 2080, 2081, 7890, 7891, 7897, 12334, 1080, 9150, 9050, 20170, 20171, 20172)


async def probe(token: str, proxy: str | None, api: str = TELEGRAM_API, timeout: float = 8.0) -> bool:
    """True if the Bot API answers through this route (any HTTP answer < 500 means the route works)."""
    connector = ProxyConnector.from_url(proxy) if proxy else None
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=timeout)) as s:
            async with s.get(f"{api}/bot{token}/getMe") as r:
                return r.status < 500
    except Exception:
        return False


def _port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _normalize(url: str) -> str:
    if "://" not in url:
        url = "http://" + url
    scheme, rest = url.split("://", 1)
    scheme = {"https": "http", "socks": "socks5", "socks5h": "socks5"}.get(scheme.lower(), scheme.lower())
    return f"{scheme}://{rest}"


def candidates(configured: str = ""):
    """Routes in order of preference; '' means a direct connection. Local ports are scanned lazily."""
    seen: set[str] = set()

    def fresh(c: str) -> bool:
        if c in seen:
            return False
        seen.add(c)
        return True

    for c in ([_normalize(configured)] if configured else []) + [""]:
        if fresh(c):
            yield c
    system = getproxies()  # Windows: Internet Settings in the registry; Linux/macOS: env vars
    for key in ("https", "all", "http", "socks"):
        if system.get(key) and fresh(c := _normalize(system[key])):
            yield c
    for port in LOCAL_PORTS:
        if _port_open(port):
            for c in (f"socks5://127.0.0.1:{port}", f"http://127.0.0.1:{port}"):  # "mixed" ports accept both
                if fresh(c):
                    yield c


async def find_route(token: str, configured: str = "", probe_fn=probe) -> str | None:
    """Working proxy URL, '' for direct, or None if Telegram is unreachable every way we know."""
    for c in candidates(configured):
        if await probe_fn(token, c or None):
            return c
    return None


def save_env_value(path: str, key: str, value: str) -> None:
    """Replaces or appends KEY=value in .env (UTF-8 without BOM)."""
    p = Path(path)
    lines = p.read_text(encoding="utf-8-sig").splitlines() if p.exists() else []
    for i, line in enumerate(lines):
        if line.split("=", 1)[0].strip() == key:
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
