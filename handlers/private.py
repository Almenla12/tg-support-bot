# handlers/private.py
import logging
import html
from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.exceptions import TelegramAPIError

import config
from database.db import get_topic_id_for_user, save_user_topic_mapping

router = Router()

@router.message(F.chat.type == "private", ~F.text.startswith('/'))
async def handle_user_private_message(message: Message, bot: Bot):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    logging.info(f"Received PM from {user_id} ({user_name})")

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
        logging.error(f"Unexpected error for {user_id}: {e}", exc_info=True)
        await message.answer("An internal error occurred.")

@router.edited_message(F.chat.type == "private")
async def handle_edited_private_message(message: Message, bot: Bot):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    logging.info(f"User {user_id} edited message {message.message_id}")

    topic_id = await get_topic_id_for_user(user_id)
    if topic_id:
        try:
            notification_text = f"❗️ User <b>{html.escape(user_name)}</b> (ID: {user_id}) edited a message:"
            await bot.send_message(config.GROUP_ID, notification_text, message_thread_id=topic_id)
            await bot.forward_message(config.GROUP_ID, message.chat.id, message.message_id, message_thread_id=topic_id)
        except Exception as e:
            logging.error(f"Error forwarding edit from {user_id}: {e}", exc_info=True)
