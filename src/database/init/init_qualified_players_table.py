import logging
import os
import sqlite3


def init_qualified_players_table(sqlite_lock):
    logging.debug("[QUALIFIED] Acquisizione del lock per SQLite")
    with sqlite_lock:
        logging.debug("[QUALIFIED] Lock acquisito")
        conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
        cursor = conn.cursor()
        logging.debug("[QUALIFIED] Creazione tabella qualified_players, se non esiste")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qualified_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                score_minutes REAL NOT NULL,  -- Punteggio in minuti (float)
                score_formatted TEXT NOT NULL, -- Punteggio formattato (es. 2m 30s)
                player_type TEXT CHECK(player_type IN ('couple', 'single', 'charlie')) NOT NULL,
                qualification_reason TEXT NOT NULL, -- 'best_today' or 'top_3_overall'
                qualification_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logging.debug("[QUALIFIED] Connessione chiusa e lock rilasciato")