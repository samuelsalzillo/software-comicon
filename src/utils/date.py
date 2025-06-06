from datetime import datetime as dt, datetime

import pytz

formato_timestamp = "%Y-%m-%d %H:%M:%S"
formato_datetime = "%Y-%m-%d %H:%M:%S.%f%z"

def initialize_queues():
    rome_tz = pytz.timezone('Europe/Rome')
    dt.now(rome_tz)

def crea_nuova_data():
    # Crea una nuova istanza datetime indipendente
    nuova_data = dt.now(pytz.timezone('Europe/Rome'))
    return nuova_data

def format_time_into_mmss(time_in_minutes: float) -> str:
    """Formatta il tempo in minuti e secondi"""
    minutes = round(time_in_minutes)
    fractional_part = time_in_minutes - minutes
    seconds = abs(round(fractional_part * 60))
    return f"{minutes}m {seconds}s"

def get_current_time() -> dt:
    """Restituisce l'ora corrente nel fuso orario di Roma"""
    rome_tz = pytz.timezone('Europe/Rome')
    return dt.now(rome_tz)

def convert_string_date_into_date(string_date : str):
    global formato_timestamp
    if string_date:
        return datetime.strptime(string_date, formato_timestamp)
    else:
        return string_date

def convert_string_date_datetime_into_date(string_date : str):
    global formato_datetime
    date = datetime.strptime(string_date, formato_datetime)
    date = date.replace(hour=date.hour + int(date.tzinfo.utcoffset(None).seconds / 3600)).replace(tzinfo=None)
    return date

def converti_float_mmss_in_secondi_totali(tempo_float):
    s_tempo = str(tempo_float)
    if '.' in s_tempo:
        minuti_str, secondi_str = s_tempo.split('.')
        minuti = int(minuti_str)
        secondi = int(secondi_str[:2]) if secondi_str else 0
    else:
        minuti = int(s_tempo)
        secondi = 0
    return (minuti * 60) + secondi