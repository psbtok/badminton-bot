import datetime
import telebot
from telebot import types
from event_service import EventService
from db_operations import DBOperations
from locales import LOCALES

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

user_event_state = {}
def get_russian_date_buttons():
    today = datetime.datetime.now(datetime.UTC)
    buttons = []
    for i in range(0, 11):
        date = today + datetime.timedelta(days=i)
        day = date.day
        month = LOCALES["month_names"][date.month - 1]
        btn_text = f"{day} {month}"
        buttons.append((btn_text, date.strftime("%Y-%m-%d")))
    return buttons

def get_time_buttons():
    return [(f"{hour}:00", str(hour)) for hour in range(10, 21)]

@bot.message_handler(commands=['create_event'])
def handle_create_event(message):
    print('hiii')
    user_id = message.from_user.id
    user_event_state[user_id] = {}
    markup = types.InlineKeyboardMarkup()
    for btn_text, date_val in get_russian_date_buttons():
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"date_{date_val}"))
    markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="cancel"))
    bot.send_message(message.chat.id, LOCALES["select_date"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("date_") or call.data == "cancel" or call.data.startswith("time_") or call.data == "back" or call.data == "confirm")
def handle_event_creation_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if call.data == "cancel":
        user_event_state.pop(user_id, None)
        bot.edit_message_text(LOCALES["event_cancelled"], chat_id, call.message.message_id)
        return
    if call.data.startswith("date_"):
        selected_date = call.data[5:]
        user_event_state[user_id] = {"date": selected_date}
        markup = types.InlineKeyboardMarkup()
        for btn_text, hour in get_time_buttons():
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"time_{hour}"))
        markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="back"))
        markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="cancel"))
        bot.edit_message_text(LOCALES["select_time"], chat_id, call.message.message_id, reply_markup=markup)
        return
    if call.data.startswith("time_"):
        selected_time = int(call.data[5:])
        user_event_state[user_id]["time_start"] = selected_time
        user_event_state[user_id]["time_end"] = selected_time + 2
        date_str = user_event_state[user_id]["date"]
        time_start = user_event_state[user_id]["time_start"]
        time_end = user_event_state[user_id]["time_end"]
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        month_name = LOCALES["month_names"][dt.month - 1]
        formatted_date = f"{dt.day} {month_name} {dt.year}"
        summary = f"{formatted_date} с {time_start:02d}:00 до {time_end:02d}:00"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(LOCALES["confirm"], callback_data="confirm"))
        markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="back"))
        markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="cancel"))
        bot.edit_message_text(f"{LOCALES["confirm_event"]}\n{summary}", chat_id, call.message.message_id, reply_markup=markup)
        return
    if call.data == "back":
        if "time_start" in user_event_state.get(user_id, {}):
            # Go back to time selection
            user_event_state[user_id].pop("time_start", None)
            user_event_state[user_id].pop("time_end", None)
            markup = types.InlineKeyboardMarkup()
            for btn_text, hour in get_time_buttons():
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"time_{hour}"))
            markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="back"))
            markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="cancel"))
            bot.edit_message_text(LOCALES["select_time"], chat_id, call.message.message_id, reply_markup=markup)
        else:
            # Go back to date selection
            markup = types.InlineKeyboardMarkup()
            for btn_text, date_val in get_russian_date_buttons():
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"date_{date_val}"))
            markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="cancel"))
            bot.edit_message_text(LOCALES["select_date"], chat_id, call.message.message_id, reply_markup=markup)
        return
    if call.data == "confirm":
        state = user_event_state.pop(user_id, None)
        if state and "date" in state and "time_start" in state and "time_end" in state:
            event_service.create_event(
                date=state["date"],
                time_start=f"{state['time_start']}:00",
                time_end=f"{state['time_end']}:00",
                creator_id=user_id
            )
            bot.edit_message_text(LOCALES["event_success"], chat_id, call.message.message_id)
        else:
            bot.edit_message_text(LOCALES["error"], chat_id, call.message.message_id)
        return

user_event_state = {}
def get_russian_date_buttons():
    today = datetime.datetime.utcnow()
    buttons = []
    for i in range(0, 11):
        date = today + datetime.timedelta(days=i)
        day = date.day
        month = LOCALES["month_names"][date.month - 1]
        btn_text = f"{day} {month}"
        buttons.append((btn_text, date.strftime("%Y-%m-%d")))
    return buttons
def get_time_buttons():
    return [(f"{hour}:00", str(hour)) for hour in range(10, 21)]

@bot.message_handler(commands=['create_event'])
def handle_create_event(message):
    print('hiii')
    user_id = message.from_user.id
    user_event_state[user_id] = {}
    markup = types.InlineKeyboardMarkup()
    for btn_text, date_val in get_russian_date_buttons():
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"date_{date_val}"))
    markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="cancel"))
    bot.send_message(message.chat.id, LOCALES["select_date"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("date_") or call.data == "cancel" or call.data.startswith("time_") or call.data == "back" or call.data == "confirm")
def handle_event_creation_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if call.data == "cancel":
        user_event_state.pop(user_id, None)
        bot.edit_message_text(LOCALES["event_cancelled"], chat_id, call.message.message_id)
        return
    if call.data.startswith("date_"):
        selected_date = call.data[5:]
        user_event_state[user_id] = {"date": selected_date}
        markup = types.InlineKeyboardMarkup()
        for btn_text, hour in get_time_buttons():
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"time_{hour}"))
        markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="back"))
        markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="cancel"))
        bot.edit_message_text(LOCALES["select_time"], chat_id, call.message.message_id, reply_markup=markup)
        return
    if call.data.startswith("time_"):
        selected_time = int(call.data[5:])
        user_event_state[user_id]["time_start"] = selected_time
        user_event_state[user_id]["time_end"] = selected_time + 2
        date = user_event_state[user_id]["date"]
        time_start = user_event_state[user_id]["time_start"]
        time_end = user_event_state[user_id]["time_end"]
        summary = LOCALES["event_summary"].format(date=date, time_start=f"{time_start}:00", time_end=f"{time_end}:00")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(LOCALES["confirm"], callback_data="confirm"))
        markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="back"))
        markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="cancel"))
        bot.edit_message_text(f"{LOCALES["confirm_event"]}\n{summary}", chat_id, call.message.message_id, reply_markup=markup)
        return
    if call.data == "back":
        if "time_start" in user_event_state.get(user_id, {}):
            # Go back to time selection
            user_event_state[user_id].pop("time_start", None)
            user_event_state[user_id].pop("time_end", None)
            markup = types.InlineKeyboardMarkup()
            for btn_text, hour in get_time_buttons():
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"time_{hour}"))
            markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="back"))
            markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="cancel"))
            bot.edit_message_text(LOCALES["select_time"], chat_id, call.message.message_id, reply_markup=markup)
        else:
            # Go back to date selection
            markup = types.InlineKeyboardMarkup()
            for btn_text, date_val in get_russian_date_buttons():
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"date_{date_val}"))
            markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="cancel"))
            bot.edit_message_text(LOCALES["select_date"], chat_id, call.message.message_id, reply_markup=markup)
        return
    if call.data == "confirm":
        state = user_event_state.pop(user_id, None)
        if state and "date" in state and "time_start" in state and "time_end" in state:
            event_service.create_event(
                date=state["date"],
                time_start=f"{state['time_start']}:00",
                time_end=f"{state['time_end']}:00",
                creator_id=user_id
            )
            bot.edit_message_text(LOCALES["event_success"], chat_id, call.message.message_id)
        else:
            bot.edit_message_text(LOCALES["error"], chat_id, call.message.message_id)
        return


register_state = {}
def get_all_trainings():
    # Returns list of (event_id, summary) for all trainings
    rows = event_service.db.cursor.execute("SELECT id, date, time_start, time_end FROM events").fetchall()
    result = []
    for row in rows:
        event_id, date_str, time_start, time_end = row
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        month_name = LOCALES["month_names"][dt.month - 1]
        formatted_date = f"{dt.day} {month_name} {dt.year} с {time_start} до {time_end}"
        result.append((event_id, formatted_date))
    return result
@bot.message_handler(commands=['register'])
def handle_register(message):
    user_id = message.from_user.id
    register_state[user_id] = {}
    markup = types.InlineKeyboardMarkup()
    for event_id, summary in get_all_trainings():
        markup.add(types.InlineKeyboardButton(summary, callback_data=f"reg_event_{event_id}"))
    markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="reg_cancel"))
    bot.send_message(message.chat.id, LOCALES["register_select_training"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reg_event_") or call.data == "reg_cancel" or call.data == "reg_back" or call.data == "reg_confirm" or call.data == "reg_use_tg_name" or call.data == "reg_enter_manually")
def handle_register_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if call.data == "reg_cancel":
        register_state.pop(user_id, None)
        bot.edit_message_text(LOCALES["register_cancelled"], chat_id, call.message.message_id)
        return
    if call.data.startswith("reg_event_"):
        event_id = int(call.data[len("reg_event_"):])
        register_state[user_id] = {"event_id": event_id}
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(LOCALES["register_use_tg_name"], callback_data="reg_use_tg_name"))
        markup.add(types.InlineKeyboardButton(LOCALES["register_enter_manually"], callback_data="reg_enter_manually"))
        markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="reg_back"))
        markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="reg_cancel"))
        bot.edit_message_text(LOCALES["register_choose_name"], chat_id, call.message.message_id, reply_markup=markup)
        return
    if call.data == "reg_use_tg_name":
        user = call.from_user
        name = (user.first_name or "") + (" " + user.last_name if user.last_name else "")
        register_state[user_id]["name"] = name.strip()
        event_id = register_state[user_id]["event_id"]
        row = event_service.db.cursor.execute("SELECT date, time_start, time_end FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            bot.edit_message_text(LOCALES["error"], chat_id, call.message.message_id)
            return
        date_str, time_start, time_end = row
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        month_name = LOCALES["month_names"][dt.month - 1]
        formatted_date = f"{dt.day} {month_name} {dt.year} с {time_start} до {time_end}"
        summary = LOCALES["register_summary"].format(training=formatted_date, name=register_state[user_id]['name'])
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(LOCALES["confirm"], callback_data="reg_confirm"))
        markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="reg_back"))
        markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="reg_cancel"))
        bot.edit_message_text(LOCALES["register_check"].format(summary=summary), chat_id, call.message.message_id, reply_markup=markup)
        return
    if call.data == "reg_enter_manually":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="reg_back"))
        markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="reg_cancel"))
        bot.edit_message_text(LOCALES["register_enter_name"], chat_id, call.message.message_id, reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, handle_register_name)
        return
    if call.data == "reg_back":
        markup = types.InlineKeyboardMarkup()
        for event_id, summary in get_all_trainings():
            markup.add(types.InlineKeyboardButton(summary, callback_data=f"reg_event_{event_id}"))
        markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="reg_cancel"))
        bot.edit_message_text(LOCALES["register_select_training"], chat_id, call.message.message_id, reply_markup=markup)
        return
    if call.data == "reg_confirm":
        state = register_state.pop(user_id, None)
        if state and "event_id" in state and "name" in state:
            event_service.db.cursor.execute(
                "INSERT INTO event_participants (event_id, participant_id, name) VALUES (?, ?, ?)",
                (state["event_id"], user_id, state["name"])
            )
            event_service.db.conn.commit()
            # Get event info for confirmation message
            row = event_service.db.cursor.execute("SELECT date, time_start, time_end FROM events WHERE id = ?", (state["event_id"],)).fetchone()
            if row:
                date_str, time_start, time_end = row
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                month_name = LOCALES["month_names"][dt.month - 1]
                formatted_date = f"{dt.day} {month_name} {dt.year} с {time_start} до {time_end}"
                confirm_msg = LOCALES["register_confirmed_full"].format(training=formatted_date, name=state["name"])
            else:
                confirm_msg = LOCALES["register_confirmed"]
            bot.edit_message_text(confirm_msg, chat_id, call.message.message_id)
        else:
            bot.edit_message_text(LOCALES["error"], chat_id, call.message.message_id)
        return

def handle_register_name(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_id not in register_state or "event_id" not in register_state[user_id]:
        bot.send_message(chat_id, LOCALES["error"])
        return
    register_state[user_id]["name"] = message.text.strip()
    event_id = register_state[user_id]["event_id"]
    # Show summary and confirm
    row = event_service.db.cursor.execute("SELECT date, time_start, time_end FROM events WHERE id = ?", (event_id,)).fetchone()
    if not row:
        bot.send_message(chat_id, LOCALES["error"])
        return
    date_str, time_start, time_end = row
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    month_name = LOCALES["month_names"][dt.month - 1]
    formatted_date = f"{dt.day} {month_name} {dt.year} с {time_start} до {time_end}"
    summary = LOCALES["register_summary"].format(training=formatted_date, name=register_state[user_id]['name'])
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(LOCALES["confirm"], callback_data="reg_confirm"))
    markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="reg_back"))
    markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="reg_cancel"))
    bot.send_message(chat_id, LOCALES["register_check"].format(summary=summary), reply_markup=markup)

if __name__ == "__main__":
    print("Bot is running...")
    bot.polling(none_stop=True)
