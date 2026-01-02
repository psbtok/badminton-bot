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
        rows = event_service.db.cursor.execute(
            """
            SELECT p.id, e.id, e.date, e.time_start, e.time_end, p.name
            FROM event_participants p
            JOIN events e ON p.event_id = e.id
            WHERE p.participant_id = ? AND (p.canceled IS NULL OR p.canceled = 0)
            """,
            (user_id,)
        ).fetchall()
        result = []
        for row in rows:
            part_id, event_id, date_str, time_start, time_end, name = row
            try:
                dt = _dt.datetime.strptime(date_str, "%Y-%m-%d")
                month_name = LOCALES["month_names"][dt.month - 1]
                formatted_date = f"{dt.day} {month_name} {dt.year} с {time_start} до {time_end}"
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
            bot.send_message(message.chat.id, LOCALES.get("no_events", "Событий не найдено."))
            return
        for part_id, event_id, display, name in regs:
            markup.add(types.InlineKeyboardButton(display, callback_data=f"can_part_{part_id}"))
        markup.add(types.InlineKeyboardButton(LOCALES["cancel"], callback_data="can_cancel"))
        bot.send_message(message.chat.id, LOCALES.get("register_select_training", "Выберите тренировку для регистрации:"), reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("can_part_") or call.data in ("can_cancel", "can_back", "can_confirm"))
    def handle_cancel_callback(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        if call.data == "can_cancel":
            cancel_state.pop(user_id, None)
            bot.edit_message_text(LOCALES.get("register_cancelled", "Регистрация отменена."), chat_id, call.message.message_id)
            return
        if call.data.startswith("can_part_"):
            part_id = int(call.data[len("can_part_"):])
            # load participant row
            prow = event_service.db.cursor.execute(
                "SELECT id, event_id, name FROM event_participants WHERE id = ?",
                (part_id,)
            ).fetchone()
            if not prow:
                bot.edit_message_text(LOCALES.get("error", "Произошла ошибка. Пожалуйста, попробуйте снова."), chat_id, call.message.message_id)
                return
            _, event_id, name = prow
            cancel_state[user_id] = {"part_id": part_id, "event_id": event_id, "name": name}
            # show confirmation with name and event info
            row = event_service.db.cursor.execute("SELECT date, time_start, time_end FROM events WHERE id = ?", (event_id,)).fetchone()
            if row:
                date_str, time_start, time_end = row
                try:
                    dt = _dt.datetime.strptime(date_str, "%Y-%m-%d")
                    month_name = LOCALES["month_names"][dt.month - 1]
                    formatted_date = f"{dt.day} {month_name} {dt.year} с {time_start} до {time_end}"
                except Exception:
                    formatted_date = f"{date_str} {time_start}-{time_end}"
            else:
                formatted_date = ""

            summary = f"{formatted_date} — {name}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(LOCALES.get("confirm", "Подтвердить"), callback_data="can_confirm"))
            markup.add(types.InlineKeyboardButton(LOCALES.get("back", "Назад"), callback_data="can_back"))
            markup.add(types.InlineKeyboardButton(LOCALES.get("cancel", "Отмена"), callback_data="can_cancel"))
            bot.edit_message_text(LOCALES.get("register_check", "Проверьте данные и подтвердите регистрацию:\n{summary}").format(summary=summary), chat_id, call.message.message_id, reply_markup=markup)
            return
        if call.data == "can_back":
            # Rebuild list of registrations
            markup = types.InlineKeyboardMarkup()
            regs = get_user_registrations_not_canceled(user_id)
            for part_id, event_id, display, name in regs:
                markup.add(types.InlineKeyboardButton(display, callback_data=f"can_part_{part_id}"))
            markup.add(types.InlineKeyboardButton(LOCALES.get("cancel", "Отмена"), callback_data="can_cancel"))
            bot.edit_message_text(LOCALES.get("register_select_training", "Выберите тренировку для регистрации:"), chat_id, call.message.message_id, reply_markup=markup)
            return
        if call.data == "can_confirm":
            state = cancel_state.pop(user_id, None)
            if state and "part_id" in state:
                part_id = state["part_id"]
                event_id = state.get("event_id")
                name = state.get("name")
                canceled_at = _dt.datetime.now(timezone.utc).isoformat()
                try:
                    event_service.db.cursor.execute(
                        "UPDATE event_participants SET canceled = 1, canceled_at = ? WHERE id = ?",
                        (canceled_at, part_id)
                    )
                    event_service.db.conn.commit()
                except Exception:
                    bot.edit_message_text(LOCALES.get("error", "Произошла ошибка. Пожалуйста, попробуйте снова."), chat_id, call.message.message_id)
                    return

                try:
                    # Build participants list (exclude canceled)
                    rows = event_service.db.cursor.execute(
                        "SELECT name, joined_at FROM event_participants WHERE event_id = ? AND (canceled IS NULL OR canceled = 0) ORDER BY joined_at",
                        (event_id,)
                    ).fetchall()
                    participants = [(r[0], r[1]) for r in rows]
                    try:
                        announce_event(bot, event_service, event_id, participants=participants)
                    except Exception:
                        pass
                except Exception:
                    traceback.print_exc()

                # Confirmation message to user with the cancelled name
                try:
                    if name:
                        bot.edit_message_text(f"Отмена записи '{name}' выполнена.", chat_id, call.message.message_id)
                    else:
                        bot.edit_message_text(LOCALES.get("register_cancelled", "Регистрация отменена."), chat_id, call.message.message_id)
                except Exception:
                    bot.edit_message_text(LOCALES.get("register_cancelled", "Регистрация отменена."), chat_id, call.message.message_id)
            else:
                bot.edit_message_text(LOCALES.get("error", "Произошла ошибка. Пожалуйста, попробуйте снова."), chat_id, call.message.message_id)
            return
