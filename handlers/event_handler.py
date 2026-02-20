from telebot import types
from locales import LOCALES
from utils.announce import announce_event
import datetime as _dt

def register_event_handlers(bot, event_service):
    user_event_state = {}

    def get_russian_date_buttons():
        today = _dt.datetime.now(_dt.timezone.utc)
        buttons = []
        for i in range(0, 11):
            date = today + _dt.timedelta(days=i)
            day = date.day
            month = LOCALES["month_names"][date.month - 1]
            btn_text = f"{day} {month}"
            buttons.append((btn_text, date.strftime("%Y-%m-%d")))
        return buttons

    def get_time_buttons():
        return [(f"{hour}:00", str(hour)) for hour in range(10, 21)]

    @bot.message_handler(commands=['event_create'])
    def handle_create_event(message):
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
            user_event_state[user_id]["awaiting_max_participants"] = True
            bot.edit_message_text(LOCALES["prompt_max_participants"], chat_id, call.message.message_id)
            return
        if call.data == "back":
            if "time_start" in user_event_state.get(user_id, {}):
                # Go back to time selection
                user_event_state[user_id].pop("time_start", None)
                user_event_state[user_id].pop("time_end", None)
                user_event_state[user_id].pop("awaiting_max_participants", None)
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
                event_id = event_service.create_event(
                    date=state["date"],
                    time_start=f"{state['time_start']}:00",
                    time_end=f"{state['time_end']}:00",
                    creator_id=user_id,
                    max_participants=state.get("max_participants")
                )
                try:
                    announce_event(bot, event_service, event_id, state["date"], state["time_start"], state["time_end"], max_participants=state.get("max_participants"))
                except Exception:
                    pass

                bot.edit_message_text(LOCALES["event_success"], chat_id, call.message.message_id)
            else:
                bot.edit_message_text(LOCALES["error"], chat_id, call.message.message_id)
            return

    @bot.message_handler(func=lambda message: user_event_state.get(message.from_user.id, {}).get("awaiting_max_participants"))
    def handle_max_participants_input(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        state = user_event_state.get(user_id, {})

        if not state or not state.get("awaiting_max_participants"):
            return

        try:
            max_participants = int(message.text)
            if max_participants == 0:
                state["max_participants"] = None
            elif max_participants > 0:
                state["max_participants"] = max_participants
            else:
                raise ValueError()
        except (ValueError, TypeError):
            bot.send_message(chat_id, LOCALES["invalid_format_number"])
            return

        state["awaiting_max_participants"] = False

        date_str = state["date"]
        time_start = state["time_start"]
        time_end = state["time_end"]
        dt = _dt.datetime.strptime(date_str, "%Y-%m-%d")
        month_name = LOCALES["month_names"][dt.month - 1]
        formatted_date = f"{dt.day} {month_name} {dt.year}"
        summary = f"{formatted_date} from {time_start:02d}:00 to {time_end:02d}:00"
        max_p = state['max_participants']
        if max_p:
            summary += LOCALES["participants_count_summary"].format(max_p=max_p)

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(LOCALES["confirm"], callback_data="confirm"))
        markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="back"))
        markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="cancel"))
        bot.send_message(chat_id, f"{LOCALES['confirm_event']}\n{summary}", reply_markup=markup)
