import asyncio
import aiohttp
from aiormq import connect
from aiormq.abc import DeliveredMessage
import base64
import logging
import os
from openai import AsyncOpenAI
import json
from typing import Optional

from src.db import async_session
from src.models import User
from src.utils import markdown_to_html
from src.config import (
    TELEGRAM_TOKEN, INSTRUCTIONS, OPENAI_API_KEY, RABBIT_HOST,
    RABBIT_LOGIN, RABBIT_PASS)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.proxyapi.ru/openai/v1"
)


class EventMessage:
    def __init__(self, message: DeliveredMessage):
        self._generation_data = json.loads(message.body.decode('utf-8'))

    @property
    def text(self) -> Optional[str]:
        return self._generation_data.get("text")

    @property
    def user_id(self) -> str:
        return self._generation_data.get("user_id")

    @property
    def class_level(self) -> str:
        return self._generation_data.get("class_level")

    @property
    def subject(self) -> str:
        return self._generation_data.get("subject")

    @property
    def image_url(self) -> Optional[str]:
        return self._generation_data.get("image_url")

    @property
    def caption(self) -> Optional[str]:
        return self._generation_data.get("caption")


async def send_message(token: str, chat_id: str, message: str) -> None:
    async with aiohttp.ClientSession() as session:
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        data = aiohttp.FormData()
        data.add_field('chat_id', chat_id)
        data.add_field('text', message)
        data.add_field('parse_mode', 'HTML')

        async with session.post(url, data=data) as response:
            await response.text()


def convert_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:image/png;base64,{encoded_string}"


async def handle_message(message):
    event_message = EventMessage(message)

    await message.channel.basic_ack(
        message.delivery.delivery_tag
    )

    logger.info(
        f"Starting generate from message "
        f"user_id={event_message.user_id}, "
        f"class_level={event_message.class_level}, "
        f"subject={event_message.subject}"
    )

    try:
        subject_instruction = INSTRUCTIONS.get(event_message.subject)
        if not subject_instruction:
            await send_message(
                token=TELEGRAM_TOKEN,
                chat_id=event_message.user_id,
                message="Не удалось найти инструкцию для выбранного предмета."
            )
            return

        if event_message.image_url:
            image_data_url = convert_image_to_base64(event_message.image_url)
            os.remove(event_message.image_url)
            user_input = [
                {
                    "type": "text",
                    "text": f"{event_message.caption or ''}"
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_data_url}
                },
            ]
        else:
            user_input = [
                {
                    "type": "text",
                    "text": f"{event_message.text or ''}"
                }
            ]

        messages = [
            {
                "role": "system",
                "content": f"Класс: {event_message.class_level}\n\n{subject_instruction}"
            },
            {
                "role": "user",
                "content": user_input
            }
        ]

        # Сокращённое логирование: показываем только первую сотню символов system/user
        system_preview = messages[0]["content"].replace('\n', '\\n')[:100]
        user_preview = str(messages[1]["content"])[:100]

        logger.info(
            f"OpenAI messages => system: \"{system_preview}\" | user: \"{user_preview}\""
        )

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
            user=str(event_message.user_id)
        )

        assistant_reply = response.choices[0].message.content

        if assistant_reply.strip():
            formatted_reply = markdown_to_html(assistant_reply)
            await send_message(
                token=TELEGRAM_TOKEN,
                chat_id=event_message.user_id,
                message=formatted_reply
            )
            async with async_session() as session:
                user = await session.get(User, int(event_message.user_id))
                user.remaining_tasks -= 1
                user.solved_tasks_count += 1
                await session.commit()
        else:
            await send_message(
                token=TELEGRAM_TOKEN,
                chat_id=event_message.user_id,
                message="Ответ от ассистента пуст или имеет неверный формат."
            )

    except Exception as e:
        logging.error(f"Ошибка при обработке запроса пользователя {event_message.user_id}: {e}")
        await send_message(
            token=TELEGRAM_TOKEN,
            chat_id=event_message.user_id,
            message="Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
        )


async def main() -> None:
    connection = await connect(
        f"amqp://{RABBIT_LOGIN}:{RABBIT_PASS}@{RABBIT_HOST}/"
    )

    logger.info("Start consuming")

    channel_generator = await connection.channel()
    await channel_generator.basic_qos(prefetch_count=10)
    declare_ok_generator = await channel_generator.queue_declare("ai_request_queue", durable=True)
    await channel_generator.basic_consume(declare_ok_generator.queue, handle_message)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_forever()
