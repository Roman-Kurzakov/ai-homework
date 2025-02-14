import logging

from telegram import Update
from telegram.ext import ContextTypes


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info("Получена команда /help от пользователя %s", user_id)
    help_text = (
        "/subject — Выбрать предмет.\n"
        "/balance — Сколько заданий доступно.\n"
        "/referral — Пригласить друга и получить 5 решений.\n"
        "/buy — Купить задания.\n"
        "/help — Помощь.\n"
        "/feedback — Оставить отзыв.\n"
        "/klass — Изменить класс."
    )
    await update.message.reply_text(help_text)
