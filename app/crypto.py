"""Encryption of marketplace API keys at rest. Keys are never stored in plain text."""
from __future__ import annotations

import json

from cryptography.fernet import Fernet, InvalidToken


class Vault:
    def __init__(self, key: str):
        self._f = Fernet(key.encode())

    def encrypt(self, data: dict) -> str:
        return self._f.encrypt(json.dumps(data).encode()).decode()

    def decrypt(self, token: str) -> dict:
        try:
            return json.loads(self._f.decrypt(token.encode()))
        except InvalidToken as e:
            raise ValueError("Не удалось расшифровать ключи: FERNET_KEY изменился?") from e


if __name__ == "__main__":  # python -m app.crypto  -> prints a new FERNET_KEY
    print(Fernet.generate_key().decode())
