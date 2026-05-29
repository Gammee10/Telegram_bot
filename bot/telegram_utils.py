import asyncio
import contextlib
import re
from collections.abc import Awaitable, Callable

from telegram import Message
from telegram.constants import ChatAction, ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes


TELEGRAM_MESSAGE_LIMIT = 4096
SAFE_CHUNK_SIZE = 3900


def split_message(text: str, limit: int = SAFE_CHUNK_SIZE) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""

    for paragraph in re.split(r"(\n\s*\n)", text):
        if len(current) + len(paragraph) <= limit:
            current += paragraph
            continue

        if current.strip():
            chunks.append(current.strip())
            current = ""

        while len(paragraph) > limit:
            split_at = paragraph.rfind("\n", 0, limit)
            if split_at == -1:
                split_at = paragraph.rfind(" ", 0, limit)
            if split_at == -1:
                split_at = limit
            chunks.append(paragraph[:split_at].strip())
            paragraph = paragraph[split_at:].strip()

        current = paragraph

    if current.strip():
        chunks.append(current.strip())

    return [chunk for chunk in chunks if chunk]


async def send_markdown_chunks(message: Message, text: str) -> None:
    for chunk in split_message(text):
        try:
            await message.reply_text(
                chunk,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
        except BadRequest:
            await message.reply_text(chunk, disable_web_page_preview=True)


def remove_bot_mention(text: str, bot_username: str) -> str:
    return re.sub(
        rf"@{re.escape(bot_username)}\b",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()


async def with_typing(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    action: Callable[[], Awaitable[str]],
) -> str:
    async def keep_typing() -> None:
        while True:
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(4)

    typing_task = asyncio.create_task(keep_typing())
    try:
        return await action()
    finally:
        typing_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await typing_task

