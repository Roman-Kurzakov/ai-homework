import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.db import async_session
from src.models import User


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_username = context.bot.username  # Получаем имя бота из контекста
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            referral_link = f"https://t.me/{bot_username}?start={user.id}"
            await update.message.reply_text(
                f"Пригласите друзей по ссылке: {referral_link}\n"
                f"Вы получите 5 решений за каждого приглашенного пользователя!"
            )
        else:
            await update.message.reply_text("Не удалось найти ваши данные. Пожалуйста, используйте команду /start.")
