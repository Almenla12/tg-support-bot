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
        "مرحبًا بك في بوت التواصل \n الرجاء ارسال كافة التفاصيل وسيتم التصحيح في اقرب وقت ممكن")
    await message.answer(welcome_text)
