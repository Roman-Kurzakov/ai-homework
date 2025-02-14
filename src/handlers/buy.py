import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.utils import create_payment


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


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
