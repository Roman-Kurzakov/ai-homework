import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


SUBJECT_MAP = {
    'math': 'Математика',
    'russian': 'Русский язык',
    'literature': 'Литература',
    'english': 'Иностранные языки',
    'physics': 'Физика',
    'chemistry': 'Химия',
    'biology': 'Биология',
    'history': 'История',
    'social_studies': 'Обществознание',
    'geography': 'География',
    'informatics': 'Информатика',
    'other': 'Другое'
}


async def subject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info("Получена команда /subject от пользователя %s", user_id)
    keyboard = [
        [InlineKeyboardButton(SUBJECT_MAP['math'], callback_data='subject_math')],
        [InlineKeyboardButton(SUBJECT_MAP['russian'], callback_data='subject_russian')],
        [InlineKeyboardButton(SUBJECT_MAP['literature'], callback_data='subject_literature')],
        [InlineKeyboardButton(SUBJECT_MAP['english'], callback_data='subject_english')],
        [InlineKeyboardButton(SUBJECT_MAP['physics'], callback_data='subject_physics')],
        [InlineKeyboardButton(SUBJECT_MAP['chemistry'], callback_data='subject_chemistry')],
        [InlineKeyboardButton(SUBJECT_MAP['biology'], callback_data='subject_biology')],
        [InlineKeyboardButton(SUBJECT_MAP['history'], callback_data='subject_history')],
        [InlineKeyboardButton(SUBJECT_MAP['social_studies'], callback_data='subject_social_studies')],
        [InlineKeyboardButton(SUBJECT_MAP['geography'], callback_data='subject_geography')],
        [InlineKeyboardButton(SUBJECT_MAP['informatics'], callback_data='subject_informatics')],
        [InlineKeyboardButton(SUBJECT_MAP['other'], callback_data='subject_other')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Пожалуйста, выберите предмет:", reply_markup=reply_markup)


async def subject_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    logging.info("Пользователь %s выбрал предмет: %s", user_id, data)

    if not data.startswith('subject_'):
        logging.warning("Неизвестный выбор: %s", data)
        await query.edit_message_text("Неизвестный выбор.")
        return

    selected_subject = data.replace('subject_', '')
    context.user_data['selected_subject'] = selected_subject

    # Переводим в удобочитаемое название
    human_readable_subject = SUBJECT_MAP.get(selected_subject, selected_subject)

    # Отвечаем пользователю
    try:
        await query.edit_message_text(
            text=f"Вы выбрали предмет: {human_readable_subject}.\n"
                 f"Теперь отправьте ваше задание."
        )
    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения: {e}")
        await query.message.reply_text(
            text=f"Вы выбрали предмет: {human_readable_subject}.\n"
                 f"Теперь отправьте ваше задание."
        )
