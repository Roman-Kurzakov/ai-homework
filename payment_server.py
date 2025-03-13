from quart import Quart, request, jsonify
import logging
from decimal import Decimal
import requests
import base64
from telegram import Bot
from telegram.constants import ParseMode
from src.config import SHOP_ID, SECRET_KEY, TELEGRAM_TOKEN
from src.db import async_session
from src.models import User, Transaction, Pricing
from sqlalchemy import select

logger = logging.getLogger(__name__)

app = Quart(__name__)
bot = Bot(token=TELEGRAM_TOKEN)


def check_payment_status(payment_id):
    # Для тестирования: если ID начинается с "test_", всегда возвращаем успешный статус
    if payment_id.startswith('test_'):
        logging.info(f"Тестовый платеж {payment_id}")
        return {
            "status": "succeeded",
            "id": payment_id,
            "amount": {
                "value": "99.00",
                "currency": "RUB"
            },
            "paid": True
        }

    # Реальная проверка для боевых платежей
    url = f"https://api.yookassa.ru/v3/payments/{payment_id}"
    auth = base64.b64encode(f"{SHOP_ID}:{SECRET_KEY}".encode()).decode()

    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        logging.error("Ошибка при проверке статуса платежа: %s", response.text)
        return None


async def send_telegram_message(user_id: int, message_text: str):
    await bot.send_message(chat_id=user_id, text=message_text, parse_mode=ParseMode.HTML)


async def handle_successful_payment(user_id: int, tariff_name: str, amount_decimal: Decimal) -> None:
    """Асинхронная обработка успешного платежа"""
    async with async_session() as session:
        # Получаем пользователя
        user = await session.get(User, user_id)
        if not user:
            user = User(id=user_id, remaining_tasks=0, solved_tasks_count=0)
            session.add(user)

        # Получаем тариф
        stmt = select(Pricing).where(Pricing.name == tariff_name)
        result = await session.execute(stmt)
        pricing = result.scalar_one_or_none()

        # Если тариф не найден, используем фиксированные значения
        if pricing is None:
            task_limit = {
                "10 заданий": 10,
                "50 заданий": 50,
                "100 заданий": 100
            }.get(tariff_name, 0)
            
            transaction = Transaction(
                user_id=user_id,
                amount=amount_decimal,
                status="success"
            )
        else:
            task_limit = pricing.task_limit
            transaction = Transaction(
                user_id=user_id,
                pricing_id=pricing.id,
                amount=amount_decimal,
                status="success"
            )

        # Обновляем баланс пользователя
        user.remaining_tasks += task_limit
        user.subscription_type = "package"
        
        session.add(transaction)
        await session.commit()

        logging.info(f"Пользователь {user_id} получил +{task_limit} заданий (тариф: {tariff_name}).")

    # Отправляем сообщение пользователю
    message_text = f"✅ Спасибо за покупку!\nВаш баланс пополнен на {task_limit} заданий по тарифу «{tariff_name}»."
    await bot.send_message(chat_id=user_id, text=message_text, parse_mode=ParseMode.HTML)


@app.route('/payment/notification', methods=['POST'])
async def payment_notification():
    """Асинхронный обработчик уведомлений"""
    data = await request.get_json()
    logging.info("Получено уведомление: %s", data)

    if data.get("event") == "payment.succeeded":
        payment_object = data["object"]
        payment_id = payment_object["id"]
        status_data = check_payment_status(payment_id)
        logging.info(f"Платёж {payment_id} обработан. Статус: {status_data.get('status')}")

        metadata = payment_object.get("metadata", {})
        user_id = metadata.get("user_id")
        tariff_name = metadata.get("tariff_name")

        if user_id and tariff_name:
            try:
                user_id = int(user_id)
            except ValueError:
                logging.error("user_id не число.")
                return jsonify({"status": "ok"}), 200

            amount_str = payment_object['amount']['value']
            amount_decimal = Decimal(amount_str)

            await handle_successful_payment(user_id, tariff_name, amount_decimal)

    return jsonify({"status": "ok"}), 200




