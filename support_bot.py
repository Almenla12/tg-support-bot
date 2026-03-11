# support_bot.py
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from database.db import initialize_db, close_db
from handlers import commands, private, group

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    # Initialize Database
    if not await initialize_db():
        sys.exit(1)

    # Initialize Bot and Dispatcher
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Include Routers
    dp.include_router(commands.router)
    dp.include_router(private.router)
    dp.include_router(group.router)

    # Drop pending updates and start polling
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        logging.info("Starting bot...")
        await dp.start_polling(bot)
    finally:
        logging.info("Stopping bot...")
        await close_db()
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
