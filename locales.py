LOCALES = {
    "welcome": "Here you can sign up for a session!",
    "welcome_admin": "Welcome! You can create and manage sessions here.",
    "start": "Start! The bot is ready to work.",
    "event_created": "Event created.",
    "error": "An error occurred. Please try again.",
    "no_events": "No events found.",
    "add_participant": "Participant added.",
    "already_participant": "You are already participating in this event.",
    "event_list": "List of events:",
    "register_confirmed_full": "Registration confirmed!\nYou are signed up for the session {training} under the name '{name}'",
    "register_choose_name": "Choose how to provide your name:",
    "register_use_tg_name": "Use Telegram name",
    "register_enter_manually": "Enter manually",
    "register_select_training": "Select a session to register for:",
    "register_cancelled": "Registration cancelled.",
    "register_enter_name": "Enter your name for registration:",
    "register_confirmed": "Registration confirmed!",
    "register_check": "Please check the details and confirm your registration:\n{summary}",
    "register_summary": "Session: {training}\nName: {name}",
    "create_event": "Create Session",
    "select_date": "Select the session date:",
    "select_time": "Select the session start time:",
    "confirm_event": "Confirm the creation of the session:",
    "back": "Back",
    "cancel": "Cancel",
    "confirm": "Confirm",
    "event_summary": "Session: {date}, {time_start}-{time_end}",
    "event_success": "Session successfully created!",
    "event_cancelled": "Session creation cancelled.",
    "event_back": "You have returned to the previous step.",
    "invalid_selection": "Invalid selection. Please try again.",
    "prompt_cancel": "You can cancel the session creation at any time.",
    "prompt_back": "You can go back to the previous step.",
    "date_button": "{day} {month}",
    "time_button": "{hour}:00",
    "month_names": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "no_access": "You do not have access rights.",
    "cancel_select_event": "Select the registration to cancel:",
    "cancel_confirm": "Are you sure you want to cancel your registration for {event_summary}?",
    "cancel_success": "Your registration for {event_summary} has been cancelled.",
    "cancel_cancelled": "Cancellation aborted.",
    "cancel_no_registrations": "You have no active registrations to cancel.",
    "cancel_event_started": "Cannot cancel registration because the session has already started.",
    "calendar_no_upcoming_events": "No upcoming sessions.",
    "calendar_upcoming_events": "Upcoming sessions:\n\n",
    "calendar_your_upcoming_events": "Your upcoming sessions:\n\n",
    "calendar_user_event_line": (
        "{date} from {time_start} to {time_end} — {name}\n"
        "👤 {participant_count}/{max_participants} {person_word}\n"
        "🔗 [Link]({public_link})\n\n"
    ),
    "calendar_admin_event_line": (
        "{date} from {time_start} to {time_end} \n"
        "👤 {participant_count}/{max_participants} {person_word}\n"
        "🔗 [Link (public chat)]({public_link})\n"
        "🔗 [Link (coach chat)]({private_link})\n\n"
    ),
    "person_single": "person",
    "person_plural": "people",
    "person_plural_genitive": "people",
    "register_event_full": "Sorry, this session is already full.",
    "cancel_training_no_upcoming": "No upcoming sessions to cancel.",
    "cancel_training_select": "Select a session to cancel:",
    "cancel_training_confirm": "Are you sure you want to cancel this session?",
    "cancel_training_yes": "Yes, cancel",
    "cancel_training_no": "No, don't cancel",
    "cancel_training_success": "Session successfully cancelled.",
    "cancel_training_cancelled": "Cancellation aborted.",
    "training_cancelled_notification": "Session Cancelled",
    "training_cancelled_public_notification": "Session Cancelled",
    "training_cancelled_public_message": (
        "❌ Session Cancelled\n\n"
        "The scheduled session on\n"
        "{date} from {time_start} to {time_end}\n"
        "has been cancelled.\n\n"
        "Participants who signed up will be automatically removed from the registration.\n\n"
        "We apologize for the inconvenience.\n"
        "Information about the next session will be posted in this channel."
    ),
    "training_cancelled_reply": "Unfortunately, the session has been cancelled.",
    "event_summary_with_time": "{date} from {start_time} to {end_time}",
    "channel_announce": "A new session has been announced!\n\n{summary}",
    "event_summary_with_time_and_date": "{date} from {start_time} to {end_time}",
    "participant_limit": "\nParticipant limit - {max_participants} {person_word}\n",
    "participants_header": "\nParticipants ({count}):\n",
    "participant_entry": "{i}. {n} ({date_part} at {time_str})\n",
    "participant_entry_private": "{i}. {n} {user_tag} ({date_part} at {time_str})\n",
    "registration_footer": "\nYou can register here @{bot_username}",
    "canceled_participants_header": "\nCancelled ({count}):\n",
    "prompt_max_participants": "Enter the maximum number of participants (or 0 for no limit).",
    "invalid_format_number": "Invalid format. Please enter a number.",
    "participants_count_summary": "\nParticipants: up to {max_p} people",
    "no_permission": "You do not have permission for this action.",
    "session_not_found": "Session not found.",
    "session_full": " (full)",
}
