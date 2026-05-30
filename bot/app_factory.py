from telegram.ext import Application, ApplicationBuilder

from bot.config import Settings
from bot.gemini import GeminiClient
from bot.handlers import register_handlers
from bot.memory import ConversationMemory, RedisConversationMemory


def create_application(settings: Settings) -> Application:
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

    if settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
        application.bot_data["memory"] = RedisConversationMemory(
            rest_url=settings.upstash_redis_rest_url,
            rest_token=settings.upstash_redis_rest_token,
            max_turns=settings.max_memory_turns,
        )
    else:
        application.bot_data["memory"] = ConversationMemory(max_turns=settings.max_memory_turns)

    register_handlers(application)
    return application
