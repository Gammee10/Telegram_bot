from collections import defaultdict
from copy import deepcopy
import json
from typing import Literal, TypedDict

import requests


Role = Literal["user", "model"]


class GeminiMessage(TypedDict):
    role: Role
    parts: list[dict[str, str]]


class ConversationMemory:
    """Small in-memory chat history store keyed by Telegram chat ID."""

    def __init__(self, max_turns: int = 12) -> None:
        self.max_messages = max_turns * 2
        self._messages: dict[int, list[GeminiMessage]] = defaultdict(list)

    def get(self, chat_id: int) -> list[GeminiMessage]:
        return deepcopy(self._messages[chat_id])

    def append_user(self, chat_id: int, text: str) -> None:
        self._append(chat_id, "user", text)

    def append_model(self, chat_id: int, text: str) -> None:
        self._append(chat_id, "model", text)

    def reset(self, chat_id: int) -> None:
        self._messages.pop(chat_id, None)

    def _append(self, chat_id: int, role: Role, text: str) -> None:
        self._messages[chat_id].append({"role": role, "parts": [{"text": text}]})
        self._messages[chat_id] = self._messages[chat_id][-self.max_messages :]


class RedisConversationMemory:
    """Upstash Redis-backed chat history for serverless deployments."""

    def __init__(self, rest_url: str, rest_token: str, max_turns: int = 12) -> None:
        self.rest_url = rest_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {rest_token}",
            "Content-Type": "application/json",
        }
        self.max_messages = max_turns * 2

    def get(self, chat_id: int) -> list[GeminiMessage]:
        response = requests.post(
            self.rest_url,
            headers=self.headers,
            json=["GET", self._key(chat_id)],
            timeout=10,
        )
        response.raise_for_status()
        raw_messages = response.json().get("result")
        if not raw_messages:
            return []
        return json.loads(raw_messages)

    def append_user(self, chat_id: int, text: str) -> None:
        self._append(chat_id, "user", text)

    def append_model(self, chat_id: int, text: str) -> None:
        self._append(chat_id, "model", text)

    def reset(self, chat_id: int) -> None:
        response = requests.post(
            self.rest_url,
            headers=self.headers,
            json=["DEL", self._key(chat_id)],
            timeout=10,
        )
        response.raise_for_status()

    def _append(self, chat_id: int, role: Role, text: str) -> None:
        messages = self.get(chat_id)
        messages.append({"role": role, "parts": [{"text": text}]})
        messages = messages[-self.max_messages :]
        response = requests.post(
            self.rest_url,
            headers=self.headers,
            json=["SET", self._key(chat_id), json.dumps(messages)],
            timeout=10,
        )
        response.raise_for_status()

    def _key(self, chat_id: int) -> str:
        return f"telegram-bot:chat:{chat_id}:history"
