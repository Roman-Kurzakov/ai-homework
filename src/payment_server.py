from flask import Flask, request, jsonify
import logging
from decimal import Decimal
import requests
import base64

from src.db import async_session
from src.models import User, Transaction, Pricing
from telegram import Bot
from src.config import SHOP_ID, SECRET_KEY, TELEGRAM_TOKEN

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)


def check_payment_status(payment_id):
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


def handle_successful_payment(user_id: int, tariff_name: str, amount_decimal: Decimal) -> None:
    """
    Вызывается при успешной оплате пользователем user_id тарифа tariff_name.
    Например: '10 задач', '50 задач', '100 задач'.
    """
    with async_session() as session:
        user = session.query(User).filter_by(id=user_id).first()
        pricing = session.query(Pricing).filter_by(name=tariff_name).first()

        if not user:
            user = User(id=user_id)
            session.add(user)
            session.commit()

        if not pricing:
            logging.error(f"Тариф '{tariff_name}' не найден в таблице Pricing.")
            return

        current_count = user.solved_tasks_count or 0
        user.remaining_tasks += pricing.task_limit
        user.subscription_type = "package"
        user.solved_tasks_count = current_count

        logging.info(
            f"Пользователь {user_id} получил +{pricing.task_limit} заданий (тариф: {tariff_name})."
        )
        message_text = (
            f"Спасибо за покупку!\nВаш баланс пополнен на {pricing.task_limit} заданий."
        )

        # Создаём транзакцию
        transaction = Transaction(
            user_id=user_id,
            pricing_id=pricing.id,
            amount=amount_decimal,
            status="success"
        )
        session.add(transaction)
        session.commit()

    # Отправляем сообщение пользователю в Телеграм
    bot.send_message(chat_id=user_id, text=message_text)
    logging.info(f"Баланс пользователя {user_id} обновлен и уведомление отправлено.")


# https://124.15.14.1.:80/payment/notification
@app.route('/payment/notification', methods=['POST'])
def payment_notification():
    data = request.json
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

            # Получаем сумму из уведомления
            amount_str = payment_object['amount']['value']  # "99.00" -> Decimal("99.00")
            amount_decimal = Decimal(amount_str)

            # Вместо логики обновления здесь — единая функция:
            handle_successful_payment(user_id, tariff_name, amount_decimal)
        else:
            logging.error("Не указаны user_id или tariff_name в метаданных платежа.")

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    print("Сервер запущен на порту 8000...")
    app.run(port=8000)
