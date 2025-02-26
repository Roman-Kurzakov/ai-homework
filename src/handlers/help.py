import logging

from telegram import Update
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info("Получена команда /help от пользователя %s", user_id)
    help_text = (
        "Чтобы начать пользоваться ботом нужно выбрать класс ученика и предмет с которым нужна помощь.\n\n"
        "Для управления ботом воспользуйтесь командами:\n\n"
        "/subject — Выбрать предмет.\n"
        "/balance — Сколько заданий доступно.\n"
        "/referral — Пригласить друга и получить 5 заданий.\n"
        "/buy — Купить задания.\n"
        "/help — Помощь.\n"
        "/feedback — Оставить отзыв.\n"
        "/klass — Изменить класс.\n\n"
        "Будьте внимательны, модель может ошибаться. Рекомендуем проверять важную информацию."
    )
    await update.message.reply_text(help_text)
