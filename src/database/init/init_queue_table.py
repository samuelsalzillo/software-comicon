import logging
import os
import sqlite3


def init_queue_table(sqlite_lock):
    logging.debug("[QUEUES] Acquisizione del lock per SQLite")
    with sqlite_lock:
        logging.debug("[QUEUES] Lock acquisito")

        conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
        cursor = conn.cursor()

        logging.debug("[QUEUES] Creazione tabella, se non esiste")
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS queues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_type TEXT CHECK(player_type IN ('couple', 'single', 'couple2', 'single2', 'charlie', 'statico')) NOT NULL,
                player_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                arrival_time DATETIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

        logging.debug("[QUEUES] Connessione chiusa e lock rilasciato")
