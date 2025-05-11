import logging
import os
import sqlite3


def init_average_times_table(sqlite_lock):
    logging.debug("[AVG TIMES DB] Acquisizione lock per init tabella average_times")
    with sqlite_lock:
        logging.debug("[AVG TIMES DB] Lock acquisito")
        try:
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
            cursor = conn.cursor()
            logging.debug("[AVG TIMES DB] Creazione tabella average_times, se non esiste")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS average_times (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_type TEXT CHECK(player_type IN ('couple', 'single', 'couple2', 'single2')) NOT NULL,
                    timer_duration_minutes REAL NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Indici potrebbero essere utili se la tabella cresce molto
            # cursor.execute("CREATE INDEX IF NOT EXISTS idx_avg_times_type ON average_times(player_type)")
            # cursor.execute("CREATE INDEX IF NOT EXISTS idx_avg_times_recorded ON average_times(recorded_at)")
            conn.commit()
            logging.info("[AVG TIMES DB] Tabella average_times assicurata.")
        except sqlite3.Error as e:
            logging.error(f"[AVG TIMES DB] Errore creazione tabella: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()
            logging.debug("[AVG TIMES DB] Connessione chiusa e lock rilasciato")
