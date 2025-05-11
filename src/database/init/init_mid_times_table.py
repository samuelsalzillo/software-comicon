import logging
import os
import sqlite3


def init_mid_times_table(sqlite_lock):
    logging.debug("[MID TIMES DB] Acquisizione lock per init tabella mid_times")
    with sqlite_lock:
        logging.debug("[MID TIMES DB] Lock acquisito")
        try:
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
            cursor = conn.cursor()
            logging.debug("[MID TIMES DB] Creazione tabella mid_times, se non esiste")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mid_times (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    couple_type TEXT CHECK(couple_type IN ('couple1', 'couple2')) NOT NULL, -- 'couple1' o 'couple2'
                    mid_duration_minutes REAL NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            logging.info("[MID TIMES DB] Tabella mid_times assicurata.")
        except sqlite3.Error as e:
            logging.error(f"[MID TIMES DB] Errore creazione tabella: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()
            logging.debug("[MID TIMES DB] Connessione chiusa e lock rilasciato")