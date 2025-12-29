
import telebot
from telebot import types

# Доступные даты и время
available_data = {
    "availableDates": [
        {
            "date": "10.12.2025",
            "times": ["18:00 - 20:00", "20:00 - 22:00"]
        },
        {
            "date": "12.12.2025",
            "times": ["18:00 - 20:00", "20:00 - 22:00"]
        }
    ]
}

# Бот по записи на бадминтон


bot = telebot.TeleBot('8355692996:AAGllY4NycCAQlnP5O5y06NdNx7MCwW44Ok')

# Для хранения данных пользователя на время регистрации
user_states = {}


def send_date_selection(chat_id, message_id=None):
    markup = types.InlineKeyboardMarkup()
    for date in available_data["availableDates"]:
        markup.add(types.InlineKeyboardButton(date["date"], callback_data=f"date_{date['date']}"))
    if message_id:
        bot.edit_message_text("Пожалуйста, выберите дату:", chat_id, message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, "Пожалуйста, выберите дату:", reply_markup=markup)

@bot.message_handler(commands=['register'])
def register(message):
    chat_id = message.chat.id
    user_states[chat_id] = {}
    send_date_selection(chat_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('date_'))
def handle_date(call):
    chat_id = call.message.chat.id
    date_selected = call.data.replace('date_', '')
    user_states[chat_id]['date'] = date_selected
    # Найти доступные времена для выбранной даты
    times = next((d['times'] for d in available_data['availableDates'] if d['date'] == date_selected), [])
    markup = types.InlineKeyboardMarkup()
    for t in times:
        markup.add(types.InlineKeyboardButton(t, callback_data=f"time_{t}"))
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back_to_date"))
    bot.edit_message_text("Пожалуйста, выберите время:", chat_id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('time_'))
def handle_time(call):
    chat_id = call.message.chat.id
    time_selected = call.data.replace('time_', '')
    user_states[chat_id]['time'] = time_selected
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Использовать имя Telegram", callback_data="name_tg"))
    markup.add(types.InlineKeyboardButton("Ввести имя вручную", callback_data="name_manual"))
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back_to_time"))
    bot.edit_message_text("Пожалуйста, выберите способ ввода имени:", chat_id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('name_'))
def handle_name_choice(call):
    chat_id = call.message.chat.id
    if call.data == 'name_tg':
        name = call.from_user.first_name or "Гость"
        user_states[chat_id]['name'] = name
        confirm_registration(chat_id, call.message.message_id)
    elif call.data == 'name_manual':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Назад", callback_data="back_to_name"))
        msg = bot.edit_message_text("Пожалуйста, введите ваше имя:", chat_id, call.message.message_id, reply_markup=markup)
        bot.register_next_step_handler(msg, handle_manual_name)


def handle_manual_name(message):
    chat_id = message.chat.id
    name = message.text.strip()
    user_states[chat_id]['name'] = name
    confirm_registration(chat_id, message.message_id)


# Обработчики кнопок "Назад"
@bot.callback_query_handler(func=lambda call: call.data == 'back_to_date')
def back_to_date(call):
    chat_id = call.message.chat.id
    user_states[chat_id].pop('date', None)
    send_date_selection(chat_id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_time')
def back_to_time(call):
    chat_id = call.message.chat.id
    date_selected = user_states[chat_id].get('date')
    if not date_selected:
        send_date_selection(chat_id, call.message.message_id)
        return
    times = next((d['times'] for d in available_data['availableDates'] if d['date'] == date_selected), [])
    markup = types.InlineKeyboardMarkup()
    for t in times:
        markup.add(types.InlineKeyboardButton(t, callback_data=f"time_{t}"))
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back_to_date"))
    bot.edit_message_text("Пожалуйста, выберите время:", chat_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_name')
def back_to_name(call):
    chat_id = call.message.chat.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Использовать имя Telegram", callback_data="name_tg"))
    markup.add(types.InlineKeyboardButton("Ввести имя вручную", callback_data="name_manual"))
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back_to_time"))
    bot.edit_message_text("Пожалуйста, выберите способ ввода имени:", chat_id, call.message.message_id, reply_markup=markup)

def confirm_registration(chat_id, message_id):
    data = user_states.get(chat_id, {})
    date = data.get('date', '-')
    time = data.get('time', '-')
    name = data.get('name', '-')
    text = f"Вы записаны на {date} в {time} для имени: {name}"
    # Remove buttons from the previous message (edit to plain text, no reply_markup)
    try:
        bot.edit_message_reply_markup(chat_id, message_id)
    except Exception:
        pass
    bot.send_message(chat_id, text)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "<b>Привет!</b> Я бот для записи на бадминтон. Используй команду /register чтобы записаться.", parse_mode='HTML')



bot.polling(none_stop=True)