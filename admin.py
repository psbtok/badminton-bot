import os
from pathlib import Path
import telebot
from telebot import apihelper

from db_operations import DBOperations
from locales import LOCALES
from event_service import EventService
from handlers.cancel_handler import register_cancel_handlers
from handlers.event_handler import register_event_handlers
from handlers.register_handler import register_register_handlers
from migrate import run_migrations

# Load .env if present
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

ADMIN_USER_IDS = os.environ.get("ADMIN_USER_IDS", "")
ADMIN_USER_IDS = [
    int(user_id.strip())
    for user_id in ADMIN_USER_IDS.split(",")
    if user_id.strip().isdigit()
]

apihelper.ENABLE_MIDDLEWARE = True

token = os.environ.get('ADMIN_BOT_API_KEY')
bot = telebot.TeleBot(token)
event_service = EventService()
db_ops = DBOperations()


# --------------------------
# Admin-only enforcement
# --------------------------
original_process = bot.process_new_messages

def admin_process_wrapper(new_messages):
    for message in new_messages:
        if hasattr(message, 'from_user') and message.from_user.id not in ADMIN_USER_IDS:
            bot.send_message(message.chat.id, "У вас нет прав для этого действия.")
            continue
        original_process([message])  # allow message for admins

bot.process_new_messages = admin_process_wrapper
# --------------------------


# Migrations will be run when a user issues /start to ensure environment is ready
@bot.message_handler(commands=['start'])
def handle_start(message):
    event_service.create_tables_if_not_exist()
    try:
        run_migrations()
    except Exception as e:
        print('Migration error on /start:', e)
    bot.reply_to(message, LOCALES["welcome_admin"])


# Register event and registration handlers from handler modules
register_event_handlers(bot, event_service)
register_register_handlers(bot, event_service)
register_cancel_handlers(bot, event_service)

if __name__ == "__main__":
    print("Admin bot is running.")
    bot.polling(none_stop=True)
