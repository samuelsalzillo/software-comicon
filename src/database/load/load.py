from threading import Lock

from .load_mid_times import load_mid_times_from_db
from .load_average_times import load_average_times_from_db
from .load_skipped import load_skipped_from_db
from .load_scores import load_scores_from_db
from .load_queues_from_db import load_queues_from_db
from .load_charlie_timer_history import load_charlie_timer_history_from_db

from ...utils.model import get_game_backend
from ...utils.database import get_lock

def load_database():
    game_backend = get_game_backend()
    sqlite_lock = get_lock()

    load_mid_times_from_db(sqlite_lock,game_backend)

    load_average_times_from_db(sqlite_lock,game_backend)

    # Carica gli skippati all'avvio dell'applicazione
    load_skipped_from_db(game_backend)

    # Carica gli score all'avvio dell'applicazione
    load_scores_from_db(sqlite_lock,game_backend)

    # Carica le code all'avvio dell'applicazione
    load_queues_from_db(game_backend)

    load_charlie_timer_history_from_db(sqlite_lock,game_backend)
