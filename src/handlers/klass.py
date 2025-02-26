import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.db import async_session
from src.models import User


logger = logging.getLogger(__name__)


async def klass_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    user_id = query.from_user.id
    logging.info("Пользователь %s выбрал класс: %s", user_id, data)

    if data.startswith('class_'):
        class_level = data.split('_')[1]

        async with async_session() as session:
            user = await session.get(User, user_id)
            if user:
                user.class_level = class_level
            else:
                user = User(id=user_id, class_level=class_level)
                session.add(user)
            await session.commit()

        await query.edit_message_text(
            text=f"Ваш класс обновлён: {class_level}\n\nЧтобы начать решать домашние задания, нажмите: /subject"
        )
    else:
        logging.warning("Неизвестный выбор класса: %s", data)
        await query.edit_message_text("Неизвестный выбор.")


async def klass_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info("Пользователь %s вызвал команду /klass", user_id)

    keyboard = [
        [InlineKeyboardButton(f"{i} класс", callback_data=f'class_{i}') for i in range(1, 5)],
        [InlineKeyboardButton(f"{i} класс", callback_data=f'class_{i}') for i in range(5, 9)],
        [InlineKeyboardButton(f"{j} класс", callback_data=f'class_{j}') for j in range(9, 12)],
        [InlineKeyboardButton("Взрослый", callback_data='class_adult')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Пожалуйста, выберите ваш класс:", reply_markup=reply_markup)
