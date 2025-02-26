import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.db import async_session
from src.models import User


logger = logging.getLogger(__name__)


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info("Получена команда /balance от пользователя %s", user_id)

    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            user = User(id=user_id, remaining_tasks=0, subscription_type="free")
            session.add(user)
            await session.commit()
        balance = user.remaining_tasks
        await update.message.reply_text(f"У вас осталось {balance} заданий.")
