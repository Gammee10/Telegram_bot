import logging

from telegram.ext import ApplicationBuilder

from bot.config import Settings
from bot.gemini import GeminiClient
from bot.handlers import register_handlers
from bot.memory import ConversationMemory


def configure_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=logging.INFO,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)

    settings = Settings.from_env()
    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .get_updates_connect_timeout(30)
        .get_updates_read_timeout(30)
        .build()
    )

    application.bot_data["gemini"] = GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
    )
    application.bot_data["settings"] = settings
    application.bot_data["memory"] = ConversationMemory(max_turns=settings.max_memory_turns)

    register_handlers(application)

    if settings.use_webhook:
        logger.info("Starting bot webhook on port %s.", settings.webhook_port)
        application.run_webhook(
            listen=settings.webhook_listen,
            port=settings.webhook_port,
            url_path=settings.webhook_path,
            webhook_url=settings.full_webhook_url,
            allowed_updates=["message"],
            bootstrap_retries=5,
            drop_pending_updates=True,
            secret_token=settings.webhook_secret_token or None,
        )
        return

    logger.info("Starting bot polling. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=["message"], bootstrap_retries=5)


if __name__ == "__main__":
    main()
