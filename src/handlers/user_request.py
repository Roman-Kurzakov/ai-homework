from aio_pika import connect, Message as RmqMessage
from aio_pika.abc import DeliveryMode

import json
import logging
from uuid import uuid4
import os

from telegram import Update
from telegram.ext import ContextTypes

from src.db import async_session
from src.models import User
from src.config import (
    RABBIT_PASS, RABBIT_LOGIN, RABBIT_HOST, RABBIT_PORT,
    QueueType, IMAGES_PATH)


logger = logging.getLogger(__name__)


async def get_connection():
    connection = await connect(
        host=RABBIT_HOST,
        port=int(RABBIT_PORT),
        login=RABBIT_LOGIN,
        password=RABBIT_PASS
    )
    return connection


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
    else:
        await message.reply_text("Принято. Решаю. \n\nБудьте внимательны, я могу ошибаться. Рекомендую проверять важную информацию.")

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

    if message.photo:
        # Обработка фото
        logging.info("Пользователь %s отправил фото", user_id)
        photo = message.photo[-1]
        photo_file = await photo.get_file()

        os.makedirs(IMAGES_PATH, exist_ok=True)
        custom_path = f"{IMAGES_PATH}/{uuid4()}.png"
        await photo_file.download_to_drive(custom_path=custom_path)

        # Формируем ввод для ассистента
        caption = message.caption if message.caption else ""

        user_input = {
            "text": None,
            "image_url": custom_path,
            "user_id": user_id,
            "caption": caption,
            "class_level": class_level,
            "subject": selected_subject
        }

    elif message.text:
        logging.info("Пользователь %s отправил текст: %s", user_id, message.text)
        # Новый блок просит адаптировать ответ под нужный класс
        user_input = {
            "text": message.text,
            "image_url": None,
            "user_id": user_id,
            "caption": None,
            "class_level": class_level,
            "subject": selected_subject
        }

    else:
        await message.reply_text("Пожалуйста, отправьте текст или изображение задания.")
        return

    async with await get_connection() as connection:
        async with connection.channel() as channel:
            rmq_message = RmqMessage(
                body=json.dumps(user_input).encode(),
                content_type="application/json",
                content_encoding="utf-8",
                message_id=uuid4().hex,
                delivery_mode=DeliveryMode.PERSISTENT,
                app_id="telegram_producer",
            )
            logging.info(f"Message is publishing with data: {user_input}")
            await channel.default_exchange.publish(
                message=rmq_message,
                routing_key=QueueType.AI_REQUEST
            )
