import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    max_memory_turns: int = 12

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        gemini_model = os.getenv("GEMINI_MODEL", cls.gemini_model).strip()
        max_memory_turns = int(os.getenv("MAX_MEMORY_TURNS", str(cls.max_memory_turns)))

        missing = []
        if not telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not gemini_api_key:
            missing.append("GEMINI_API_KEY")
        if missing:
            names = ", ".join(missing)
            raise RuntimeError(f"Missing required environment variable(s): {names}")

        return cls(
            telegram_bot_token=telegram_bot_token,
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            max_memory_turns=max_memory_turns,
        )
