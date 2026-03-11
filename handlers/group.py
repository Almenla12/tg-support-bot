# handlers/group.py
import logging
from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.exceptions import TelegramAPIError
import html

import config
from database.db import get_user_id_for_topic

router = Router()

@router.message(F.chat.id == config.GROUP_ID, F.message_thread_id, ~F.text.startswith('/'))
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
        await message.reply("⚠️ An internal error occurred.")

@router.edited_message(F.chat.id == config.GROUP_ID, F.message_thread_id)
async def handle_edited_topic_message(message: Message, bot: Bot):
    if message.from_user.id == bot.id or not message.text:
        return

    user_id = await get_user_id_for_topic(message.message_thread_id)
    if user_id:
        try:
            edited_text = f"<i>[Support message was edited]</i>\n\n{message.text}"
            await bot.send_message(user_id, edited_text)
        except Exception as e:
            logging.error(f"Failed to send edit notification to user {user_id}: {e}")
            await message.reply(f"⚠️ Failed to deliver edited message.")
