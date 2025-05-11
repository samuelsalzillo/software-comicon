



from threading import Lock

from .init_queue_table import init_queue_table
from .init_scoring_table import init_scoring_table
from .init_average_times_table import init_average_times_table
from .init_mid_times_table import init_mid_times_table
from .init_skipped_table import init_skipped_table
from .init_qualified_players_table import init_qualified_players_table
from .init_charlie_timer_table import init_charlie_timer_table
from ...utils.date import initialize_queues

sqlite_lock = Lock()

def init_database():

    # Chiama la funzione per inizializzare il database
    init_queue_table(sqlite_lock)

    # Chiama la funzione per inizializzare la tabella scoring
    init_scoring_table(sqlite_lock)

    # Chiamare la funzione all'avvio
    init_average_times_table(sqlite_lock)

    # Chiamare la funzione all'avvio
    init_mid_times_table(sqlite_lock)

    # Chiama la funzione per inizializzare la tabella skipped_players
    init_skipped_table(sqlite_lock)

    init_qualified_players_table(sqlite_lock)

    # --- NUOVA Funzione Init Tabella Timer Charlie ---
    init_charlie_timer_table(sqlite_lock)

    initialize_queues()