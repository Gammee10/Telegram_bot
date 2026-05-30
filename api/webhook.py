import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler
from typing import Any

from telegram import Update

from bot.app_factory import create_application
from bot.config import Settings


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)


async def process_update(update_data: dict[str, Any]) -> None:
    settings = Settings.from_env()
    application = create_application(settings)

    await application.initialize()
    try:
        update = Update.de_json(update_data, application.bot)
        if update:
            await application.process_update(update)
    finally:
        await application.shutdown()


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._send_json(200, {"ok": True, "service": "telegram-gemini-bot"})

    def do_POST(self) -> None:
        settings = Settings.from_env()
        if settings.webhook_secret_token:
            received_secret = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if received_secret != settings.webhook_secret_token:
                self._send_json(403, {"ok": False, "error": "invalid secret token"})
                return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            update_data = json.loads(body.decode("utf-8"))
            asyncio.run(process_update(update_data))
        except Exception as exc:
            logging.exception("Failed to process Telegram webhook update")
            self._send_json(500, {"ok": False, "error": str(exc)})
            return

        self._send_json(200, {"ok": True})

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
