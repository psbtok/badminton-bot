import telebot
from event_service import EventService
from db_operations import DBOperations
from locales import LOCALES
from handlers.event_handler import register_event_handlers
from handlers.register_handler import register_register_handlers

bot = telebot.TeleBot('8355692996:AAGllY4NycCAQlnP5O5y06NdNx7MCwW44Ok')
event_service = EventService()
db_ops = DBOperations()


@bot.message_handler(commands=['start'])
def handle_start(message):
    event_service.create_tables_if_not_exist()
    bot.reply_to(message, LOCALES["welcome"])


@bot.message_handler(commands=['restart'])
def handle_restart(message):
    db_ops.delete_db()
    event_service.create_tables_if_not_exist()
    bot.reply_to(message, LOCALES["start"])


# Register event and registration handlers from handler modules
register_event_handlers(bot, event_service)
register_register_handlers(bot, event_service)


if __name__ == "__main__":
    print("Bot is running...")
    bot.polling(none_stop=True)
