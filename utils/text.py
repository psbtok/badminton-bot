from datetime import datetime
from locales import LOCALES

def format_date_for_calendar(date_str):
    """Formats date string from YYYY-MM-DD to 'd month YYYY'."""
    if isinstance(date_str, str):
        dt_object = datetime.strptime(date_str, '%Y-%m-%d')
    else: # assume it's a date or datetime object
        dt_object = date_str
        
    month_name = LOCALES["month_names"][dt_object.month - 1]
    return f"{dt_object.day} {month_name} {dt_object.year}"

def get_person_word(count):
    if count % 10 == 1 and count % 100 != 11:
        return LOCALES["person_single"]
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return LOCALES["person_plural"]
    else:
        return LOCALES["person_plural_genitive"]
