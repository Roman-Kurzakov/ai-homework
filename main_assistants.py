import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ConversationHandler,
    MessageHandler, filters, CallbackQueryHandler)

from src.config import TELEGRAM_TOKEN
from src.handlers import (
    start_command, klass_command, subject_command, balance_command,
    buy_command, help_command, referral_command, feedback_command,
    handle_feedback_message, broadcast_command, collect_broadcast_message,
    klass_button_handler, subject_selected, handle_user_message, FEEDBACK,
    BROADCAST_COLLECT)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def main():
    logging.info("Запуск бота")
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

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
            BROADCAST_COLLECT: [
                MessageHandler(filters.ALL, collect_broadcast_message)
            ],
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
