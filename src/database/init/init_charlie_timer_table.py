import logging
import os
import sqlite3


def init_charlie_timer_table(sqlite_lock):
    logging.debug("[CHARLIE TIMER DB] Acquisizione lock per init tabella")
    with sqlite_lock:
        logging.debug("[CHARLIE TIMER DB] Lock acquisito")
        try:
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
            cursor = conn.cursor()
            logging.debug("[CHARLIE TIMER DB] Creazione tabella charlie_timer_scores, se non esiste")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS charlie_timer_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timer_duration_minutes REAL NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Opzionale: Aggiungere indici se la tabella diventa grande
            # cursor.execute("CREATE INDEX IF NOT EXISTS idx_charlie_timer_recorded_at ON charlie_timer_scores(recorded_at)")
            conn.commit()
            logging.info("[CHARLIE TIMER DB] Tabella charlie_timer_scores assicurata.")
        except sqlite3.Error as e:
            logging.error(f"[CHARLIE TIMER DB] Errore creazione tabella: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()
            logging.debug("[CHARLIE TIMER DB] Connessione chiusa e lock rilasciato")