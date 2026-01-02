from locales import LOCALES
import datetime as _dt
import requests
import os


def announce_event(bot, event_service, event_id, date_str=None, time_start=None, time_end=None, participants=None):
	"""Create or update announcement for an event.

	This function requires a numeric Telegram chat id in `channel` (either an
	`int` or a numeric string). Usernames (for example, "@badmintonOleArena")
	are NOT accepted. If `channel` is missing or not numeric the function
	returns False immediately.

	If `participants` is provided (list of tuples (name, joined_at)), the announcement
	will include the participants list. If an announcement already exists for the
	event, the function will try to edit it; otherwise it will send a new message
	and persist its location via `event_service.set_event_announcement`.

	Returns True on success, False otherwise.
	"""
	# Ensure we have event date/time; fetch if not provided
	try:
		if date_str is None or time_start is None or time_end is None:
			row = event_service.db.cursor.execute(
				"SELECT date, time_start, time_end FROM events WHERE id = ?",
				(event_id,)
			).fetchone()
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

	announce_text = LOCALES.get("channel_announce", "Объявляется тренировка:\n{summary}").format(summary=summary)

	parts_text = ""
	if participants:
		count = len(participants)
		parts_text = "\n\nУчастники ({count}):\n".format(count=count)
		for i, (n, joined) in enumerate(participants, start=1):
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

	public_text = announce_text + parts_text

	# Build canceled participants list for private message
	canceled_text = ""
	try:
		rows = event_service.db.cursor.execute(
			"SELECT name, canceled_at FROM event_participants WHERE event_id = ? AND canceled = 1 ORDER BY canceled_at",
			(event_id,)
		).fetchall()
		if rows:
			count = len(rows)
			canceled_text = "\n\nОтменившиеся ({count}):\n".format(count=count)
			for i, (n, canceled_at) in enumerate(rows, start=1):
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
				canceled_text += f"{i}. {n} ({date_part} в {time_str})\n"
	except Exception:
		canceled_text = ""

	private_text = public_text + canceled_text

	# Read target chat ids from environment and require at least one numeric id.
	public_id = os.environ.get('PUBLIC_CHAT_ID')
	private_id = os.environ.get('PRIVATE_CHAT_ID')
	targets = []
	for cid in (public_id, private_id):
		if cid is None:
			continue
		try:
			targets.append(int(cid))
		except Exception:
			continue

	if not targets:
		# No valid numeric chat ids configured
		return False

	# Check for existing announcement (only message ids stored in DB)
	try:
		announce_msg_id, private_msg_id = event_service.get_event_announcement(event_id)
	except Exception:
		announce_msg_id = private_msg_id = None

	# Use public target from environment always
	try:
		public_target = int(public_id) if public_id is not None else None
	except Exception:
		public_target = None

	# If we have announcement info (message ids), try to edit both public and private messages
	try:
		private_target = int(private_id) if private_id is not None else None
	except Exception:
		private_target = None

	if (public_target and announce_msg_id) or (private_target and private_msg_id):
		edited_any = False
		# Try edit public
		try:
			if public_target and announce_msg_id:
				try:
					chat_id_val = int(public_target) if not isinstance(public_target, int) else public_target
					msg_id_val = int(announce_msg_id) if not isinstance(announce_msg_id, int) else announce_msg_id
					bot.edit_message_text(public_text, chat_id_val, msg_id_val)
					edited_any = True
				except Exception:
					edited_any = edited_any or False
		except Exception:
			pass

		# Try edit private (no thread) — include canceled list
		try:
			if private_target and private_msg_id:
				try:
					pch = int(private_target) if not isinstance(private_target, int) else private_target
					pmid = int(private_msg_id) if not isinstance(private_msg_id, int) else private_msg_id
					bot.edit_message_text(private_text, pch, pmid)
					edited_any = True
				except Exception:
					edited_any = edited_any or False
		except Exception:
			pass

		return edited_any

	# Send a new announcement to all configured targets and persist the public and private message ids.
	first_public_msg = None
	try:
		# Send to all targets. No thread/topic creation; use simple messages.
		private_msg_id = None
		for t in targets:
			try:
				# Use public_text for public target, private_text for private target
				if private_target is not None and t == private_target:
					sent_msg = bot.send_message(t, private_text)
				else:
					sent_msg = bot.send_message(t, public_text)
			except Exception:
				sent_msg = None

			# Capture the public/private message objects to persist
			if public_target is not None and t == public_target and sent_msg is not None:
				first_public_msg = sent_msg
			if private_target is not None and t == private_target and sent_msg is not None:
				private_msg_id = getattr(sent_msg, 'message_id', None)

	except Exception:
		first_public_msg = None

	if first_public_msg is not None:
		try:
			msg_id = getattr(first_public_msg, 'message_id', None)
			# Persist only message ids (chat ids are taken from env)
			event_service.set_event_announcement(
				event_id,
				announce_message_id=msg_id,
				private_message_id=private_msg_id,
			)
		except Exception:
			pass
		return True

	return False

