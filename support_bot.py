# support_bot.py
import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

import config
from database.db import initialize_db, close_db, get_db_connection
from handlers import commands, private, group

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- Web server for Render (keep-alive) ---
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot is running"))
    app.router.add_get("/health", lambda r: web.Response(text="OK"))

    # Route لإبقاء Aiven نشطة (SELECT 1) — محمي بـ Token سري
    async def db_ping(request):
        # تحقق من الـ Token السري (بالـ Header أو Query Parameter)
        secret = request.headers.get("X-DB-Ping-Secret") or request.query.get("secret")
        expected = os.environ.get("DB_PING_SECRET", "")

        if not expected or secret != expected:
            logging.warning(f"Unauthorized /db-ping attempt from {request.remote}")
            return web.Response(text="Unauthorized", status=401)

        try:
            async with get_db_connection() as cursor:
                await cursor.execute("SELECT 1")
                await cursor.fetchone()
            return web.Response(text="DB is alive")
        except Exception as e:
            logging.error(f"DB ping error: {e}")
            return web.Response(text=f"DB error: {e}", status=500)

    app.router.add_get("/db-ping", db_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"✅ Web server started on port {port}")


async def main():
    # Initialize Database
    if not await initialize_db():
        sys.exit(1)

    # Start web server (Render needs an open port)
    await start_web_server()

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
