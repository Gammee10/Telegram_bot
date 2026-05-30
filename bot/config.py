import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    max_memory_turns: int = 12
    bot_mode: str = "polling"
    webhook_url: str = ""
    webhook_path: str = "telegram-webhook"
    webhook_listen: str = "0.0.0.0"
    webhook_port: int = 8000
    webhook_secret_token: str = ""

    @property
    def use_webhook(self) -> bool:
        return self.bot_mode == "webhook" or bool(self.webhook_url)

    @property
    def full_webhook_url(self) -> str:
        return f"{self.webhook_url.rstrip('/')}/{self.webhook_path.lstrip('/')}"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        gemini_model = os.getenv("GEMINI_MODEL", cls.gemini_model).strip()
        max_memory_turns = int(os.getenv("MAX_MEMORY_TURNS", str(cls.max_memory_turns)))
        bot_mode = os.getenv("BOT_MODE", cls.bot_mode).strip().lower()
        webhook_url = os.getenv("WEBHOOK_URL", "").strip()
        webhook_path = os.getenv("WEBHOOK_PATH", cls.webhook_path).strip().strip("/")
        webhook_listen = os.getenv("WEBHOOK_LISTEN", cls.webhook_listen).strip()
        webhook_port = int(os.getenv("PORT", os.getenv("WEBHOOK_PORT", str(cls.webhook_port))))
        webhook_secret_token = os.getenv("WEBHOOK_SECRET_TOKEN", "").strip()

        missing = []
        if not telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not gemini_api_key:
            missing.append("GEMINI_API_KEY")
        if bot_mode not in {"polling", "webhook"}:
            raise RuntimeError("BOT_MODE must be either 'polling' or 'webhook'")
        if bot_mode == "webhook" and not webhook_url:
            missing.append("WEBHOOK_URL")
        if missing:
            names = ", ".join(missing)
            raise RuntimeError(f"Missing required environment variable(s): {names}")

        return cls(
            telegram_bot_token=telegram_bot_token,
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            max_memory_turns=max_memory_turns,
            bot_mode=bot_mode,
            webhook_url=webhook_url,
            webhook_path=webhook_path or cls.webhook_path,
            webhook_listen=webhook_listen,
            webhook_port=webhook_port,
            webhook_secret_token=webhook_secret_token,
        )
