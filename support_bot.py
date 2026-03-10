# support_bot.py
import asyncio
import logging
import sys
from contextlib import suppress

import aiomysql
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart
from aiogram.types import Message
import html

import config

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Global variables for database pools ---
db_pool = None

# --- Aiogram routers initialization ---
private_router = Router()
group_router = Router()
commands_router = Router()


# === Database helper functions (user_topics) ===
async def initialize_db_pools():
    """Initializes the database connection pool."""
    global db_pool
    try:
        db_pool = await aiomysql.create_pool(
            host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASSWORD,
            db=config.DB_NAME, autocommit=True, loop=asyncio.get_running_loop()
        )
        logging.info("Main DB connection pool created successfully.")
        return True
    except Exception as e:
        logging.critical(f"Failed to create DB connection pool: {e}")
        return False


async def initialize_database_tables():
    """Checks and creates necessary tables in the bot's database."""
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_topics (
                        user_id BIGINT PRIMARY KEY, topic_id BIGINT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_topic_id (topic_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                logging.info("Check/Creation of 'user_topics' table completed.")
                return True
            except Exception as e:
                logging.error(f"Error initializing 'user_topics' table: {e}")
                return False


async def get_topic_id_for_user(user_id: int) -> int | None:
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT topic_id FROM user_topics WHERE user_id = %s", (user_id,))
            result = await cursor.fetchone()
            return result[0] if result else None


async def get_user_id_for_topic(topic_id: int) -> int | None:
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT user_id FROM user_topics WHERE topic_id = %s", (topic_id,))
            result = await cursor.fetchone()
            return result[0] if result else None


async def save_user_topic_mapping(user_id: int, topic_id: int) -> bool:
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                query = "INSERT INTO user_topics (user_id, topic_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE topic_id = VALUES(topic_id);"
                await cursor.execute(query, (user_id, topic_id))
                logging.info(f"DB: Link user_id {user_id} -> topic_id {topic_id} saved/updated.")
                return True
            except Exception as e:
                logging.error(f"DB Error: save_user_topic_mapping({user_id}, {topic_id}): {e}")
                return False


# --- Command Handlers (commands_router) ---

@commands_router.message(CommandStart())
async def handle_start(message: Message):
    logging.info(f"User {message.from_user.id} ({message.from_user.full_name}) sent /start")
    welcome_text = (
        "Hello!\nWrite your question and we will answer you as soon as possible!\n"
        "Please describe your problem in as much detail as possible."
    )
    await message.answer(welcome_text)


# --- Private Message Handlers (private_router) ---

@private_router.message(F.chat.type == "private", ~F.text.startswith('/'))
async def handle_user_private_message(message: Message, bot: Bot):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    logging.info(f"Received PM (type: {message.content_type}) from {user_id} ({user_name})")

    try:
        topic_id = await get_topic_id_for_user(user_id)
        if not topic_id:
            topic_name = f"Support: {user_name} (ID: {user_id})"
            created_topic = await bot.create_forum_topic(chat_id=config.GROUP_ID, name=topic_name)
            topic_id = created_topic.message_thread_id
            logging.info(f"Created topic {topic_id} for user {user_id}.")
            if not await save_user_topic_mapping(user_id, topic_id):
                await message.answer("Error saving session data. Please try again.")
                return

        await bot.copy_message(
            chat_id=config.GROUP_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            message_thread_id=topic_id
        )
    except TelegramAPIError as e:
        logging.error(f"API Error processing PM from {user_id}: {e}")
        await message.answer("Failed to process your message. Please try again later.")
    except Exception as e:
        logging.error(f"Unexpected error in handle_user_private_message for {user_id}: {e}", exc_info=True)
        await message.answer("An internal error occurred. We are already working on it.")


@private_router.edited_message(F.chat.type == "private")
async def handle_edited_private_message(message: Message, bot: Bot):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    logging.info(f"User {user_id} ({user_name}) edited message ID {message.message_id}")

    topic_id = await get_topic_id_for_user(user_id)
    if topic_id:
        try:
            notification_text = f"❗️ User <b>{html.escape(user_name)}</b> (ID: {user_id}) edited a message:"
            await bot.send_message(config.GROUP_ID, notification_text, message_thread_id=topic_id)
            await bot.forward_message(config.GROUP_ID, message.chat.id, message.message_id, message_thread_id=topic_id)
        except Exception as e:
            logging.error(f"Error forwarding edited message from {user_id}: {e}", exc_info=True)


# --- Support Group Message Handlers (group_router) ---

@group_router.message(F.chat.id == config.GROUP_ID, F.message_thread_id, ~F.text.startswith('/'))
async def handle_topic_message(message: Message, bot: Bot):
    if message.from_user.id == bot.id:
        return

    agent_name = message.from_user.full_name
    topic_id = message.message_thread_id
    logging.info(f"Received message in topic {topic_id} from agent {agent_name}")

    user_id = await get_user_id_for_topic(topic_id)
    if not user_id:
        logging.warning(f"No user found in DB for topic {topic_id}.")
        await message.reply("⚠️ Failed to find the user associated with this topic.")
        return

    try:
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
    except TelegramAPIError as e:
        logging.error(f"API Error replying to user {user_id}: {e}")
        error_text = f"⚠️ <b>Failed to deliver message.</b>\nReason: <code>{html.escape(e.message)}</code>"
        if "bot was blocked by the user" in e.message:
            error_text = f"⚠️ <b>User (ID: {user_id}) has blocked the bot.</b>"
        elif "chat not found" in e.message:
            error_text = f"⚠️ <b>Chat with user (ID: {user_id}) not found.</b>"

        await message.reply(error_text)
    except Exception as e:
        logging.error(f"Unexpected error replying to user {user_id}: {e}", exc_info=True)
        await message.reply("⚠️ An internal error occurred while sending the message.")


@group_router.edited_message(F.chat.id == config.GROUP_ID, F.message_thread_id)
async def handle_edited_topic_message(message: Message, bot: Bot):
    if message.from_user.id == bot.id or not message.text:
        return

    user_id = await get_user_id_for_topic(message.message_thread_id)
    if user_id:
        try:
            edited_text = (
                f"<i>[Support message was edited]</i>\n\n"
                f"{message.text}"
            )
            await bot.send_message(user_id, edited_text)
        except Exception as e:
            logging.error(f"Failed to send edit notification to user {user_id}: {e}")
            await message.reply(f"⚠️ Failed to deliver edited message (ID: {user_id}).")


# --- Main entry point ---
async def main():
    if not await initialize_db_pools():
        sys.exit(1)
    if not await initialize_database_tables():
        sys.exit(1)

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(commands_router)
    dp.include_router(private_router)
    dp.include_router(group_router)

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        logging.info("Starting bot...")
        await dp.start_polling(bot)
    finally:
        logging.info("Stopping bot...")
        if db_pool:
            db_pool.close()
            await db_pool.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
