import logging


from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.db import async_session
from src.models import User, Feedback


logger = logging.getLogger(__name__)

FEEDBACK = 1


async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info("Получена команда /feedback от пользователя %s", user_id)
    await update.message.reply_text("Введите ваш отзыв как обычное сообщение")
    return FEEDBACK


async def handle_feedback_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    feedback_text = update.message.text

    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            feedback = Feedback(user_id=user_id, feedback_text=feedback_text)
            session.add(feedback)
            await session.commit()
            await update.message.reply_text("Спасибо за ваш отзыв!")
        else:
            await update.message.reply_text("Не удалось сохранить ваш отзыв. Пожалуйста, попробуйте позже.")
    context.user_data.pop('conversation', None)
    return ConversationHandler.END
