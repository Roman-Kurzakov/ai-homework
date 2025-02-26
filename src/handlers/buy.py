import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.utils import create_payment


logger = logging.getLogger(__name__)


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info("Команда /buy от пользователя %s", user_id)

    # Пример тарифов
    tariffs = {
        "10 заданий": {"price": 99, "task_limit": 10},
        "50 заданий": {"price": 390, "task_limit": 50},
        "100 заданий": {"price": 690, "task_limit": 100}
    }

    # Генерация кнопок без ссылок, используя callback_data
    keyboard = []
    for name, info in tariffs.items():
        price = info["price"]
        tasks = info["task_limit"]
        # Вычисляем стоимость за одно сообщение (округление до 1 знака)
        price_per_task = round(price / tasks, 1)

        # Используем callback_data для передачи выбранного тарифа
        button_text = f"{name} - {price}₽ (~{price_per_task}₽/сообщ.)"
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"tariff_{name}")
        ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите тариф для оплаты:", reply_markup=reply_markup)


async def tariff_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    selected_tariff = query.data.replace("tariff_", "")

    logging.info("Пользователь %s выбрал тариф: %s", user_id, selected_tariff)

    # Пример тарифов (тот же словарь, что и в buy_command)
    tariffs = {
        "10 заданий": {"price": 99, "task_limit": 10},
        "50 заданий": {"price": 390, "task_limit": 50},
        "100 заданий": {"price": 690, "task_limit": 100}
    }

    if selected_tariff in tariffs:
        info = tariffs[selected_tariff]
        price = info["price"]

        # Создаем платежную ссылку для выбранного тарифа
        payment_url = create_payment(
            amount=price,
            description=f"Покупка тарифа: {selected_tariff}",
            user_id=user_id,
            tariff_name=selected_tariff
        )

        if payment_url:
            # Отправляем сообщение с кнопкой "Оплатить"
            keyboard = [[InlineKeyboardButton("Оплатить", url=payment_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                f"Вы выбрали тариф \"{selected_tariff}\".\nНажмите кнопку ниже для оплаты:",
                reply_markup=reply_markup
            )
        else:
            logging.error("Не удалось создать платеж для тарифа %s", selected_tariff)
            await query.message.reply_text("Извините, произошла ошибка при создании платежа. Попробуйте позже.")
    else:
        await query.message.reply_text("Извините, выбранный тариф не найден.")
