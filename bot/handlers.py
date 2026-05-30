import logging
import re

from telegram import Message, Update
from telegram.constants import ChatType
from telegram import MessageEntity
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.config import Settings
from bot.gemini import GeminiClient, GeminiError
from bot.memory import ConversationMemory
from bot.telegram_utils import remove_bot_mention, send_markdown_chunks, with_typing


logger = logging.getLogger(__name__)


START_TEXT = (
    "Hi! I am your Gemini-powered AI assistant.\n\n"
    "Message me directly, or add me to a group and mention me when you want help."
)

HELP_TEXT = (
    "*How to use me*\n\n"
    "- Private chat: send any message.\n"
    "- Group chat: mention me, like `@BotName explain OOP`.\n"
    "- Group chat: reply to one of my messages to continue the thread.\n"
    "- `/reset` clears this chat's conversation memory."
)


def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(START_TEXT)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_message:
        return

    memory: ConversationMemory = context.application.bot_data["memory"]
    memory.reset(update.effective_chat.id)
    await update.effective_message.reply_text("Conversation memory cleared for this chat.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not message or not chat or not user:
        return

    original_text = (message.text or "").strip()
    if not original_text:
        return

    bot_user = await context.bot.get_me()
    should_answer = chat.type == ChatType.PRIVATE
    prompt = original_text

    if chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
        mentioned = is_bot_mentioned(message, bot_user.username)
        replied_to_bot = bool(
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.id == bot_user.id
        )
        should_answer = mentioned or replied_to_bot

        if mentioned and bot_user.username:
            prompt = remove_bot_mention(original_text, bot_user.username)

    if not should_answer or not prompt.strip():
        return

    memory: ConversationMemory = context.application.bot_data["memory"]
    gemini: GeminiClient = context.application.bot_data["gemini"]

    user_name = user.full_name or user.username or "User"
    memory_prompt = f"{user_name}: {prompt}" if chat.type != ChatType.PRIVATE else prompt
    memory.append_user(chat.id, memory_prompt)

    try:
        response = await with_typing(
            context=context,
            chat_id=chat.id,
            action=lambda: gemini.generate(memory.get(chat.id)),
        )
    except GeminiError as exc:
        await message.reply_text(str(exc))
        return
    except Exception:
        logger.exception("Unexpected failure while handling message")
        await message.reply_text("Something went wrong while generating a response.")
        return

    memory.append_model(chat.id, response)
    await send_markdown_chunks(message, response)


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not message or not chat or not user or not message.voice:
        return

    bot_user = await context.bot.get_me()
    should_answer = chat.type == ChatType.PRIVATE

    if chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
        should_answer = is_reply_to_bot(message, bot_user.id)

    if not should_answer:
        return

    settings: Settings = context.application.bot_data["settings"]
    voice = message.voice
    if voice.file_size and voice.file_size > settings.max_voice_bytes:
        await message.reply_text("That voice message is too large for me to process.")
        return

    memory: ConversationMemory = context.application.bot_data["memory"]
    gemini: GeminiClient = context.application.bot_data["gemini"]

    try:
        voice_file = await voice.get_file()
        voice_data = bytes(await voice_file.download_as_bytearray())
        if len(voice_data) > settings.max_voice_bytes:
            await message.reply_text("That voice message is too large for me to process.")
            return

        mime_type = voice.mime_type or "audio/ogg"

        transcript = await with_typing(
            context=context,
            chat_id=chat.id,
            action=lambda: gemini.transcribe_audio(voice_data, mime_type),
        )

        user_name = user.full_name or user.username or "User"
        memory_prompt = (
            f"{user_name} sent a voice message. Transcript: {transcript}"
            if chat.type != ChatType.PRIVATE
            else f"Voice message transcript: {transcript}"
        )
        memory.append_user(chat.id, memory_prompt)

        response = await with_typing(
            context=context,
            chat_id=chat.id,
            action=lambda: gemini.generate(memory.get(chat.id)),
        )
    except GeminiError as exc:
        await message.reply_text(str(exc))
        return
    except Exception:
        logger.exception("Unexpected failure while handling voice message")
        await message.reply_text("Something went wrong while processing that voice message.")
        return

    memory.append_model(chat.id, response)
    await send_markdown_chunks(message, response)


def is_bot_mentioned(message: Message, bot_username: str | None) -> bool:
    if not bot_username or not message.text:
        return False

    expected = f"@{bot_username}".lower()
    for entity in message.entities or []:
        if entity.type != MessageEntity.MENTION:
            continue

        mention_text = message.text[entity.offset : entity.offset + entity.length]
        if mention_text.lower() == expected:
            return True

    mention_pattern = rf"{re.escape(expected)}\b"
    return bool(re.search(mention_pattern, message.text, re.IGNORECASE))


def is_reply_to_bot(message: Message, bot_id: int) -> bool:
    return bool(
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == bot_id
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled Telegram error. update=%s", update, exc_info=context.error)
