import logging
import os
import sqlite3


def init_scoring_table(sqlite_lock):
    logging.debug("[SCORING] Acquisizione del lock per SQLite")
    with sqlite_lock:
        logging.debug("[SCORING] Lock acquisito")

        conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
        cursor = conn.cursor()

        logging.debug("[SCORING] Creazione tabella scoring, se non esiste")
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS scoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_type TEXT CHECK(player_type IN ('couple', 'single','single2','couple2' , 'charlie', 'statico')) NOT NULL,
                player_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                score REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        logging.debug("[SCORING] Connessione chiusa e lock rilasciato")


