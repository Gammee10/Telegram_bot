from collections import defaultdict
from copy import deepcopy
from typing import Literal, TypedDict


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

