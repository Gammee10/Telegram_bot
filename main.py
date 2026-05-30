import logging

from bot.app_factory import create_application
from bot.config import Settings


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
    application = create_application(settings)

    if settings.use_webhook:
        logger.info("Starting bot webhook on port %s.", settings.webhook_port)
        application.run_webhook(
            listen=settings.webhook_listen,
            port=settings.webhook_port,
            url_path=settings.webhook_path,
            webhook_url=settings.full_webhook_url,
            allowed_updates=["message"],
            bootstrap_retries=5,
            drop_pending_updates=False,
            secret_token=settings.webhook_secret_token or None,
        )
        return

    logger.info("Starting bot polling. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=["message"], bootstrap_retries=5)


if __name__ == "__main__":
    main()
