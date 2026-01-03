from telebot import types
from locales import LOCALES
import traceback
import datetime as _dt
from datetime import timezone
from utils.announce import announce_event

def register_register_handlers(bot, event_service):
    register_state = {}

    def get_all_trainings():
        rows = event_service.get_all_events()
        result = []
        for row in rows:
            event_id, date_str, time_start, time_end = row
            dt = _dt.datetime.strptime(date_str, "%Y-%m-%d")
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
            row = event_service.get_event(event_id)
            if not row:
                bot.edit_message_text(LOCALES["error"], chat_id, call.message.message_id)
                return
            date_str, time_start, time_end = row
            dt = _dt.datetime.strptime(date_str, "%Y-%m-%d")
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
            # Save the prompt message id so we can remove buttons after user sends name
            register_state.setdefault(user_id, {})["prompt_message_id"] = call.message.message_id
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
                joined_at = _dt.datetime.now(timezone.utc).isoformat()
                event_service.add_participant(state["event_id"], user_id, state["name"], joined_at)
                # Update announcement message in channel/thread with participants list
                try:
                    event_id = state["event_id"]
                    # Build participants list
                    rows = event_service.get_event_participants(event_id)
                    participants = [(r[0], r[1]) for r in rows]
                    # Delegate announcement/update to announce_event
                    try:
                        announce_event(bot, event_service, event_id, participants=participants)
                    except Exception:
                        pass
                except Exception:
                    traceback.print_exc()
                # Get event info for confirmation message
                row = event_service.get_event(state["event_id"])
                if row:
                    date_str, time_start, time_end = row
                    dt = _dt.datetime.strptime(date_str, "%Y-%m-%d")
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
        # Remove buttons from the prompt message (if we saved it)
        prompt_msg_id = register_state[user_id].pop("prompt_message_id", None)
        if prompt_msg_id:
            try:
                bot.edit_message_reply_markup(chat_id=chat_id, message_id=prompt_msg_id, reply_markup=None)
            except Exception:
                pass
        event_id = register_state[user_id]["event_id"]
        row = event_service.get_event(event_id)
        if not row:
            bot.send_message(chat_id, LOCALES["error"])
            return
        date_str, time_start, time_end = row
        dt = _dt.datetime.strptime(date_str, "%Y-%m-%d")
        month_name = LOCALES["month_names"][dt.month - 1]
        formatted_date = f"{dt.day} {month_name} {dt.year} с {time_start} до {time_end}"
        summary = LOCALES["register_summary"].format(training=formatted_date, name=register_state[user_id]['name'])
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(LOCALES["confirm"], callback_data="reg_confirm"))
        markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="reg_back"))
        markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="reg_cancel"))
        bot.send_message(chat_id, LOCALES["register_check"].format(summary=summary), reply_markup=markup)
