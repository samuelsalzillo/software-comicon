from datetime import datetime as dt

import pytz


def initialize_queues():
    rome_tz = pytz.timezone('Europe/Rome')
    dt.now(rome_tz)

def crea_nuova_data():
    # Crea una nuova istanza datetime indipendente
    nuova_data = dt.now(pytz.timezone('Europe/Rome'))
    return nuova_data

def format_time(time_in_minutes: float) -> str:
    """Formatta il tempo in minuti e secondi"""
    minutes = int(time_in_minutes)
    seconds = int((time_in_minutes - minutes) * 60)
    return f"{minutes}m {seconds}s"

def get_current_time() -> dt:
    """Restituisce l'ora corrente nel fuso orario di Roma"""
    rome_tz = pytz.timezone('Europe/Rome')
    return dt.now(rome_tz)