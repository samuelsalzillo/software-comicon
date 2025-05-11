import logging
import os
import sqlite3


def init_skipped_table(sqlite_lock):
    logging.debug("[SKIPPED] Acquisizione del lock per SQLite")
    with sqlite_lock:
        logging.debug("[SKIPPED] Lock acquisito")

        conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
        cursor = conn.cursor()

        logging.debug("[SKIPPED] Creazione tabella skipped_players, se non esiste")
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS skipped_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_type TEXT CHECK(player_type IN ('couple', 'single', 'couple2', 'single2', 'charlie', 'statico')) NOT NULL,
                player_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                skipped_at DATETIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        logging.debug("[SKIPPED] Connessione chiusa e lock rilasciato")
