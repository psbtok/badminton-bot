import os
from locales import LOCALES
from utils.text import get_person_word, format_date_for_calendar

def register_calendar_handlers(bot, db_ops, is_admin=False):
    @bot.message_handler(commands=['calendar'])
    def handle_calendar(message):
        chat_id = message.chat.id
        if is_admin:
            events = db_ops.get_upcoming_events()
            if not events:
                bot.reply_to(message, LOCALES["calendar_no_upcoming_events"])
                return
            
            response = LOCALES["calendar_upcoming_events"]
            for i, event in enumerate(events, 1):
                date, time_start, time_end, _, private_message_id, announce_message_id, participant_count, max_participants = event
                
                private_chat_id = os.environ.get('PRIVATE_CHAT_ID', '').replace('-100', '')
                public_chat_id = os.environ.get('PUBLIC_CHAT_ID', '').replace('-100', '')


                private_link = f"https://t.me/c/{private_chat_id}/{private_message_id}" if private_message_id and private_chat_id else ""
                public_link = f"https://t.me/c/{public_chat_id}/{announce_message_id}" if announce_message_id and public_chat_id else ""

                person_word = get_person_word(max_participants)

                response += LOCALES["calendar_admin_event_line"].format(
                    event_number=i,
                    date=format_date_for_calendar(date), 
                    time_start=time_start, 
                    time_end=time_end, 
                    participant_count=participant_count,
                    max_participants=max_participants,
                    person_word=person_word,
                    private_link=private_link,
                    public_link=public_link
                )
        else:
            user_id = message.from_user.id
            events = db_ops.get_upcoming_events(participant_id=user_id)
            if not events:
                bot.reply_to(message, LOCALES["calendar_no_upcoming_events"])
                return
            response = LOCALES["calendar_your_upcoming_events"]
            for i, event in enumerate(events, 1):
                date, time_start, time_end, event_id, announce_message_id, participant_count, max_participants, name = event
                public_chat_id = os.environ.get('PUBLIC_CHAT_ID', '').replace('-100', '')
                public_link = f"https://t.me/c/{public_chat_id}/{announce_message_id}" if announce_message_id and public_chat_id else ""
                person_word = get_person_word(max_participants)
                response += LOCALES["calendar_user_event_line"].format(
                    event_number=i,
                    date=format_date_for_calendar(date), 
                    time_start=time_start, 
                    time_end=time_end,
                    public_link=public_link,
                    participant_count=participant_count,
                    max_participants=max_participants,
                    person_word=person_word,
                    name=name
                )
        
        bot.reply_to(message, response, parse_mode='Markdown', disable_web_page_preview=True)
