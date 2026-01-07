import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from event_service import EventService
from utils.text import format_event_for_selection, format_event_summary, format_date_for_calendar
from locales import LOCALES

(SELECT_EVENT, CONFIRM_CANCEL) = range(2)

def register_cancel_training_handlers(bot, event_service):
    db_ops = EventService()

    @bot.message_handler(commands=['event_cancel'])
    def cancel_training_start(message):
        events = db_ops.get_future_events()
        if not events:
            bot.reply_to(message, LOCALES["cancel_training_no_upcoming"])
            return

        keyboard = InlineKeyboardMarkup()
        for event in events:
            event_id = event[3]
            event_text = format_event_for_selection(event)
            keyboard.add(InlineKeyboardButton(event_text, callback_data=f"cancel_event_{event_id}"))

        bot.reply_to(message, LOCALES["cancel_training_select"], reply_markup=keyboard)
        return SELECT_EVENT

    @bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_event_'))
    def cancel_event_selected(call):
        event_id = int(call.data.split('_')[2])
        event = event_service.get_event_by_id(event_id)
        if not event:
            bot.answer_callback_query(call.id, "Тренировка не найдена.", show_alert=True)
            return

        summary = format_event_summary(event)
        confirmation_text = f"{LOCALES['cancel_training_confirm']}\n\n{summary}"
        
        # Ask for confirmation
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(LOCALES["cancel_training_yes"], callback_data=f"confirm_cancel_{event_id}"))
        keyboard.add(InlineKeyboardButton(LOCALES["cancel_training_no"], callback_data="cancel_cancellation"))
        
        bot.edit_message_text(confirmation_text,
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard)
        return CONFIRM_CANCEL

    @bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_cancel_'))
    def confirm_cancel_event(call):
        event_id = int(call.data.split('_')[2])
        
        # Fetch event details before canceling
        event = event_service.get_event_by_id(event_id)
        
        db_ops.cancel_event(event_id)

        # Notify participants
        participants = event_service.get_event_participants(event_id)
        for p in participants:
            participant_id = p[0]
            try:
                bot.send_message(participant_id, LOCALES["training_cancelled_notification"])
            except Exception as e:
                print(f"Failed to send cancellation to {participant_id}: {e}")

        # Update public message
        if event and event.announce_message_id:
            try:
                formatted_date = format_date_for_calendar(event.date)
                new_text = LOCALES["training_cancelled_public_message"].format(
                    date=formatted_date,
                    time_start=event.time_start,
                    time_end=event.time_end
                )
                announce_chat_id = os.environ.get('PUBLIC_CHAT_ID')
                private_chat_id = os.environ.get('PRIVATE_CHAT_ID')

                bot.edit_message_text(new_text,
                                      chat_id=announce_chat_id,
                                      message_id=event.announce_message_id,
                                      parse_mode='HTML')
                bot.send_message(announce_chat_id, LOCALES["training_cancelled_reply"], reply_to_message_id=event.announce_message_id)
                bot.send_message(private_chat_id, LOCALES["training_cancelled_notification"], reply_to_message_id=event.private_message_id)

            except Exception as e:
                print(f"Failed to edit announcement message: {e}")

        bot.edit_message_text(LOCALES["cancel_training_success"],
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        return -1 # End of conversation

    @bot.callback_query_handler(func=lambda call: call.data == 'cancel_cancellation')
    def cancel_cancellation(call):
        bot.edit_message_text(LOCALES["cancel_training_cancelled"],
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        return -1
