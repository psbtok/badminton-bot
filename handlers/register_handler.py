from telebot import types
from locales import LOCALES
import traceback

def register_register_handlers(bot, event_service):
    register_state = {}

    def get_all_trainings():
        import datetime
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
            import datetime
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
                # Update announcement message in channel/thread with participants list
                try:
                    event_id = state["event_id"]
                    # Fetch announcement info
                    announce_chat, announce_msg_id, announce_thread = event_service.get_event_announcement(event_id)
                    if announce_chat and announce_msg_id:
                        # Build participants list
                        rows = event_service.db.cursor.execute("SELECT name FROM event_participants WHERE event_id = ?", (event_id,)).fetchall()
                        names = [r[0] for r in rows]
                        count = len(names)
                        parts_text = "\n\nУчастники ({count}):\n".format(count=count)
                        for i, n in enumerate(names, start=1):
                            parts_text += f"{i}. {n}\n"

                        # Rebuild summary to include training info
                        row = event_service.db.cursor.execute("SELECT date, time_start, time_end FROM events WHERE id = ?", (event_id,)).fetchone()
                        if row:
                            import datetime as _dt
                            date_str, time_start, time_end = row
                            dt = _dt.datetime.strptime(date_str, "%Y-%m-%d")
                            month_name = LOCALES["month_names"][dt.month - 1]
                            formatted_date = f"{dt.day} {month_name} {dt.year}"
                            summary = f"{formatted_date} с {int(time_start.split(':')[0]):02d}:00 до {int(time_end.split(':')[0]):02d}:00"
                        else:
                            summary = ""

                        announce = LOCALES.get("channel_announce", "Новая тренировка:\n{summary}").format(summary=summary)
                        new_text = announce + parts_text
                        try:
                            if announce_thread:
                                bot.edit_message_text(new_text, announce_chat, announce_msg_id, message_thread_id=int(announce_thread))
                            else:
                                bot.edit_message_text(new_text, announce_chat, announce_msg_id)
                        except Exception:
                            # ignore editing failures
                            pass
                except Exception:
                    traceback.print_exc()
                # Get event info for confirmation message
                row = event_service.db.cursor.execute("SELECT date, time_start, time_end FROM events WHERE id = ?", (state["event_id"],)).fetchone()
                if row:
                    date_str, time_start, time_end = row
                    import datetime
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
        row = event_service.db.cursor.execute("SELECT date, time_start, time_end FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            bot.send_message(chat_id, LOCALES["error"])
            return
        date_str, time_start, time_end = row
        import datetime
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        month_name = LOCALES["month_names"][dt.month - 1]
        formatted_date = f"{dt.day} {month_name} {dt.year} с {time_start} до {time_end}"
        summary = LOCALES["register_summary"].format(training=formatted_date, name=register_state[user_id]['name'])
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(LOCALES["confirm"], callback_data="reg_confirm"))
        markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="reg_back"))
        markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="reg_cancel"))
        bot.send_message(chat_id, LOCALES["register_check"].format(summary=summary), reply_markup=markup)
