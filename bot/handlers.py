from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.config import Settings
from bot.rewrite import RewriteError, StyleRewriter


def build_router(settings: Settings, rewriter: StyleRewriter) -> Router:
    router = Router()

    def is_allowed(user_id: int | None) -> bool:
        if user_id is None:
            return False
        return user_id in settings.allowed_user_ids

    @router.message(CommandStart())
    async def start_handler(message: Message) -> None:
        await message.answer(
            "Привет. Я переписываю тексты в стиле автора по его примерам.\n\n"
            "Как пользоваться:\n"
            "1. Пришли мне обычный текст сообщением.\n"
            "2. Я верну переписанную версию.\n\n"
            "Команды:\n"
            "/help — инструкция\n"
            "/id — показать твой Telegram user id"
        )

    @router.message(Command("help"))
    async def help_handler(message: Message) -> None:
        await message.answer(
            "Отправь мне текст одним сообщением, и я перепишу его в нужном стиле.\n\n"
            "Важно:\n"
            "- бот работает только для пользователей из списка доступа;\n"
            "- лучше присылать именно текст, без файлов и без голосовых;\n"
            "- если текст очень длинный, бот попросит его сократить.\n\n"
            "Если нужно узнать свой user id для доступа, отправь /id."
        )

    @router.message(Command("id"))
    async def id_handler(message: Message) -> None:
        await message.answer(
            f"Твой Telegram user id: {message.from_user.id if message.from_user else 'не удалось определить'}"
        )

    @router.message(F.text)
    async def rewrite_handler(message: Message) -> None:
        if not is_allowed(message.from_user.id if message.from_user else None):
            await message.answer(
                "У тебя пока нет доступа к этому боту. Пришли владельцу свой user id через команду /id."
            )
            return

        text = message.text.strip()
        if not text:
            await message.answer("Пришли текст сообщением, и я его перепишу.")
            return

        if text.startswith("/"):
            await message.answer("Неизвестная команда. Используй /help.")
            return

        await message.answer("Переписываю текст...")

        try:
            result = await asyncio.to_thread(rewriter.rewrite, text)
        except RewriteError as error:
            await message.answer(str(error))
            return

        await message.answer(result.text)

    @router.message()
    async def unsupported_message_handler(message: Message) -> None:
        await message.answer("Пока я умею работать только с обычным текстом. Пришли текст сообщением.")

    return router
