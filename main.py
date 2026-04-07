import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import load_settings
from bot.handlers import build_router
from bot.rewrite import StyleRewriter


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    settings = load_settings()
    rewriter = StyleRewriter(settings)

    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router(settings, rewriter))

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
