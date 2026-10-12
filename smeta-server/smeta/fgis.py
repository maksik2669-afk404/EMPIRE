"""Download official data (FSNB-2022, FGIS CS indices) and import it in one command.

Run this on the server that has access to the portals:

    python3 -m smeta.fgis check  https://fgiscs.minstroyrf.ru/...
    python3 -m smeta.fgis fetch  https://fgiscs.minstroyrf.ru/... --kind rates
    python3 -m smeta.fgis fetch  'https://.../indices.xlsx' --kind indices \
        --header 'Cookie: session=...'            # если портал требует авторизацию
    python3 -m smeta.fgis load   ~/Downloads/ФСНБ-2022.zip --kind rates

`fetch` saves the original file to data/import/ and writes the canonical CSV that the bot
reads (data/rates/fer.csv or data/rates/indices.csv), so nothing has to be done by hand.
Telegram limits bot downloads to 20 MB - full FSNB archives are imported this way instead.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from . import importer

DATA = Path("data")
IMPORT_DIR = DATA / "import"
RATES_CSV = DATA / "rates" / "fer.csv"
INDICES_CSV = DATA / "rates" / "indices_fgis.csv"
MAX_BYTES = 1024 * 1024 * 1024
USER_AGENT = "smeta-bot/1.0 (+https://github.com/maksik2669-afk404/EMPIRE)"


def _client(headers: list[str] | None, timeout: float):
    import httpx

    extra = {}
    for item in headers or []:
        name, _, value = item.partition(":")
        if name.strip() and value.strip():
            extra[name.strip()] = value.strip()
    return httpx.Client(
        follow_redirects=True,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT, **extra},
        trust_env=True,                       # HTTPS_PROXY / REQUESTS_CA_BUNDLE
    )


def check(url: str, *, headers: list[str] | None = None, timeout: float = 30) -> int:
    try:
        return _check(url, headers=headers, timeout=timeout)
    except Exception as error:                 # сеть, прокси, TLS, DNS
        print(f"Не дотянулся до {url}: {error}")
        print("Проверьте, что сервер видит портал: curl -I <ссылка>. "
              "Если доступ закрыт политикой сети — откройте домен в настройках окружения.")
        return 1


def _check(url: str, *, headers: list[str] | None = None, timeout: float = 30) -> int:
    with _client(headers, timeout) as client:
        response = client.request("GET", url, headers={"Range": "bytes=0-0"})
        size = response.headers.get("content-range", "").rpartition("/")[2] or response.headers.get("content-length", "?")
        print(f"HTTP {response.status_code} · {response.headers.get('content-type', '?')} · размер {size} байт")
        if response.status_code >= 400:
            print("Портал не отдал файл. Если нужна авторизация — скопируйте из браузера "
                  "заголовок Cookie и повторите с --header 'Cookie: ...'")
            return 1
    return 0


def fetch(url: str, *, dest: Path | None = None, headers: list[str] | None = None,
          timeout: float = 120, retries: int = 4) -> Path:
    """Download with retries and a size cap. Returns the saved path."""
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    name = Path(url.split("?")[0]).name or f"download-{int(time.time())}"
    target = dest or IMPORT_DIR / name
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with _client(headers, timeout) as client, client.stream("GET", url) as response:
                response.raise_for_status()
                written = 0
                with open(target, "wb") as handle:
                    for chunk in response.iter_bytes(1024 * 256):
                        written += len(chunk)
                        if written > MAX_BYTES:
                            raise OSError(f"файл больше {MAX_BYTES // 1024 // 1024} МБ — скачайте вручную")
                        handle.write(chunk)
                print(f"Скачал {written / 1024 / 1024:.1f} МБ → {target}")
                return target
        except Exception as error:             # сеть, 5xx, таймаут
            last_error = error
            if attempt < retries - 1:
                delay = 2 ** (attempt + 1)
                print(f"Попытка {attempt + 1} не удалась ({error}). Повтор через {delay} с…")
                time.sleep(delay)
    raise SystemExit(f"Не смог скачать: {last_error}")


def load(path: Path, kind: str = "auto", *, out: Path | None = None, append: bool = False) -> int:
    """Import a local file into the canonical CSV the bot reads."""
    data = path.read_bytes()
    if kind == "auto":
        name = path.name.lower()
        kind = "indices" if any(word in name for word in ("индекс", "index", "ксмр", "ismr")) else "rates"

    if kind == "rates":
        rates, report = importer.import_rates(data, path.name)
        print(report.as_text())
        if not rates:
            return 1
        target = out or RATES_CSV
        target.parent.mkdir(parents=True, exist_ok=True)
        body = importer.rates_to_csv(rates)
        if append and target.exists():
            body = target.read_text(encoding="utf-8").rstrip("\n") + "\n" + body.split("\n", 1)[1]
        target.write_text(body, encoding="utf-8")
        print(f"Готово: {len(rates)} расценок в {target}. Бот подхватит их при следующем запуске.")
        return 0

    indices, report = importer.import_indices(data, path.name)
    print(report.as_text())
    if not indices:
        return 1
    target = out or INDICES_CSV
    target.parent.mkdir(parents=True, exist_ok=True)
    body = importer.indices_to_csv(indices)
    if append and target.exists():
        body = target.read_text(encoding="utf-8").rstrip("\n") + "\n" + body.split("\n", 1)[1]
    target.write_text(body, encoding="utf-8")
    print(f"Готово: {len(indices)} индексов в {target}. Выбрать нужный — командой /index в боте.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="smeta.fgis", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--header", action="append", dest="headers", help="доп. заголовок, можно несколько")
    common.add_argument("--timeout", type=float, default=120)

    check_parser = sub.add_parser("check", parents=[common], help="проверить доступность ссылки")
    check_parser.add_argument("url")

    fetch_parser = sub.add_parser("fetch", parents=[common], help="скачать и импортировать")
    fetch_parser.add_argument("url")
    fetch_parser.add_argument("--kind", choices=("rates", "indices", "auto"), default="auto")
    fetch_parser.add_argument("--out", type=Path)
    fetch_parser.add_argument("--append", action="store_true", help="добавить к уже загруженному")
    fetch_parser.add_argument("--no-import", action="store_true", help="только скачать")

    load_parser = sub.add_parser("load", help="импортировать локальный файл")
    load_parser.add_argument("path", type=Path)
    load_parser.add_argument("--kind", choices=("rates", "indices", "auto"), default="auto")
    load_parser.add_argument("--out", type=Path)
    load_parser.add_argument("--append", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "check":
        return check(args.url, headers=args.headers, timeout=args.timeout)
    if args.command == "fetch":
        path = fetch(args.url, headers=args.headers, timeout=args.timeout)
        if args.no_import:
            return 0
        return load(path, args.kind, out=args.out, append=args.append)
    return load(args.path, args.kind, out=args.out, append=args.append)


if __name__ == "__main__":
    raise SystemExit(main())
