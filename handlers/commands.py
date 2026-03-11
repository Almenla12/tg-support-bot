# handlers/commands.py
import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()

@router.message(CommandStart())
async def handle_start(message: Message):
    logging.info(f"User {message.from_user.id} ({message.from_user.full_name}) sent /start")
    welcome_text = (
        "Hello!\nWrite your question and we will answer you as soon as possible!\n"
        "Please describe your problem in as much detail as possible."
    )
    await message.answer(welcome_text)
