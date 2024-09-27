from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from config import TELEGRAM_BOT_TOKEN
from bot_handlers import start, handle_spotify_link

def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_spotify_link))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()