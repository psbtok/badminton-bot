import os
from pathlib import Path
from handlers.cancel_handler import register_cancel_handlers
import telebot
from event_service import EventService
from db_operations import DBOperations
from locales import LOCALES
from handlers.event_handler import register_event_handlers
from handlers.register_handler import register_register_handlers
from migrate import run_migrations

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

token = os.environ.get('BOT_API_KEY')
bot = telebot.TeleBot(token)
event_service = EventService()
db_ops = DBOperations()

# Migrations will be run when a user issues /start to ensure environment is ready

@bot.message_handler(commands=['start'])
def handle_start(message):
    event_service.create_tables_if_not_exist()
    try:
        run_migrations()
    except Exception as e:
        print('Migration error on /start:', e)
    bot.reply_to(message, LOCALES["welcome"])

# Register event and registration handlers from handler modules
register_event_handlers(bot, event_service)
register_register_handlers(bot, event_service)
register_cancel_handlers(bot, event_service)


# @bot.middleware_handler(update_types=['message'])
# def debug_middleware(bot_instance, message):
#     print("MIDDLEWARE:", message)

if __name__ == "__main__":
    print("Bot is running...")
    bot.polling(none_stop=True)
