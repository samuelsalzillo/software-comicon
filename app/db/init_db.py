# app/db/init_db.py

import sqlite3
import logging
from threading import Lock

SQLITE_DB_PATH = 'stand_db.db'
sqlite_lock = Lock()

def init_sqlite():
    with sqlite_lock:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
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

def init_scoring_table():
    with sqlite_lock:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS scoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_type TEXT CHECK(player_type IN ('couple', 'single', 'single2', 'couple2', 'charlie', 'statico')) NOT NULL,
                player_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                score REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

def init_average_times_table():
    with sqlite_lock:
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS average_times (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_type TEXT CHECK(player_type IN ('couple', 'single', 'couple2', 'single2')) NOT NULL,
                    timer_duration_minutes REAL NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        except sqlite3.Error as e:
            logging.error(f"[AVG TIMES DB] Errore creazione tabella: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()

def init_mid_times_table():
    with sqlite_lock:
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mid_times (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    couple_type TEXT CHECK(couple_type IN ('couple1', 'couple2')) NOT NULL,
                    mid_duration_minutes REAL NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        except sqlite3.Error as e:
            logging.error(f"[MID TIMES DB] Errore creazione tabella: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()

def init_skipped_table():
    with sqlite_lock:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
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

def init_qualified_players_table():
    with sqlite_lock:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qualified_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                score_minutes REAL NOT NULL,
                score_formatted TEXT NOT NULL,
                player_type TEXT CHECK(player_type IN ('couple', 'single', 'charlie')) NOT NULL,
                qualification_reason TEXT NOT NULL,
                qualification_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

def init_charlie_timer_table():
    with sqlite_lock:
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS charlie_timer_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timer_duration_minutes REAL NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        except sqlite3.Error as e:
            logging.error(f"[CHARLIE TIMER DB] Errore creazione tabella: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()

def initialize_database():
    logging.info("[DB INIT] Avvio inizializzazione tabelle database")
    init_sqlite()
    init_scoring_table()
    init_average_times_table()
    init_mid_times_table()
    init_skipped_table()
    init_qualified_players_table()
    init_charlie_timer_table()
    logging.info("[DB INIT] Inizializzazione completata")
