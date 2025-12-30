
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


def send_summary(chat_id, state, message_id=None):
    date = state.get('date', 'Не выбрано')
    time = state.get('time', 'Не выбрано')
    name = state.get('name', state.get('default_name', 'Не выбрано'))
    text = f"Вы выбрали:\n" \
           f"\U0001F4C5 Дата: {date}\n" \
           f"\u23F0 Время: {time}\n" \
           f"\U0001F464 Имя: {name}\n"
    markup = types.InlineKeyboardMarkup()
    if not state.get('date'):
        for d in available_data["availableDates"]:
            markup.add(types.InlineKeyboardButton(d["date"], callback_data=f"date_{d['date']}"))
        markup.add(types.InlineKeyboardButton("Отмена", callback_data="cancel"))
    elif not state.get('time'):
        times = next((d['times'] for d in available_data['availableDates'] if d['date'] == state['date']), [])
        for t in times:
            markup.add(types.InlineKeyboardButton(t, callback_data=f"time_{t}"))
        markup.add(types.InlineKeyboardButton("Назад", callback_data="back_to_date"))
    elif not state.get('name'):
        markup.add(types.InlineKeyboardButton("Использовать имя Telegram", callback_data="name_tg"))
        markup.add(types.InlineKeyboardButton("Ввести имя вручную", callback_data="name_manual"))
        markup.add(types.InlineKeyboardButton("Назад", callback_data="back_to_time"))
    else:
        markup.add(types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"))
        markup.add(types.InlineKeyboardButton("🔄 Назад", callback_data="back_to_name"))
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='HTML')
    else:
        msg = bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')
        return msg


@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def cancel_registration(call):
    chat_id = call.message.chat.id
    data = user_states.get(chat_id, {})
    msg_id = data.get('summary_msg_id') or call.message.message_id
    try:
        bot.edit_message_text("Запись прервана", chat_id, msg_id, reply_markup=None)
    except Exception:
        try:
            bot.send_message(chat_id, "Запись прервана")
        except Exception:
            pass

@bot.message_handler(commands=['register'])
def register(message):
    bot.send_message(message.chat.id, "Запуск регистрации...", reply_markup=types.ReplyKeyboardRemove())

    chat_id = message.chat.id
    default_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip() or "Гость"
    user_states[chat_id] = {'default_name': default_name}
    msg = send_summary(chat_id, user_states[chat_id])
    user_states[chat_id]['summary_msg_id'] = msg.message_id


@bot.callback_query_handler(func=lambda call: call.data.startswith('date_'))
def handle_date(call):
    chat_id = call.message.chat.id
    date_selected = call.data.replace('date_', '')
    user_states[chat_id]['date'] = date_selected
    send_summary(chat_id, user_states[chat_id], user_states[chat_id]['summary_msg_id'])


@bot.callback_query_handler(func=lambda call: call.data.startswith('time_'))
def handle_time(call):
    chat_id = call.message.chat.id
    time_selected = call.data.replace('time_', '')
    user_states[chat_id]['time'] = time_selected
    send_summary(chat_id, user_states[chat_id], user_states[chat_id]['summary_msg_id'])


@bot.callback_query_handler(func=lambda call: call.data.startswith('name_'))
def handle_name_choice(call):
    chat_id = call.message.chat.id
    if call.data == 'name_tg':
        name = f"{call.from_user.first_name or ''} {call.from_user.last_name or ''}".strip() or "Гость"
        user_states[chat_id]['name'] = name
        send_summary(chat_id, user_states[chat_id], user_states[chat_id]['summary_msg_id'])
    elif call.data == 'name_manual':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Назад", callback_data="back_to_name"))
        msg = bot.edit_message_text("Пожалуйста, введите ваше имя:", chat_id, call.message.message_id, reply_markup=markup)
        bot.register_next_step_handler(msg, handle_manual_name)


def handle_manual_name(message):
    chat_id = message.chat.id
    name = message.text.strip()
    user_states[chat_id]['name'] = name
    # Удаляем сообщение с ручным вводом имени
    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass
    send_summary(chat_id, user_states[chat_id], user_states[chat_id]['summary_msg_id'])


# Обработчики кнопок "Назад"
@bot.callback_query_handler(func=lambda call: call.data == 'back_to_date')
def back_to_date(call):
    chat_id = call.message.chat.id
    user_states[chat_id].pop('date', None)
    user_states[chat_id].pop('time', None)
    user_states[chat_id].pop('name', None)
    send_summary(chat_id, user_states[chat_id], user_states[chat_id]['summary_msg_id'])

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_time')
def back_to_time(call):
    chat_id = call.message.chat.id
    user_states[chat_id].pop('time', None)
    user_states[chat_id].pop('name', None)
    send_summary(chat_id, user_states[chat_id], user_states[chat_id]['summary_msg_id'])

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_name')
def back_to_name(call):
    chat_id = call.message.chat.id
    user_states[chat_id].pop('name', None)
    send_summary(chat_id, user_states[chat_id], user_states[chat_id]['summary_msg_id'])

@bot.callback_query_handler(func=lambda call: call.data == 'confirm')
def confirm_registration(call):
    chat_id = call.message.chat.id
    data = user_states.get(chat_id, {})
    date = data.get('date', '-')
    time = data.get('time', '-')
    name = data.get('name', data.get('default_name', '-'))
    text = f"Вы записаны на {date} в {time} на имя: {name}"
    try:
        bot.edit_message_reply_markup(chat_id, data['summary_msg_id'])
    except Exception:
        pass
    bot.send_message(chat_id, text)


# Показываем кнопку 'Регистрация' внизу экрана до начала регистрации
main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(types.KeyboardButton('Регистрация'))

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "<b>Привет!</b> Я бот для записи на бадминтон. Нажмите кнопку 'Регистрация' внизу экрана, чтобы записаться.", parse_mode='HTML', reply_markup=main_keyboard)

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'регистрация')
def registration_button_handler(message):
    # Убираем клавиатуру и запускаем регистрацию
    register(message)



bot.polling(none_stop=True)