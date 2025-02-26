import asyncio
import logging
from sqlalchemy import select

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.db import async_session
from src.models import User
from src.config import ADMIN_ID


logger = logging.getLogger(__name__)

BROADCAST_COLLECT = range(1)


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return ConversationHandler.END

    await update.message.reply_text("Пожалуйста, отправьте текст и/или фото для рассылки.")
    return BROADCAST_COLLECT


async def collect_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return ConversationHandler.END

    message = update.message
    context.user_data['broadcast_message'] = message

    await update.message.reply_text("Начинаю рассылку...")
    await send_broadcast(context)
    await update.message.reply_text("Рассылка завершена.")
    context.user_data.pop('conversation', None)
    return ConversationHandler.END


async def send_broadcast(context: ContextTypes.DEFAULT_TYPE):
    message = context.user_data.get('broadcast_message')
    if not message:
        return

    # Получаем список всех пользователей из базы данных
    async with async_session() as session:
        users = await session.execute(select(User))
        users = users.scalars().all()

    # тестовая отправка только себе
    test_user_id = ADMIN_ID

    caption = message.caption if message.caption else message.text if message.text else ""

    if message.photo:
        file_id = message.photo[-1].file_id
        count = 0  # Счётчик отправленных сообщений
        for user in users:
            if user.id != test_user_id: # тестовая отправка только себе
                continue # тестовая отправка только себе
            try:
                await context.bot.send_photo(
                    chat_id=user.id,
                    photo=file_id,
                    caption=caption
                )
                count += 1
                if count % 20 == 0:
                    await asyncio.sleep(1)  # Задержка после каждых 20 сообщений
            except Exception as e:
                logging.error(f"Не удалось отправить сообщение пользователю {user.id}: {e}")
    else:
        # Если сообщение содержит только текст
        text = caption
        count = 0  # Счётчик отправленных сообщений
        for user in users:
            if user.id != test_user_id: # тестовая отправка только себе
                continue # тестовая отправка только себе
            try:
                await context.bot.send_message(
                    chat_id=user.id,
                    text=text
                )
                count += 1
                if count % 20 == 0:
                    await asyncio.sleep(1)  # Задержка после каждых 20 сообщений
            except Exception as e:
                logging.error(f"Не удалось отправить сообщение пользователю {user.id}: {e}")
