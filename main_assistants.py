'''бэкап 23.01 чат комплишнс текст, фото, адаптация под класс'''

import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, Message
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler, ConversationHandler
)
from telegram.constants import ParseMode
from db import async_session
from db_models import User, UserThread, Feedback
from openai import AsyncOpenAI
from imgurpython import ImgurClient
import tempfile
from utils import markdown_to_html, create_payment
from sqlalchemy import select



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")
IMGUR_CLIENT_SECRET = os.getenv("IMGUR_CLIENT_SECRET")
ADMIN_ID = int(os.getenv('ADMIN_ID'))

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
imgur_client = ImgurClient(IMGUR_CLIENT_ID, IMGUR_CLIENT_SECRET)

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

FEEDBACK = 1
BROADCAST_COLLECT = range(1)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Получена команда /start от пользователя %s", update.effective_user.id)
    user_id = update.effective_user.id
    args = context.args
    referred_by_id = int(args[0]) if args and args[0].isdigit() else None

    async with async_session() as session:
        user = await session.get(User, user_id)

        if not user:
            # Новый пользователь
            user = User(id=user_id)
            if referred_by_id and referred_by_id != user_id:
                referrer = await session.get(User, referred_by_id)
                if referrer:
                    user.referred_by = referrer.id
            session.add(user)
            await session.commit()

            # Начисление бонуса пригласившему
            if user.referred_by and not user.referral_bonus_claimed:
                referrer = await session.get(User, user.referred_by)
                if referrer:
                    referrer.remaining_tasks += 5
                    user.referral_bonus_claimed = True
                    await session.commit()
                    # Уведомляем пригласившего
                    await context.bot.send_message(
                        chat_id=referrer.id,
                        text="Ваш друг присоединился к боту по вашей реферальной ссылке! Вам начислено 5 решений."
                    )
        else:
            # Если пользователь уже есть, но появился referred_by_id
            if referred_by_id and not user.referred_by and referred_by_id != user_id:
                referrer = await session.get(User, referred_by_id)
                if referrer:
                    user.referred_by = referrer.id
                    await session.commit()

    await update.message.reply_text(
        "Привет! Давай разберемся с твоим дз. Выбери класс, чтобы я мог объяснять решения на понятном тебе языке."
    )
    keyboard = [
        [InlineKeyboardButton(f"{i} класс", callback_data=f'class_{i}') for i in range(1, 5)],
        [InlineKeyboardButton(f"{i} класс", callback_data=f'class_{i}') for i in range(5, 9)],
        [InlineKeyboardButton(f"{j} класс", callback_data=f'class_{j}') for j in range(9, 12)],
        [InlineKeyboardButton("Взрослый", callback_data='class_adult')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Пожалуйста, выберите ваш класс:", reply_markup=reply_markup)

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


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.message_id == context.user_data.get('last_processed_message_id'):
        return

    user_id = update.effective_user.id
    message = update.message

    # Проверяем наличие выбранного предмета
    selected_subject = context.user_data.get('selected_subject')
    if not selected_subject:
        await message.reply_text("Пожалуйста, сначала выберите предмет, используя команду /subject.")
        return

    # Получаем инструкцию для выбранного предмета
    subject_instruction = get_subject_instruction(selected_subject)
    if not subject_instruction:
        await message.reply_text("Не удалось найти инструкцию для выбранного предмета.")
        return

    # Получаем уровень класса пользователя
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            await message.reply_text("Не удалось получить данные пользователя.")
            return
        if user.remaining_tasks <= 0:
            await message.reply_text("У вас закончились доступные задания.\nЧтобы купить больше решений, нажмите: /buy")
            return
        class_level = user.class_level or "неизвестный"

    # Получаем ввод пользователя
    user_input = None

    if message.photo:
        # Обработка фото
        logging.info("Пользователь %s отправил фото", user_id)
        photo = message.photo[-1]
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        # Создаем временный файл для фото
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp:
            temp.write(photo_bytes)
            temp_path = temp.name

        # Загрузка изображения на Imgur
        image = imgur_client.upload_from_path(temp_path)
        image_url = image['link']

        # Удаляем временный файл
        os.remove(temp_path)

        # Формируем ввод для ассистента
        caption = message.caption if message.caption else ""

        user_input = [
            {"type": "text", "text": caption},
            {
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                }
            },
        ]
    elif message.text:
        logging.info("Пользователь %s отправил текст: %s", user_id, message.text)
        # Новый блок просит адаптировать ответ под нужный класс
        user_input = [
            {"type": "text", "text": message.text}
        ]
    else:
        await message.reply_text("Пожалуйста, отправьте текст или изображение задания.")
        return

    # Формируем сообщения для OpenAI API
    messages = [
        {"role": "system", "content": f"{subject_instruction}\n\nУровень класса: {class_level}"},
        {"role": "user", "content": user_input}
    ]

    #запрос к OpenAI API
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
            user=str(user_id)
        )
        
        assistant_reply = response.choices[0].message.content

        if assistant_reply.strip():
            formatted_reply = markdown_to_html(assistant_reply)
            await message.reply_text(formatted_reply, parse_mode=ParseMode.HTML)
            
            # Уменьшаем баланс пользователя
            async with async_session() as session:
                user = await session.get(User, user_id)
                user.remaining_tasks -= 1
                user.solved_tasks_count += 1
                await session.commit()
        else:
            await message.reply_text("Ответ от ассистента пуст или имеет неверный формат.")
    except Exception as e:
        logging.error(f"Ошибка при обработке запроса пользователя {user_id}: {e}")
        await message.reply_text("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.")

def get_subject_instruction(subject_key):
    """
    Получает инструкцию для заданного предмета.
    """
    # Можно хранить инструкции в словаре, как показано ниже,
    # либо загрузить их из .env или других файлов
    instructions = {
        'math': os.getenv("INSTRUCTION_MATH"),
        'russian': os.getenv("INSTRUCTION_RUSSIAN"),
        'literature': os.getenv("INSTRUCTION_LITERATURE"),
        'english': os.getenv("INSTRUCTION_ENGLISH"),
        'physics': os.getenv("INSTRUCTION_PHYSICS"),
        'chemistry': os.getenv("INSTRUCTION_CHEMISTRY"),
        'biology': os.getenv("INSTRUCTION_BIOLOGY"),
        'history': os.getenv("INSTRUCTION_HISTORY"),
        'social_studies': os.getenv("INSTRUCTION_SOCIAL_STUDIES"),
        'geography': os.getenv("INSTRUCTION_GEOGRAPHY"),
        'informatics': os.getenv("INSTRUCTION_INFORMATICS"),
        'other': os.getenv("INSTRUCTION_OTHER")
    }
    return instructions.get(subject_key)

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

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info("Команда /buy от пользователя %s", user_id)

    # Пример тарифов
    tariffs = {
        "10 заданий": {"price": 99, "task_limit": 10},
        "50 заданий": {"price": 390, "task_limit": 50},
        "100 заданий": {"price": 690, "task_limit": 100}
    }

    # Генерация кнопок с реальными ссылками на оплату
    keyboard = []
    for name, info in tariffs.items():
        price = info["price"]
        tasks = info["task_limit"]
        # Вычисляем стоимость за одно сообщение (округление до 1 знака)
        price_per_task = round(price / tasks, 1)

        payment_url = create_payment(
            amount=price,
            description=f"Покупка тарифа: {name}",
            user_id=user_id,
            tariff_name=name
        )
        if payment_url:
            # Добавляем в текст кнопки информацию о цене за 1 сообщение
            button_text = f"{name} - {price}₽ (~{price_per_task}₽/сообщ.)"
            keyboard.append([InlineKeyboardButton(button_text, url=payment_url)])
        else:
            logging.error(f"Не удалось создать платеж для тарифа {name}")

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите тариф для оплаты:", reply_markup=reply_markup)

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
    # test_user_id = ADMIN_ID

    caption = message.caption if message.caption else message.text if message.text else ""

    if message.photo:
        file_id = message.photo[-1].file_id
        count = 0  # Счётчик отправленных сообщений
        for user in users:
            #if user.id != test_user_id: # тестовая отправка только себе
            #    continue # тестовая отправка только себе
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
            #if user.id != test_user_id: # тестовая отправка только себе
            #    continue # тестовая отправка только себе
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

def main():
    logging.info("Запуск бота")
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Установка команд бота
    application.bot.set_my_commands([
        BotCommand("subject", "Выбрать предмет"),
        BotCommand("balance", "Проверить баланс"),
        BotCommand("buy", "Купить задания"),
        BotCommand("help", "Получить помощь"),
        BotCommand("feedback", "Оставить отзыв"),
        BotCommand("klass", "Изменить класс"),
        BotCommand("referral", "Получить реферальный код")
    ])

    # Обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("klass", klass_command))
    application.add_handler(CommandHandler("subject", subject_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("referral", referral_command))

    # Обработчик диалога для сбора отзывов
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('feedback', feedback_command)],
        states={FEEDBACK: [MessageHandler(filters.ALL, handle_feedback_message)]},
        fallbacks=[]
    ), group=0)
    
    # Обработчик диалога для команды /broadcast
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('broadcast', broadcast_command)],
        states={
            BROADCAST_COLLECT: [MessageHandler(filters.ALL, collect_broadcast_message)],
        },
        fallbacks=[],
    ), group=0)

    # Обработчики CallbackQuery
    application.add_handler(CallbackQueryHandler(klass_button_handler, pattern='^class_'))
    application.add_handler(CallbackQueryHandler(subject_selected, pattern='^subject_'))

    # Обработчики сообщений от пользователя для основного функционала
    application.add_handler(MessageHandler(filters.PHOTO, handle_user_message), group=1)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message), group=1)

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()