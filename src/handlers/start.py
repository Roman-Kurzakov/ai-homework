import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.db import async_session
from src.models import User


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


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
