from telebot import types
from locales import LOCALES
import requests
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

    @bot.message_handler(commands=['create'])
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
            date_str = user_event_state[user_id]["date"]
            time_start = user_event_state[user_id]["time_start"]
            time_end = user_event_state[user_id]["time_end"]
            dt = _dt.datetime.strptime(date_str, "%Y-%m-%d")
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
                event_id = event_service.create_event(
                    date=state["date"],
                    time_start=f"{state['time_start']}:00",
                    time_end=f"{state['time_end']}:00",
                    creator_id=user_id
                )
                # Prepare announcement text
                formatted_date = None
                try:
                    dt = _dt.datetime.strptime(state["date"], "%Y-%m-%d")
                    month_name = LOCALES["month_names"][dt.month - 1]
                    formatted_date = f"{dt.day} {month_name} {dt.year}"
                except Exception:
                    formatted_date = state["date"]
                time_start = state["time_start"]
                time_end = state["time_end"]
                summary = f"{formatted_date} с {time_start:02d}:00 до {time_end:02d}:00"
                announce = LOCALES.get("channel_announce", "Объявляется тренировка:\n{summary}").format(summary=summary)

                # Try creating a forum topic (thread) in the channel/supergroup, fallback to simple post
                channel = "@badmintonOleArena"
                token = getattr(bot, 'token', None) or getattr(bot, '_token', None)
                thread_id = None
                sent_msg = None
                try:
                    # Attempt to create a forum topic via Bot API
                    if token:
                        topic_name = summary[:128]
                        resp = requests.post(
                            f"https://api.telegram.org/bot{token}/createForumTopic",
                            data={"chat_id": channel, "name": topic_name}
                        )
                        j = resp.json()
                        if j.get("ok") and "result" in j:
                            thread_id = j["result"].get("message_thread_id")

                    # Send announcement (into thread if created)
                    if thread_id:
                        sent_msg = bot.send_message(channel, announce, message_thread_id=int(thread_id))
                    else:
                        sent_msg = bot.send_message(channel, announce)
                except Exception:
                    sent_msg = None

                # Persist announcement location if we have a sent message
                if sent_msg is not None:
                    try:
                        msg_id = getattr(sent_msg, 'message_id', None)
                        event_service.set_event_announcement(event_id, channel, msg_id, thread_id)
                    except Exception:
                        pass

                bot.edit_message_text(LOCALES["event_success"], chat_id, call.message.message_id)
            else:
                bot.edit_message_text(LOCALES["error"], chat_id, call.message.message_id)
            return
