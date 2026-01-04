from locales import LOCALES
import datetime as _dt
import requests
import os


def _send_public_announcement(bot, event_service, event_id, public_text):
    """Handles sending or editing the public announcement."""
    public_id = os.environ.get('PUBLIC_CHAT_ID')
    if not public_id:
        return None, False

    try:
        public_target = int(public_id)
    except (ValueError, TypeError):
        return None, False

    announce_msg_id, _ = event_service.get_event_announcement(event_id)

    try:
        if announce_msg_id:
            bot.edit_message_text(public_text, public_target, announce_msg_id)
            return None, True  # No new message ID, but success
        else:
            sent_msg = bot.send_message(public_target, public_text)
            return sent_msg.message_id, True
    except Exception:
        return None, False

def _send_private_announcement(bot, event_service, event_id, private_text):
    """Handles sending or editing the private announcement."""
    private_id = os.environ.get('PRIVATE_CHAT_ID')
    if not private_id:
        return None, False

    try:
        private_target = int(private_id)
    except (ValueError, TypeError):
        return None, False

    _, private_msg_id = event_service.get_event_announcement(event_id)

    try:
        if private_msg_id:
            bot.edit_message_text(private_text, private_target, private_msg_id)
            return None, True  # No new message ID, but success
        else:
            sent_msg = bot.send_message(private_target, private_text)
            return sent_msg.message_id, True
    except Exception:
        return None, False

def _build_public_text(summary, participants):
    """Builds the announcement text for the public channel."""
    announce_text = LOCALES.get("channel_announce", "Объявляется тренировка:\n{summary}").format(summary=summary)

    parts_text = ""
    if participants:
        count = len(participants)
        parts_text = "\n\nУчастники ({count}):\n".format(count=count)
        for i, (n, _, joined) in enumerate(participants, start=1):
            try:
                joined_dt = _dt.datetime.fromisoformat(joined)
                local_dt = joined_dt.astimezone()
                time_str = local_dt.strftime('%H:%M')
                day = local_dt.day
                month_name = LOCALES["month_names"][local_dt.month - 1]
                date_part = f"{day} {month_name}"
            except Exception:
                time_str = "?"
                date_part = "?"
            parts_text += f"{i}. {n} ({date_part} в {time_str})\n"
    
    return announce_text + parts_text

def _build_private_text(summary, participants, event_service, event_id):
    """Builds the announcement text for the private channel."""
    announce_text = LOCALES.get("channel_announce", "Объявляется тренировка:\n{summary}").format(summary=summary)

    parts_text = ""
    if participants:
        count = len(participants)
        parts_text = "\n\nУчастники ({count}):\n".format(count=count)
        for i, (n, username, joined) in enumerate(participants, start=1):
            try:
                joined_dt = _dt.datetime.fromisoformat(joined)
                local_dt = joined_dt.astimezone()
                time_str = local_dt.strftime('%H:%M')
                day = local_dt.day
                month_name = LOCALES["month_names"][local_dt.month - 1]
                date_part = f"{day} {month_name}"
            except Exception:
                time_str = "?"
                date_part = "?"

            user_tag = f"@{username}" if username else ""
            parts_text += f"{i}. {n} {user_tag} ({date_part} в {time_str})\n"

    canceled_text = ""
    try:
        rows = event_service.get_canceled_participants(event_id)
        if rows:
            count = len(rows)
            canceled_text = "\n\nОтменившиеся ({count}):\n".format(count=count)
            for i, (n, username, canceled_at) in enumerate(rows, start=1):
                try:
                    c_dt = _dt.datetime.fromisoformat(canceled_at)
                    c_local = c_dt.astimezone()
                    time_str = c_local.strftime('%H:%M')
                    day = c_local.day
                    month_name = LOCALES["month_names"][c_local.month - 1]
                    date_part = f"{day} {month_name}"
                except Exception:
                    time_str = "?"
                    date_part = "?"

                user_tag = f"@{username}" if username else ""
                canceled_text += f"{i}. {n} {user_tag} ({date_part} в {time_str})\n"
    except Exception:
        canceled_text = ""

    return announce_text + parts_text + canceled_text

def announce_event(bot, event_service, event_id, date_str=None, time_start=None, time_end=None, participants=None):
	# Ensure we have event date/time; fetch if not provided
	try:
		if date_str is None or time_start is None or time_end is None:
			row = event_service.get_event(event_id)
			if row:
				date_str, time_start, time_end = row
	except Exception:
		return False

	# Format date and summary
	try:
		dt = _dt.datetime.strptime(date_str, "%Y-%m-%d")
		month_name = LOCALES["month_names"][dt.month - 1]
		formatted_date = f"{dt.day} {month_name} {dt.year}"
	except Exception:
		formatted_date = date_str

	# Normalize time_start/time_end to integers if they come as strings like '10:00'
	try:
		ts = int(str(time_start).split(":")[0])
		te = int(str(time_end).split(":")[0])
	except Exception:
		try:
			ts = int(time_start)
			te = int(time_end)
		except Exception:
			ts = None
			te = None

	if ts is not None and te is not None:
		summary = f"{formatted_date} с {ts:02d}:00 до {te:02d}:00"
	else:
		summary = f"{formatted_date} {time_start} - {time_end}"

	if participants is None:
		participants = event_service.get_event_participants(event_id)

	public_text = _build_public_text(summary, participants)
	private_text = _build_private_text(summary, participants, event_service, event_id)
	print("Public Announcement Text:\n", public_text)
	new_public_id, public_success = _send_public_announcement(bot, event_service, event_id, public_text)
	new_private_id, private_success = _send_private_announcement(bot, event_service, event_id, private_text)

	# If new messages were sent, update the database
	if new_public_id is not None or new_private_id is not None:
		# We need to get the existing IDs to avoid overwriting one with None
		existing_public_id, existing_private_id = event_service.get_event_announcement(event_id)
		
		final_public_id = new_public_id if new_public_id is not None else existing_public_id
		final_private_id = new_private_id if new_private_id is not None else existing_private_id
		
		event_service.set_event_announcement(
			event_id,
			announce_message_id=final_public_id,
			private_message_id=final_private_id,
		)

	return public_success or private_success

