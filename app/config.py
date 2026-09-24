"""Settings are read from environment variables (and an optional .env file)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def load_dotenv(path: str = ".env") -> None:
    """Minimal .env loader: KEY=VALUE lines, existing env vars win."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8-sig").splitlines():  # -sig: tolerate a BOM from Windows editors
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    bot_token: str
    fernet_key: str
    db_path: str = "data/app.db"
    # LLM: "yandex" (YandexGPT, Yandex Cloud), "openai" (any OpenAI-compatible API), "mock" (demo/tests)
    llm_provider: str = "yandex"
    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_model: str = "yandexgpt/latest"
    openai_base_url: str = ""
    openai_api_key: str = ""
    openai_model: str = ""
    poll_interval_sec: int = 300
    max_items_per_poll: int = 20
    free_monthly_limit: int = 100
    admin_ids: frozenset[int] = field(default_factory=frozenset)
    telegram_proxy: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        env = os.environ.get
        missing = [k for k in ("BOT_TOKEN", "FERNET_KEY") if not env(k)]
        if missing:
            raise RuntimeError(f"Не заданы переменные окружения: {', '.join(missing)} (см. .env.example)")
        admins = frozenset(int(x) for x in env("ADMIN_IDS", "").replace(" ", "").split(",") if x)
        return cls(
            bot_token=env("BOT_TOKEN", ""),
            fernet_key=env("FERNET_KEY", ""),
            db_path=env("DB_PATH", "data/app.db"),
            llm_provider=env("LLM_PROVIDER", "yandex"),
            yandex_api_key=env("YANDEX_API_KEY", ""),
            yandex_folder_id=env("YANDEX_FOLDER_ID", ""),
            yandex_model=env("YANDEX_MODEL", "yandexgpt/latest"),
            openai_base_url=env("OPENAI_BASE_URL", ""),
            openai_api_key=env("OPENAI_API_KEY", ""),
            openai_model=env("OPENAI_MODEL", ""),
            poll_interval_sec=int(env("POLL_INTERVAL_SEC", "300")),
            max_items_per_poll=int(env("MAX_ITEMS_PER_POLL", "20")),
            free_monthly_limit=int(env("FREE_MONTHLY_LIMIT", "100")),
            admin_ids=admins,
            telegram_proxy=env("TELEGRAM_PROXY", ""),
        )
