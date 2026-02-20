from telebot import types
from locales import LOCALES
import traceback
import datetime as _dt
from datetime import timezone
from utils.announce import announce_event


def register_cancel_handlers(bot, event_service):
    cancel_state = {}
    def get_user_registrations_not_canceled(user_id):
        # Return participant row id, event id, formatted event summary and participant name
        rows = event_service.get_user_registrations(user_id)
        result = []
        for row in rows:
            part_id, event_id, date_str, time_start, time_end, name = row
            try:
                dt = _dt.datetime.strptime(date_str, "%Y-%m-%d")
                month_name = LOCALES["month_names"][dt.month - 1]
                formatted_date = f"{dt.day} {month_name} {dt.year} from {time_start} to {time_end}"
            except Exception:
                formatted_date = f"{date_str} {time_start}-{time_end}"
            display = f"{formatted_date} — {name}"
            result.append((part_id, event_id, display, name))
        return result

    @bot.message_handler(commands=['cancel'])
    def handle_cancel(message):
        user_id = message.from_user.id
        cancel_state[user_id] = {}
        markup = types.InlineKeyboardMarkup()
        regs = get_user_registrations_not_canceled(user_id)
        if not regs:
            bot.send_message(message.chat.id, LOCALES["cancel_no_registrations"])
            return
        for part_id, event_id, display, name in regs:
            markup.add(types.InlineKeyboardButton(display, callback_data=f"can_part_{part_id}"))
        markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="can_cancel"))
        bot.send_message(message.chat.id, LOCALES["cancel_select_event"], reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("can_part_") or call.data in ("can_cancel", "can_back", "can_confirm"))
    def handle_cancel_callback(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        if call.data == "can_cancel":
            cancel_state.pop(user_id, None)
            bot.edit_message_text(LOCALES["cancel_cancelled"], chat_id, call.message.message_id)
            return
        if call.data.startswith("can_part_"):
            part_id = int(call.data[len("can_part_"):])
            # load participant row
            prow = event_service.get_participant(part_id)
            if not prow:
                bot.edit_message_text(LOCALES["error"], chat_id, call.message.message_id)
                return
            _, event_id, name = prow
            cancel_state[user_id] = {"part_id": part_id, "event_id": event_id, "name": name}
            # show confirmation with name and event info
            row = event_service.get_event(event_id)
            if row:
                date_str, time_start, time_end, _ = row
                try:
                    dt = _dt.datetime.strptime(date_str, "%Y-%m-%d")
                    month_name = LOCALES["month_names"][dt.month - 1]
                    formatted_date = f"{dt.day} {month_name} {dt.year} from {time_start} to {time_end}"
                except Exception:
                    formatted_date = f"{date_str} {time_start}-{time_end}"
            else:
                formatted_date = ""

            summary = f"{formatted_date} — {name}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(LOCALES.get("confirm", "Confirm"), callback_data="can_confirm"))
            markup.add(types.InlineKeyboardButton(LOCALES["back"], callback_data="can_back"))
            markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="can_cancel"))
            bot.edit_message_text(LOCALES["cancel_confirm"].format(event_summary=summary), chat_id, call.message.message_id, reply_markup=markup)
            return
        if call.data == "can_back":
            # Rebuild list of registrations
            markup = types.InlineKeyboardMarkup()
            regs = get_user_registrations_not_canceled(user_id)
            for part_id, event_id, display, name in regs:
                markup.add(types.InlineKeyboardButton(display, callback_data=f"can_part_{part_id}"))
            markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="can_cancel"))
            bot.edit_message_text(LOCALES["cancel_select_event"], chat_id, call.message.message_id, reply_markup=markup)
            return
        if call.data == "can_confirm":
            state = cancel_state.pop(user_id, None)
            if state and "part_id" in state:
                part_id = state["part_id"]
                event_id = state.get("event_id")
                name = state.get("name")
                canceled_at = _dt.datetime.now().isoformat()
                
                success = event_service.cancel_registration(part_id, canceled_at)
                if not success:
                    bot.edit_message_text(LOCALES["cancel_event_started"], chat_id, call.message.message_id)
                    return

                try:
                    if event_id:
                        # Announce the change
                        announce_event(bot, event_service, event_id)
                except Exception:
                    traceback.print_exc()

                # Get event info for confirmation message
                row = event_service.get_event(event_id)
                if row:
                    date_str, time_start, time_end, _ = row
                    try:
                        dt = _dt.datetime.strptime(date_str, "%Y-%m-%d")
                        month_name = LOCALES["month_names"][dt.month - 1]
                        formatted_date = f"{dt.day} {month_name} {dt.year} from {time_start} to {time_end}"
                    except Exception:
                        formatted_date = f"{date_str} {time_start}-{time_end}"
                else:
                    formatted_date = ""

                summary = f"{formatted_date} — {name}"
                try:
                    bot.edit_message_text(LOCALES["cancel_success"].format(event_summary=summary), chat_id, call.message.message_id)
                except Exception:
                    bot.edit_message_text(LOCALES["cancel_cancelled"], chat_id, call.message.message_id)
            else:
                bot.edit_message_text(LOCALES["error"], chat_id, call.message.message_id)
            return
