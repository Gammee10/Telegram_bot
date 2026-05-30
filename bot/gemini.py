import asyncio
import base64
import logging
from typing import Any

import requests

from bot.memory import GeminiMessage


logger = logging.getLogger(__name__)


class GeminiError(RuntimeError):
    """Raised when Gemini cannot produce a usable response."""


class GeminiClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        )

    async def generate(self, history: list[GeminiMessage]) -> str:
        return await asyncio.to_thread(self._generate_sync, history)

    async def transcribe_audio(self, audio_bytes: bytes, mime_type: str) -> str:
        return await asyncio.to_thread(self._transcribe_audio_sync, audio_bytes, mime_type)

    def _generate_sync(self, history: list[GeminiMessage]) -> str:
        payload: dict[str, Any] = {
            "system_instruction": {
                "parts": [
                    {
                        "text": (
                            "You are a helpful AI assistant in a Telegram chat. "
                            "Respond in a warm, conversational ChatGPT-like style. "
                            "Use clear Markdown when it improves readability. "
                            "Keep answers concise unless the user asks for depth."
                        )
                    }
                ]
            },
            "contents": history,
            "generationConfig": {
                "temperature": 0.8,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            },
        }

        return self._post_generate_content(payload)

    def _transcribe_audio_sync(self, audio_bytes: bytes, mime_type: str) -> str:
        encoded_audio = base64.b64encode(audio_bytes).decode("ascii")
        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Transcribe this Telegram voice message accurately. "
                                "Return only the user's spoken words. "
                                "If the audio is unclear, say what you can understand."
                            )
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": encoded_audio,
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1024,
            },
        }

        return self._post_generate_content(payload)

    def _post_generate_content(self, payload: dict[str, Any]) -> str:

        try:
            response = requests.post(
                self.endpoint,
                headers={"x-goog-api-key": self.api_key},
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("Gemini request failed")
            raise GeminiError("I could not reach Gemini right now. Please try again.") from exc

        data = response.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
            text = "\n".join(part.get("text", "") for part in parts).strip()
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("Unexpected Gemini response: %s", data)
            raise GeminiError("Gemini returned an unexpected response.") from exc

        if not text:
            raise GeminiError("Gemini returned an empty response.")

        return text
