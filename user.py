import os
from pathlib import Path
import telebot

from event_service import EventService
from event_service import EventService
from locales import LOCALES
from handlers.cancel_handler import register_cancel_handlers
from handlers.calendar_handler import register_calendar_handlers
from handlers.register_handler import register_register_handlers

# Load .env if present (simple loader, no extra dependency)
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())


# from telebot import apihelper
# apihelper.ENABLE_MIDDLEWARE = True

token = os.environ.get('USER_BOT_API_KEY')
bot = telebot.TeleBot(token)
event_service = EventService()
db_ops = EventService()

# Migrations will be run when a user issues /start to ensure environment is ready

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, LOCALES["welcome"])

# Register event and registration handlers from handler modules
register_register_handlers(bot, event_service)
register_cancel_handlers(bot, event_service)
register_calendar_handlers(bot, db_ops)


# @bot.middleware_handler(update_types=['message'])
# def debug_middleware(bot_instance, message):
#     print("MIDDLEWARE:", message)

if __name__ == "__main__":
    print("User bot is running.")
    bot.polling(none_stop=True)
