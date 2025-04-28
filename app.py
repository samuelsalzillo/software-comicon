from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file
from main import GameBackend
import datetime
import os
import pytz
import subprocess
import time
import atexit
import logging
import sqlite3
import time
import subprocess
from io import BytesIO
from threading import Thread
from threading import Lock
import socket # per il print dell'ip

app = Flask(__name__)
backend = GameBackend()

# Impostazioni logging
logging.basicConfig(level=logging.DEBUG) 

sqlite_lock = Lock()
SQLITE_DB_PATH = 'stand_db.db'  # Database local MySQLite in cui salveremo le queue
BASE_URL = "http://localhost:2000"  # Bisogna cambiarlo con il sito delle queue si mercenari socs che andremo a creare


def init_sqlite():
    logging.debug("[QUEUES] Acquisizione del lock per SQLite")
    with sqlite_lock:
        logging.debug("[QUEUES] Lock acquisito")

        conn = sqlite3.connect(SQLITE_DB_PATH)
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


# Chiama la funzione per inizializzare il database
init_sqlite()


def init_scoring_table():
    logging.debug("[SCORING] Acquisizione del lock per SQLite")
    with sqlite_lock:
        logging.debug("[SCORING] Lock acquisito")

        conn = sqlite3.connect(SQLITE_DB_PATH)
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


# Chiama la funzione per inizializzare la tabella scoring
init_scoring_table()

def init_average_times_table():
    logging.debug("[AVG TIMES DB] Acquisizione lock per init tabella average_times")
    with sqlite_lock:
        logging.debug("[AVG TIMES DB] Lock acquisito")
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
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

# Chiamare la funzione all'avvio
init_average_times_table()

def init_mid_times_table():
    logging.debug("[MID TIMES DB] Acquisizione lock per init tabella mid_times")
    with sqlite_lock:
        logging.debug("[MID TIMES DB] Lock acquisito")
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
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

# Chiamare la funzione all'avvio
init_mid_times_table()

def load_mid_times_from_db():
    logging.debug("[LOAD MID TIMES] Tentativo caricamento storico mid times da DB.")
    loaded_rows = 0
    appended_mid1 = 0
    appended_mid2 = 0
    try:
        with sqlite_lock:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT couple_type, mid_duration_minutes
                FROM mid_times ORDER BY recorded_at ASC
            """)
            rows = cursor.fetchall()
            loaded_rows = len(rows)
            conn.close()
        logging.debug(f"[LOAD MID TIMES] Lock DB rilasciato. Trovati {loaded_rows} record mid time nel DB.")

        # Pulisci liste
        backend.couple_history_mid.clear()
        backend.couple_history_mid2.clear()
        logging.debug("[LOAD MID TIMES] Liste backend couple_history_mid e mid2 resettate.")

        for i, row in enumerate(rows):
            try:
                couple_type, mid_duration = row
                duration_minutes = float(mid_duration)
                logging.debug(f"[LOAD MID TIMES] Processing row {i+1}/{loaded_rows}: type={couple_type}, duration={duration_minutes:.4f}")

                if couple_type == 'couple1':
                    backend.couple_history_mid.append(duration_minutes)
                    appended_mid1 += 1
                    logging.debug(f"  -> Appended to couple_history_mid (new size: {len(backend.couple_history_mid)})")
                elif couple_type == 'couple2':
                    backend.couple_history_mid2.append(duration_minutes)
                    appended_mid2 += 1
                    logging.debug(f"  -> Appended to couple_history_mid2 (new size: {len(backend.couple_history_mid2)})")
                else:
                     logging.warning(f"  -> Unknown couple_type '{couple_type}' in mid_times table, row ignored.")

            except Exception as e:
                logging.warning(f"[LOAD MID TIMES] Errore processando riga {i+1}: {row}. Errore: {e}. Riga ignorata.")

        logging.info(f"[LOAD MID TIMES] Caricamento completato. Righe DB: {loaded_rows}. Appended Mid1: {appended_mid1}. Appended Mid2: {appended_mid2}.")
        logging.info(f"  -> Final backend list sizes: mid1={len(backend.couple_history_mid)}, mid2={len(backend.couple_history_mid2)}")

        # Ricalcola medie (DOPO aver caricato TUTTI i dati necessari, quindi magari chiamalo una sola volta alla fine di tutti i load_)
        # backend.update_averages() # Sposta questa chiamata alla fine di tutte le funzioni load_

    except sqlite3.Error as db_err:
         logging.error(f"[LOAD MID TIMES] Errore Database: {db_err}", exc_info=True)
    except Exception as e:
        logging.error(f"[LOAD MID TIMES] Errore generico: {e}", exc_info=True)

load_mid_times_from_db()

def load_average_times_from_db():
    logging.debug("[LOAD AVG TIMES] Tentativo caricamento storico timer per medie da DB.")
    loaded_rows = 0 # Contatore righe DB
    appended_couple = 0 # Contatore append coppie
    appended_single = 0 # Contatore append singoli
    try:
        with sqlite_lock:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            # ... (connessione e cursor) ...
            cursor.execute("""
                SELECT player_type, timer_duration_minutes
                FROM average_times ORDER BY recorded_at ASC
            """)
            rows = cursor.fetchall()
            loaded_rows = len(rows) # Quante righe dal DB?
            conn.close()
        logging.debug(f"[LOAD AVG TIMES] Lock DB rilasciato. Trovati {loaded_rows} record timer nel DB.")

        # Pulisci liste
        backend.couple_timer_history.clear()
        backend.single_timer_history.clear()
        logging.debug("[LOAD AVG TIMES] Liste backend *timer* resettate.")

        for i, row in enumerate(rows): # Aggiunto indice per logging
            try:
                player_type, timer_duration = row
                duration_minutes = float(timer_duration)
                logging.debug(f"[LOAD AVG TIMES] Processing row {i+1}/{loaded_rows}: type={player_type}, duration={duration_minutes:.4f}") # LOG RIGA

                if player_type in ('couple', 'couple2'):
                    backend.couple_timer_history.append(duration_minutes)
                    appended_couple += 1
                    logging.debug(f"  -> Appended to couple_timer_history (new size: {len(backend.couple_timer_history)})") # LOG APPEND
                elif player_type in ('single', 'single2'):
                    backend.single_timer_history.append(duration_minutes)
                    appended_single += 1
                    logging.debug(f"  -> Appended to single_timer_history (new size: {len(backend.single_timer_history)})") # LOG APPEND
                else:
                     logging.warning(f"  -> Unknown player_type '{player_type}' in average_times table, row ignored.")

            except Exception as e:
                logging.warning(f"[LOAD AVG TIMES] Errore processando riga {i+1}: {row}. Errore: {e}. Riga ignorata.")

        logging.info(f"[LOAD AVG TIMES] Caricamento completato. Righe DB: {loaded_rows}. Appended Couple Timers: {appended_couple}. Appended Single Timers: {appended_single}.")
        logging.info(f"  -> Final backend list sizes: couple_timer={len(backend.couple_timer_history)}, single_timer={len(backend.single_timer_history)}")

        # Ricalcola medie
        backend.update_averages() # Chiamato DOPO il caricamento
        logging.info("[LOAD AVG TIMES] Medie ricalcolate post-caricamento timers.")

    except sqlite3.Error as db_err:
         logging.error(f"[LOAD AVG TIMES] Errore Database: {db_err}", exc_info=True)
    except Exception as e:
        logging.error(f"[LOAD AVG TIMES] Errore generico: {e}", exc_info=True)

load_average_times_from_db()

def init_skipped_table():
    logging.debug("[SKIPPED] Acquisizione del lock per SQLite")
    with sqlite_lock:
        logging.debug("[SKIPPED] Lock acquisito")

        conn = sqlite3.connect(SQLITE_DB_PATH)
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

# Chiama la funzione per inizializzare la tabella skipped_players
init_skipped_table()

# Aggiungi questa funzione per caricare gli skippati all'avvio
def load_skipped_from_db():
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT player_type, player_id, player_name FROM skipped_players ORDER BY created_at DESC")
        rows = cursor.fetchall()

        # Pulisci le liste esistenti
        backend.skipped_couples.clear()
        backend.skipped_singles.clear()
        backend.skipped_couples2.clear()
        backend.skipped_singles2.clear()
        backend.skipped_charlie.clear()
        backend.skipped_statico.clear()

        for row in rows:
            player_type, player_id, player_name = row
            player_data = {'id': player_id, 'name': player_name}
            
            if player_type == 'couple':
                backend.skipped_couples.append(player_data)
            elif player_type == 'single':
                backend.skipped_singles.append(player_data)
            elif player_type == 'couple2':
                backend.skipped_couples2.append(player_data)
            elif player_type == 'single2':
                backend.skipped_singles2.append(player_data)
            elif player_type == 'charlie':
                backend.skipped_charlie.append(player_data)
            elif player_type == 'statico':
                backend.skipped_statico.append(player_data)

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Errore durante il caricamento degli skippati dal database: {e}")

# Carica gli skippati all'avvio dell'applicazione
load_skipped_from_db()

def load_scores_from_db():
    """
    Carica i punteggi NUMERICI dalla tabella 'scoring' nelle liste
    di storico del backend all'avvio dell'applicazione.
    Queste liste sono usate per calcolare le medie T_mid, T_total, etc.
    """
    logging.debug("[LOAD SCORES] Tentativo caricamento punteggi da DB.")
    try:
        # >>> ACQUISISCI IL LOCK <<<
        with sqlite_lock:
            logging.debug("[LOAD SCORES] Lock DB acquisito.")
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()

            # Seleziona il tipo di giocatore e il punteggio numerico
            # Ordina per data creazione se vuoi processarli in ordine cronologico
            cursor.execute("""
                SELECT player_type, player_id, score
                FROM scoring
                WHERE score IS NOT NULL
                ORDER BY created_at ASC
            """)
            rows = cursor.fetchall()
            conn.close()
        # >>> RILASCIA IL LOCK <<<
        logging.debug(f"[LOAD SCORES] Lock DB rilasciato. Trovati {len(rows)} punteggi.")

        # Pulisci le liste esistenti nel backend PRIMA di caricarle
        backend.couple_history_total.clear()
        backend.single_history.clear()
        backend.couple_history_total2.clear()
        backend.single_history2.clear()
        backend.charlie_history.clear()
        backend.statico_history.clear()
        logging.debug("[LOAD SCORES] Liste storico backend resettate.")

        loaded_counts = {'couple': 0, 'single': 0, 'charlie': 0, 'statico': 0}

        for row in rows:
            player_type, player_id, score_value = row
            try:
                score_minutes = float(score_value)
                if player_type == 'couple':
                    backend.couple_history_total.append((player_id, score_minutes))
                elif player_type == 'single':
                    backend.single_history.append((player_id, score_minutes))
                elif player_type == 'couple2':
                    backend.couple_history_total2.append((player_id, score_minutes))
                elif player_type == 'single2':
                    backend.single_history2.append((player_id, score_minutes))
                elif player_type == 'charlie':
                    backend.charlie_history.append((player_id, score_minutes))
                elif player_type == 'statico':
                    backend.statico_history.append((player_id, score_minutes))
            except Exception as e:
                logging.error(f"Error processing score row {row}: {e}")

        logging.info(f"[LOAD SCORES] Caricamento completato. Conteggi: Coppie={loaded_counts['couple']}, Singoli={loaded_counts['single']}, Charlie={loaded_counts['charlie']}, Statico={loaded_counts['statico']}")

        # Dopo aver caricato le storie, ricalcola subito le medie iniziali
        backend.update_averages()
        logging.info("[LOAD SCORES] Medie iniziali ricalcolate.")

    except sqlite3.Error as db_err:
         logging.error(f"[LOAD SCORES] Errore Database durante caricamento punteggi: {db_err}", exc_info=True)
    except Exception as e:
        logging.error(f"[LOAD SCORES] Errore generico durante caricamento punteggi: {e}", exc_info=True)



# Carica gli score all'avvio dell'applicazione
load_scores_from_db()


# Funzione per caricare le code dal database all'avvio
def load_queues_from_db():
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT player_type, player_id, player_name, arrival_time FROM queues ORDER BY created_at DESC")
        rows = cursor.fetchall()

        backend.queue_couples.clear()
        backend.queue_singles.clear()
        backend.queue_couples2.clear()
        backend.queue_singles2.clear()
        backend.queue_charlie.clear()
        backend.queue_statico.clear()

        for row in rows:
            player_type, player_id, player_name, arrival_time = row
            if player_type == 'couple':
                backend.queue_couples.append({'id': player_id, 'arrival': arrival_time})
            elif player_type == 'single':
                backend.queue_singles.append({'id': player_id, 'arrival': arrival_time})
            elif player_type == 'couple2':
                backend.queue_couples2.append({'id': player_id, 'arrival': arrival_time})
            elif player_type == 'single2':
                backend.queue_singles2.append({'id': player_id, 'arrival': arrival_time})
            elif player_type == 'charlie':
                backend.queue_charlie.append({'id': player_id, 'arrival': arrival_time})
            elif player_type == 'statico':
                backend.queue_statico.append({'id': player_id, 'arrival': arrival_time})

            backend.player_names[player_id] = player_name

            # Imposta il prossimo giocatore per Charlie
        if backend.queue_charlie:
            backend.next_player_charlie_id = backend.queue_charlie[0]['id']
            backend.next_player_charlie_name = backend.get_player_name(backend.next_player_charlie_id)
            backend.next_player_charlie_locked = True
        else:
            backend.next_player_charlie_id = None
            backend.next_player_charlie_name = None
            backend.next_player_charlie_locked = False

        if backend.queue_statico:
            backend.next_player_statico_id = backend.queue_statico[0]['id']
            backend.next_player_statico_name = backend.get_player_name(backend.next_player_statico_id)
            backend.next_player_statico_locked = True
        else:
            backend.next_player_statico_id = None
            backend.next_player_statico_name = None
            backend.next_player_statico_locked = False

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Errore durante il caricamento delle code dal database: {e}")


# Carica le code all'avvio dell'applicazione
load_queues_from_db()


def save_queues_to_db():
    while True:
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()

            # Cancella le vecchie code
            cursor.execute("DELETE FROM queues")
            conn.commit()

            # Salva le code delle coppie
            for couple in backend.queue_couples:
                cursor.execute(
                    "INSERT INTO queues (player_type, player_id, player_name, arrival_time) VALUES (?, ?, ?, ?) ",
                    ('couple', couple['id'], backend.get_player_name(couple['id']), couple['arrival'])
                )

            # Salva le code dei singoli
            for single in backend.queue_singles:
                cursor.execute(
                    "INSERT INTO queues (player_type, player_id, player_name, arrival_time) VALUES (?, ?, ?, ?)",
                    ('single', single['id'], backend.get_player_name(single['id']), single['arrival'])
                )

            # Salva le code delle coppie2
            for couple2 in backend.queue_couples2:
                cursor.execute(
                    "INSERT INTO queues (player_type, player_id, player_name, arrival_time) VALUES (?, ?, ?, ?)",
                    ('couple2', couple2['id'], backend.get_player_name(couple2['id']), couple2['arrival'])
                )   

            # Salva le code dei singoli2
            for single2 in backend.queue_singles2:
                cursor.execute(
                    "INSERT INTO queues (player_type, player_id, player_name, arrival_time) VALUES (?, ?, ?, ?)",
                    ('single2', single2['id'], backend.get_player_name(single2['id']), single2['arrival'])
                )

            # Salva le code di Charlie
            for charlie in backend.queue_charlie:
                cursor.execute(
                    "INSERT INTO queues (player_type, player_id, player_name, arrival_time) VALUES (?, ?, ?, ?)",
                    ('charlie', charlie['id'], backend.get_player_name(charlie['id']), charlie['arrival'])
                )

            # Salva le code di Statico
            for statico in backend.queue_statico:
                cursor.execute(
                    "INSERT INTO queues (player_type, player_id, player_name, arrival_time) VALUES (?, ?, ?, ?)",
                    ('statico', statico['id'], backend.get_player_name(statico['id']), statico['arrival'])
                )

            # Salva gli score
            cursor.execute("DELETE FROM scoring")
            for player_id, score in backend.couple_history_total:
                cursor.execute(
                    "INSERT INTO scoring (player_type, player_id, player_name, score) VALUES (?, ?, ?, ?)",
                    ('couple', player_id, backend.get_player_name(player_id), score)
                )
            for player_id, score in backend.single_history:
                cursor.execute(
                    "INSERT INTO scoring (player_type, player_id, player_name, score) VALUES (?, ?, ?, ?)",
                    ('single', player_id, backend.get_player_name(player_id), score)
                )
            for player_id, score in backend.couple_history_total2:
                cursor.execute(
                    "INSERT INTO scoring (player_type, player_id, player_name, score) VALUES (?, ?, ?, ?)",
                    ('couple2', player_id, backend.get_player_name(player_id), score)
                )
            for player_id, score in backend.single_history2:
                cursor.execute(
                    "INSERT INTO scoring (player_type, player_id, player_name, score) VALUES (?, ?, ?, ?)",
                    ('single', player_id, backend.get_player_name(player_id), score)
                )
            for player_id, score in backend.charlie_history:
                cursor.execute(
                    "INSERT INTO scoring (player_type, player_id, player_name, score) VALUES (?, ?, ?, ?)",
                    ('charlie', player_id, backend.get_player_name(player_id), score)
                )
            for player_id, score in backend.statico_history:
                cursor.execute(
                    "INSERT INTO scoring (player_type, player_id, player_name, score) VALUES (?, ?, ?, ?)",
                    ('statico', player_id, backend.get_player_name(player_id), score)
                )

            logging.debug("[DB SAVE THREAD] Cancellazione vecchi timer Charlie...")
            cursor.execute("DELETE FROM charlie_timer_scores")
            logging.debug(f"[DB SAVE THREAD] Salvataggio {len(backend.charlie_timer_history)} record timer Charlie...")
            for duration in backend.charlie_timer_history:
                    cursor.execute(
                        "INSERT INTO charlie_timer_scores (timer_duration_minutes) VALUES (?)",
                        (duration,) # Passa come tupla
                    )
            logging.debug("[DB SAVE THREAD] Timer Charlie salvati.")

            # Salva gli skippati
            cursor.execute("DELETE FROM skipped_players")
            for player in backend.skipped_couples:
                cursor.execute(
                    "INSERT INTO skipped_players (player_type, player_id, player_name, skipped_at) VALUES (?, ?, ?, ?)",
                    ('couple', player['id'], backend.get_player_name(player['id']), datetime.datetime.now())
                )
            for player in backend.skipped_singles:
                cursor.execute(
                    "INSERT INTO skipped_players (player_type, player_id, player_name, skipped_at) VALUES (?, ?, ?, ?)",
                    ('single', player['id'], backend.get_player_name(player['id']), datetime.datetime.now())
                )

            for player in backend.skipped_couples2:
                cursor.execute(
                    "INSERT INTO skipped_players (player_type, player_id, player_name, skipped_at) VALUES (?, ?, ?, ?)",
                    ('couple2', player['id'], backend.get_player_name(player['id']), datetime.datetime.now())
                )
            for player in backend.skipped_singles2:
                cursor.execute(
                    "INSERT INTO skipped_players (player_type, player_id, player_name, skipped_at) VALUES (?, ?, ?, ?)",
                    ('single2', player['id'], backend.get_player_name(player['id']), datetime.datetime.now())
                )
            for player in backend.skipped_charlie:
                cursor.execute(
                    "INSERT INTO skipped_players (player_type, player_id, player_name, skipped_at) VALUES (?, ?, ?, ?)",
                    ('charlie', player['id'], backend.get_player_name(player['id']), datetime.datetime.now())
                )
            for player in backend.skipped_statico:
                cursor.execute(
                    "INSERT INTO skipped_players (player_type, player_id, player_name, skipped_at) VALUES (?, ?, ?, ?)",
                    ('statico', player['id'], backend.get_player_name(player['id']), datetime.datetime.now())
                )

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore durante il salvataggio delle code nel database: {e}")
        time.sleep(10)  # Salva ogni 10 secondi

def init_qualified_players_table():
    logging.debug("[QUALIFIED] Acquisizione del lock per SQLite")
    with sqlite_lock:
        logging.debug("[QUALIFIED] Lock acquisito")
        conn = sqlite3.connect(SQLITE_DB_PATH)
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

init_qualified_players_table()

# --- NUOVA Funzione Init Tabella Timer Charlie ---
def init_charlie_timer_table():
    logging.debug("[CHARLIE TIMER DB] Acquisizione lock per init tabella")
    with sqlite_lock:
        logging.debug("[CHARLIE TIMER DB] Lock acquisito")
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
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

init_charlie_timer_table()

# --- NUOVA Funzione Load History Timer Charlie ---
def load_charlie_timer_history_from_db():
    logging.debug("[LOAD CHARLIE TIMERS] Tentativo caricamento storico timer Charlie da DB.")
    try:
        with sqlite_lock:
            logging.debug("[LOAD CHARLIE TIMERS] Lock DB acquisito.")
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            # Seleziona solo le durate, ordinate per data (opzionale ma buono)
            cursor.execute("""
                SELECT timer_duration_minutes
                FROM charlie_timer_scores
                ORDER BY recorded_at ASC
            """)
            rows = cursor.fetchall()
            conn.close()
        logging.debug(f"[LOAD CHARLIE TIMERS] Lock DB rilasciato. Trovati {len(rows)} record timer.")

        # Pulisci la lista esistente PRIMA di caricare
        backend.charlie_timer_history.clear()
        logging.debug("[LOAD CHARLIE TIMERS] Lista backend.charlie_timer_history resettata.")

        loaded_count = 0
        for row in rows:
            try:
                duration_minutes = float(row[0])
                backend.charlie_timer_history.append(duration_minutes)
                loaded_count += 1
            except (ValueError, TypeError, IndexError) as e:
                logging.warning(f"[LOAD CHARLIE TIMERS] Errore conversione/lettura durata timer: {row}. Errore: {e}. Riga ignorata.")

        logging.info(f"[LOAD CHARLIE TIMERS] Caricamento completato. Caricati {loaded_count} record timer.")

        # Ricalcola subito la media T_charlie dopo il caricamento
        backend.update_averages()
        logging.info("[LOAD CHARLIE TIMERS] Media T_charlie ricalcolata post-caricamento.")

    except sqlite3.Error as db_err:
         logging.error(f"[LOAD CHARLIE TIMERS] Errore Database durante caricamento storico timer: {db_err}", exc_info=True)
    except Exception as e:
        logging.error(f"[LOAD CHARLIE TIMERS] Errore generico durante caricamento storico timer: {e}", exc_info=True)


load_charlie_timer_history_from_db()

# Avvia il thread per il salvataggio periodico
save_thread = Thread(target=save_queues_to_db, daemon=True)
save_thread.start()



def initialize_queues():
    rome_tz = pytz.timezone('Europe/Rome')
    now = datetime.datetime.now(rome_tz)
    # backend.queue_couples.clear()
    # backend.queue_singles.clear()
    # backend.queue_charlie.clear()


initialize_queues()


# Aggiungi queste route
@app.route('/controls/statico')
def controls_statico():
    return render_template('controls_statico.html')

@app.route('/controls/combined')
def controls_combined():
    return render_template('controls_combined1.html')

@app.route('/controls/combined2')
def controls_combined2():
    return render_template('controls_combined2.html')

@app.route('/add_statico', methods=['POST'])
def add_statico():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id > 100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    statico_id = f"{name.upper()} {int(id):03d}"
    backend.add_statico_player(statico_id, name)
    return jsonify(success=True)

@app.route('/skip_statico_player', methods=['POST'])
def skip_statico_player():
    player_id = request.json.get('id')
    if player_id:
        backend.skip_statico_player(player_id)
        return jsonify(
            success=True,
            next_player_statico_id=backend.next_player_statico_id,
            next_player_statico_name=backend.next_player_statico_name
        )
    return jsonify(success=False, error="Player ID is required"), 400

@app.route('/statico_start', methods=['POST'])
def statico_start():
    if not backend.queue_statico:
        return jsonify(success=False, error="La coda di Statico è vuota. Non è possibile avviare il gioco.")
    backend.start_statico_game()
    return jsonify(success=True, current_player_delta=backend.current_player_delta,
                  current_player_echo=backend.current_player_echo)

@app.route('/statico_stop', methods=['POST'])
def statico_stop():
    if backend.current_player_delta or backend.current_player_echo:
        player_id = backend.current_player_delta['id'] if backend.current_player_delta else backend.current_player_echo['id']
        now = backend.get_current_time()
        if player_id and player_id in backend.player_start_times:
            backend.record_statico_game((now - backend.player_start_times[player_id]).total_seconds() / 60)
            backend.current_player_delta = None
            backend.current_player_echo = None
            return jsonify(success=True)
        else:
            return jsonify(success=False, error="Errore nel recupero del tempo di inizio del giocatore Statico.")
    return jsonify(success=False, error="Nessun giocatore Statico in pista.")


@app.route('/')
def index():
    return redirect(url_for('dashboard'))


@app.route('/controls/cassa')
def controls_cassa():
    return render_template('controls_cassa.html')


@app.route('/controls/couple')
def controls_couple():
    return render_template('controls_couple.html')


@app.route('/controls/single')
def controls_single():
    return render_template('controls_single.html')


@app.route('/controls/charlie')
def controls_charlie():
    return render_template('controls_charlie.html')


@app.route('/get_scores', methods=['GET'])
def get_scores():
    leaderboard = backend.get_leaderboard()
    return jsonify(leaderboard)


@app.route('/scoring')
def scoring():
    leaderboard = backend.get_leaderboard()
    return render_template('scoring.html', leaderboard=leaderboard)


@app.route('/keypad')
def keypad():
    return render_template('keypad.html')

@app.route('/keypad2')
def keypad2():
    return render_template('keypad2.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/add_couple', methods=['POST'])
def add_couple():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id >100: 
        return jsonify(success=False, error="ID must be less than 100"), 400
    couple_id = f"{name.upper()} {int(id):03d}"
    backend.add_couple(couple_id, name)
    return jsonify(success=True)


@app.route('/add_single', methods=['POST'])
def add_single():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id >100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    single_id = f"{name.upper()} {int(id):03d}"
    backend.add_single(single_id, name)
    return jsonify(success=True)


@app.route('/add_couple2', methods=['POST'])
def add_couple2():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:  
        return jsonify(success=False, error="ID and name are required"), 400
    if id >100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    couple2_id = f"{name.upper()} {int(id):03d}"
    backend.add_couple2(couple2_id, name)
    return jsonify(success=True)


@app.route('/add_single2', methods=['POST'])
def add_single2():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:  
        return jsonify(success=False, error="ID and name are required"), 400
    if id >100: 
        return jsonify(success=False, error="ID must be less than 100"), 400
    single2_id = f"{name.upper()} {int(id):03d}"
    backend.add_single2(single2_id, name)
    return jsonify(success=True)


@app.route('/add_charlie', methods=['POST'])
def add_charlie():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id >100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    charlie_id = f"{name.upper()} {int(id):03d}"
    backend.add_charlie_player(charlie_id, name)
    return jsonify(success=True)


@app.route('/add_charlie_player', methods=['POST'])
def add_charlie_player():
    name = request.json.get('name')
    id = request.json.get('id')
    if not name or not id:
        return jsonify(success=False, error="Name and id are required"), 400
    if id >100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    player_id = f"{name.upper()} {int(id):03d}"
    backend.add_charlie_player(player_id, name)

    if not backend.next_player_charlie_id and backend.queue_charlie:
        backend.next_player_charlie_id = backend.queue_charlie[0]['id']
        backend.next_player_charlie_name = backend.get_player_name(backend.next_player_charlie_id)
        backend.next_player_charlie_locked = True

    return jsonify(success=True, player_id=player_id, name=name)


@app.route('/queue')
def queue():
    return render_template('queue.html')


@app.route('/simulate', methods=['GET'])
def simulate():
    couples_board, singles_board, couples2_board, singles2_board, charlie_board, statico_board = backend.get_waiting_board()
    next_player_alfa_bravo_id = backend.next_player_alfa_bravo_id
    next_player_alfa_bravo_id2 = backend.next_player_alfa_bravo_id2
    next_player_charlie_id = backend.next_player_charlie_id
    next_player_charlie_name = backend.next_player_charlie_name
    now = backend.get_current_time()

    alfa_remaining = max(0, (backend.localize_time(backend.ALFA_next_available) - now).total_seconds() / 60)
    bravo_remaining = max(0, (backend.localize_time(backend.BRAVO_next_available) - now).total_seconds() / 60)
    alfa2_remaining = max(0, (backend.localize_time(backend.ALFA_next_available2) - now).total_seconds() / 60)
    bravo2_remaining = max(0, (backend.localize_time(backend.BRAVO_next_available2) - now).total_seconds() / 60)
    durations = backend.get_durations()
    formatted_charlie_board = []
    for pos, player_id, time_est in charlie_board:
        formatted_charlie_board.append({
            'id': player_id,
            'name': backend.get_player_name(player_id),
            'estimated_time': time_est
        })

    formatted_couples_board = []
    for pos, player_id, time_est in couples_board:
        formatted_couples_board.append({
            'id': player_id,
            'name': backend.get_player_name(player_id),
            'estimated_time': time_est
        })

    formatted_singles_board = []
    for pos, player_id, time_est in singles_board:
        formatted_singles_board.append({
            'id': player_id,
            'name': backend.get_player_name(player_id),
            'estimated_time': time_est
        })


    formatted_couples2_board = []
    for pos, player_id, time_est in couples2_board:
        formatted_couples2_board.append({
            'id': player_id,
            'name': backend.get_player_name(player_id),
            'estimated_time': time_est
        })  

    formatted_singles2_board = []
    for pos, player_id, time_est in singles2_board:
        formatted_singles2_board.append({
            'id': player_id,
            'name': backend.get_player_name(player_id),
            'estimated_time': time_est
        })  

    # Aggiungo la board per statico
    formatted_statico_board = []
    for pos, player_id, time_est in statico_board:
        formatted_statico_board.append({
            'id': player_id,
            'name': backend.get_player_name(player_id),
            'estimated_time': time_est
        })    

    next_player_alfa_bravo_name = backend.get_player_name(
        next_player_alfa_bravo_id) if next_player_alfa_bravo_id else None
    next_player_alfa_bravo_name2 = backend.get_player_name(
        next_player_alfa_bravo_id2) if next_player_alfa_bravo_id2 else None
    current_player_alfa = backend.current_player_alfa
    current_player_bravo = backend.current_player_bravo
    current_player_alfa2 = backend.current_player_alfa2
    current_player_bravo2 = backend.current_player_bravo2
    current_player_charlie = backend.current_player_charlie

    single_in_alfa = (
            isinstance(backend.current_player_alfa, dict) and
            'name' in backend.current_player_alfa and
            backend.current_player_alfa['name'] == "BLU"
    )
    couple_in_alfa = (
            isinstance(backend.current_player_alfa, dict) and
            'name' in backend.current_player_alfa and
            backend.current_player_alfa['name'] == "GIALLO"
    )
    couple_in_bravo = (
            isinstance(backend.current_player_bravo, dict) and
            'name' in backend.current_player_bravo and
            backend.current_player_bravo['name'] == "GIALLO"
    )
    single_in_alfa2 = (
            isinstance(backend.current_player_alfa2, dict) and
            'name' in backend.current_player_alfa2 and
            backend.current_player_alfa2['name'] == "BLU"
    )
    couple_in_alfa2 = (
            isinstance(backend.current_player_alfa2, dict) and
            'name' in backend.current_player_alfa2 and
            backend.current_player_alfa2['name'] == "GIALLO"
    )
    couple_in_bravo2 = (
            isinstance(backend.current_player_bravo2, dict) and
            'name' in backend.current_player_bravo2 and
            backend.current_player_bravo2['name'] == "GIALLO"
    )   

    now = backend.get_current_time()
    backend.ALFA_next_available = backend.localize_time(backend.ALFA_next_available)
    backend.BRAVO_next_available = backend.localize_time(backend.BRAVO_next_available)
    backend.ALFA_next_available2 = backend.localize_time(backend.ALFA_next_available2)
    backend.BRAVO_next_available2 = backend.localize_time(backend.BRAVO_next_available2)
    backend.CHARLIE_next_available = backend.localize_time(backend.CHARLIE_next_available)
    backend.DELTA_next_available = backend.localize_time(backend.DELTA_next_available)
    backend.ECHO_next_available = backend.localize_time(backend.ECHO_next_available)


    alfa_remaining = max(0, (backend.ALFA_next_available - now).total_seconds() / 60)
    bravo_remaining = max(0, (backend.BRAVO_next_available - now).total_seconds() / 60)
    alfa2_remaining = max(0, (backend.ALFA_next_available2 - now).total_seconds() / 60)
    bravo2_remaining = max(0, (backend.BRAVO_next_available2 - now).total_seconds() / 60)
    charlie_remaining = max(0, (backend.CHARLIE_next_available - now).total_seconds() / 60)
    delta_remaining = max(0, (backend.DELTA_next_available - now).total_seconds() / 60)
    echo_remaining = max(0, (backend.ECHO_next_available - now).total_seconds() / 60)

    can_stop_couple1 = backend.can_stop_couple()
    can_stop_couple2 = backend.can_stop_couple2()
    # Nota: Per i singoli, lo stop è sempre possibile se il gioco è attivo
    can_stop_single1 = backend.current_player_alfa is not None and backend.current_player_alfa.get('id','').startswith("BLU")
    can_stop_single2 = backend.current_player_alfa2 is not None and backend.current_player_alfa2.get('id','').startswith("BIANCO")

    return jsonify(
        couples=formatted_couples_board,
        singles=formatted_singles_board,
        couples2=formatted_couples2_board,
        singles2=formatted_singles2_board,
        charlie=formatted_charlie_board,
        statico=formatted_statico_board,
        next_player_alfa_bravo_id=next_player_alfa_bravo_id,
        next_player_alfa_bravo_name=next_player_alfa_bravo_name,
        next_player_alfa_bravo_id2=next_player_alfa_bravo_id2,
        next_player_alfa_bravo_name2=next_player_alfa_bravo_name2,
        next_player_charlie_id=next_player_charlie_id,
        next_player_charlie_name=next_player_charlie_name,
        next_player_statico_id=backend.next_player_statico_id,  # Aggiungiamo
        next_player_statico_name=backend.next_player_statico_name,  # Aggiungiamo
        current_player_alfa=current_player_alfa,
        current_player_bravo=current_player_bravo,
        current_player_alfa2=current_player_alfa2,
        current_player_bravo2=current_player_bravo2,
        current_player_charlie=current_player_charlie,
        current_player_delta=backend.current_player_delta,  # Aggiungiamo
        current_player_echo=backend.current_player_echo,  # Aggiungiamo
        player_icon_url=url_for('static', filename='icons/Vector.svg'),
        alfa_status='Occupata' if backend.current_player_alfa else 'Libera',
        bravo_status='Occupata' if backend.current_player_bravo else 'Libera',
        alfa2_status='Occupata' if backend.current_player_alfa2 else 'Libera',
        bravo2_status='Occupata' if backend.current_player_bravo2 else 'Libera',
        charlie_status='Occupata' if backend.current_player_charlie else 'Libera',
        delta_status='Occupata' if backend.current_player_delta else 'Libera',  # Aggiungiamo
        echo_status='Occupata' if backend.current_player_echo else 'Libera',  # Aggiungiamo
        alfa_remaining=f"{int(alfa_remaining)}min" if alfa_remaining > 0 else "0min",
        bravo_remaining=f"{int(bravo_remaining)}min" if bravo_remaining > 0 else "0min",
        alfa2_remaining=f"{int(alfa2_remaining)}min" if alfa2_remaining > 0 else "0min",
        bravo2_remaining=f"{int(bravo2_remaining)}min" if bravo2_remaining > 0 else "0min",
        charlie_remaining=f"{int(charlie_remaining)}min" if charlie_remaining > 0 else "0min",
        delta_remaining=f"{int(delta_remaining)}min" if delta_remaining > 0 else "0min",  # Aggiungiamo
        echo_remaining=f"{int(echo_remaining)}min" if echo_remaining > 0 else "0min",  # Aggiungiamo
        alfa_duration=durations.get('alfa', "N/D"), 
        bravo_duration=durations.get('bravo', "N/D"),
        alfa2_duration=durations.get('alfa2', "N/D"),
        bravo2_duration=durations.get('bravo2', "N/D"),
        charlie_duration=durations.get('charlie', "N/D"),
        delta_duration=durations.get('delta', "N/D"),  # Aggiungiamo
        echo_duration=durations.get('echo', "N/D"),  # Aggiungiamo
        can_stop_couple1=can_stop_couple1,
        can_stop_couple2=can_stop_couple2,
        can_stop_single1=can_stop_single1,
        can_stop_single2=can_stop_single2
    )


@app.route('/button_press', methods=['POST'])
def button_press():
    button = request.json.get('button')
    now = backend.get_current_time()


    if button in ['first_start', 'second_start', 'first_start2', 'second_start2',
                  'third', 'third2',
                  'charlie_start', 'charlie_stop', # charlie_stop verrà modificato dopo
                  'statico_start_delta', 'statico_start_echo',
                  'statico_stop_delta', 'statico_stop_echo']:

        if button == 'first_start':
            if not backend.queue_couples:
                return jsonify(success=False, error="La coda delle coppie è vuota. Non è possibile avviare il gioco.")
            
            backend.start_game(is_couple=True)
            return jsonify(success=True, start_time=now.isoformat(), current_player_bravo=backend.current_player_bravo,
                        current_player_alfa=backend.current_player_alfa)
        
        elif button == 'first_start2': # NUOVO CASO SPECIFICO
            if not backend.queue_couples2: # Controlla queue_couples2
                return jsonify(success=False, error="La coda Coppie 2 (Rosa) è vuota.")
            try:
                backend.start_game2(is_couple=True) # Chiama start_game2
                return jsonify(success=True, start_time=now.isoformat(),
                            current_player_bravo2=backend.current_player_bravo2,
                            current_player_alfa2=backend.current_player_alfa2)
            except ValueError as e:
                return jsonify(success=False, error=str(e)), 400

        elif button == 'second_start':
            if not backend.queue_singles:
                return jsonify(success=False, error="La coda dei singoli è vuota. Non è possibile avviare il gioco.")
            backend.start_game(is_couple=False)
            return jsonify(success=True, start_time=now.isoformat(), current_player_alfa=backend.current_player_alfa)
        
        elif button == 'second_start2':
            if not backend.queue_singles2:
                return jsonify(success=False, error="La coda dei singoli è vuota. Non è possibile avviare il gioco.")
            backend.start_game2(is_couple=False)


            return jsonify(success=True, start_time=now.isoformat(), current_player_alfa2=backend.current_player_alfa2)



        elif button == 'third':
            backend.button_third_pressed()
            return jsonify(success=True)
        
        elif button == 'third2':
                try:
                    # Chiama la funzione specifica nel backend
                    backend.button_third_pressed2()
                    logging.info("Metà percorso 2 (third2) attivato con successo.")
                    return jsonify(success=True)
                except ValueError as e: # Cattura l'errore se non c'è la coppia giusta
                    logging.warning(f"Attivazione third2 fallita: {e}")
                    return jsonify(success=False, error=str(e)), 400 # Restituisce l'errore al frontend
                except Exception as e: # Cattura altri errori imprevisti
                    logging.error(f"Errore imprevisto durante l'attivazione di third2: {e}", exc_info=True)
                    return jsonify(success=False, error="Errore interno del server."), 500
        

        if button == 'charlie_start':
            if not backend.queue_charlie:
                logging.warning(f"Charlie start aborted: Queue empty.")
                return jsonify(success=False, error="La coda di Charlie è vuota.")
            try:
                backend.start_charlie_game()
                logging.info(f"Charlie game started for player: {backend.current_player_charlie}")
                response_data = {
                    'success': True,
                    'current_player_charlie': backend.current_player_charlie
                }
                return(jsonify(response_data))
            except Exception as e:
                logging.error(f"Error during charlie_start: {e}", exc_info=True)
                response_data['error'] = f"Errore avvio Charlie: {e}"

        elif button == 'charlie_stop':
            player_info = backend.current_player_charlie
            if player_info and player_info.get('id'):
                player_id = player_info['id']
                start_time = backend.player_start_times.get(player_id)
                if start_time:
                    timer_duration_minutes = (now - start_time).total_seconds() / 60.0
                    logging.info(f"Charlie stop requested for {player_id}. Timer duration: {timer_duration_minutes:.4f} min.")
                    try:
                        # Chiama record_charlie_game SOLO con la durata del timer
                        backend.record_charlie_game(timer_duration_minutes)

                        # Prepara la risposta per il frontend, includendo chi ha finito
                        response_data = {
                            'success': True,
                            'player_id': player_id,
                            'player_name': backend.get_player_name(player_id) # Passa il nome
                        }
                        return(jsonify(response_data))
                        # NON salvare in scoring qui, NON checkare qualifica qui
                        logging.info(f"Charlie timer recorded for {player_id}. Ready for manual input.")
                    except Exception as e:
                        logging.error(f"Error during backend.record_charlie_game: {e}", exc_info=True)
                        response_data['error'] = f"Errore registrazione timer Charlie: {e}"
                        return(jsonify(response_data))

                else:
                    logging.error(f"Charlie stop failed for {player_id}: Start time not found.")
                    # Forse è meglio chiamare comunque record_charlie_game con 0 o T_default?
                    # backend.record_charlie_game(backend.T_charlie) # Fallback?
                    response_data['error'] = f"Errore: Orario inizio non trovato per {player_id}."
                    return(jsonify(response_data))

            else:
                logging.warning(f"Charlie stop requested but no player active.")
                response_data['error'] = "Nessun giocatore Charlie attivo da fermare."

        # Nuovi casi per Statico DELTA e ECHO
        elif button == 'statico_start_delta':
            if not backend.queue_statico:
                return jsonify(success=False, error="La coda di Statico è vuota. Non è possibile avviare il gioco.")
            if backend.current_player_delta:
                return jsonify(success=False, error="La pista DELTA è già occupata.")
            
            backend.start_statico_game(pista='delta')
            return jsonify(
                success=True,
                current_player_delta=backend.current_player_delta,
                current_player_echo=None
            )

        elif button == 'statico_start_echo':
            if not backend.queue_statico:
                return jsonify(success=False, error="La coda di Statico è vuota. Non è possibile avviare il gioco.")
            if backend.current_player_echo:
                return jsonify(success=False, error="La pista ECHO è già occupata.")
            
            backend.start_statico_game(pista='echo')
            return jsonify(
                success=True,
                current_player_delta=None,
                current_player_echo=backend.current_player_echo
            )

        elif button == 'statico_stop_delta':
            if backend.current_player_delta:
                player_id = backend.current_player_delta.get('id')
                if player_id and player_id in backend.player_start_times:
                    backend.record_statico_game(
                        (now - backend.player_start_times[player_id]).total_seconds() / 60,
                        pista='delta'
                    )
                    backend.current_player_delta = None
                    return jsonify(success=True)
                else:
                    return jsonify(success=False, error="Errore nel recupero del tempo di inizio del giocatore Statico (DELTA).")
            return jsonify(success=False, error="Nessun giocatore Statico in pista DELTA.")

        elif button == 'statico_stop_echo':
            if backend.current_player_echo:
                player_id = backend.current_player_echo.get('id')
                if player_id and player_id in backend.player_start_times:
                    backend.record_statico_game(
                        (now - backend.player_start_times[player_id]).total_seconds() / 60,
                        pista='echo'
                    )
                    backend.current_player_echo = None
                    return jsonify(success=True)
                else:
                    return jsonify(success=False, error="Errore nel recupero del tempo di inizio del giocatore Statico (ECHO).")
            return jsonify(success=False, error="Nessun giocatore Statico in pista ECHO.")

    elif button in ['first_stop', 'second_stop', 'first_stop2', 'second_stop2']:
        player_id = None
        player_name = None
        game_time_minutes = None
        player_type = None # 'couple' or 'single'
        mid_time_approx = None # Solo per coppie

        try:
            if button == 'first_stop':
                can_stop = backend.can_stop_couple()
                if not can_stop: return jsonify(success=False, error="Stop coppia non possibile (metà percorso?).")
                current_p = backend.current_player_couple # La coppia che è in Bravo
                if not current_p: return jsonify(success=False, error="Nessuna coppia attiva trovata per lo stop.")
                player_id = current_p['id']
                player_type = 'couple'
                start_time = backend.player_start_times.get(player_id)

            elif button == 'second_stop':
                current_p = backend.current_player_alfa
                if not (current_p and current_p.get('id','').startswith("BLU")):
                    return jsonify(success=False, error="Nessun singolo (BLU) in pista ALFA.")
                player_id = current_p['id']
                player_type = 'single'
                start_time = backend.player_start_times.get(player_id)
                can_stop = True # Lo stop per singolo è sempre possibile se è in pista

            elif button == 'first_stop2':
                can_stop = backend.can_stop_couple2()
                if not can_stop: return jsonify(success=False, error="Stop coppia 2 non possibile (metà percorso?).")
                current_p = backend.current_player_couple2
                if not current_p: return jsonify(success=False, error="Nessuna coppia 2 attiva trovata per lo stop.")
                player_id = current_p['id']
                player_type = 'couple2' # Tipo specifico per il DB average_times
                start_time = backend.player_start_times.get(player_id)

            elif button == 'second_stop2':
                current_p = backend.current_player_alfa2
                if not (current_p and current_p.get('id','').startswith("BIANCO")):
                    return jsonify(success=False, error="Nessun singolo (BIANCO) in pista ALFA 2.")
                player_id = current_p['id']
                player_type = 'single2' # Tipo specifico
                start_time = backend.player_start_times.get(player_id)
                can_stop = True

            # Verifica comune
            if not player_id: return jsonify(success=False, error="ID giocatore non trovato.")
            if not start_time:
                logging.error(f"Start time missing for {player_id} on {button}")
                # Cosa fare qui? Non possiamo calcolare la durata.
                # Forse forzare uno stato di errore nel frontend?
                return jsonify(success=False, error=f"Orario inizio non trovato per {player_id}.")

            player_name = backend.get_player_name(player_id)
            timer_duration_minutes = (now - start_time).total_seconds() / 60.0
            logging.info(f"Stop '{button}' premuto per {player_id} ({player_name}). Durata Timer Calcolata: {timer_duration_minutes:.4f} min.")

        except Exception as e:
            logging.error(f"Errore durante la preparazione dello stop per {button}: {e}", exc_info=True)
            return jsonify(success=False, error=f"Errore interno preparazione stop: {e}"), 500

        # 2. NON fare altro qui (no record, no save, no check qualifica)
        #    Restituisci i dati al frontend per il modal delle penalità

        logging.info(f"--- Button Press (Stop Prep): {button} SUCCESS ---")
        return jsonify(
            success=True,
            action="penalty_input_required", # Segnala al frontend cosa fare
            player_id=player_id,
            player_name=player_name,
            timer_duration_minutes=timer_duration_minutes,
            player_type=player_type # Es: 'couple', 'single', 'couple2', 'single2'
        )

@app.route('/submit_combined_score', methods=['POST'])
def submit_combined_score():
    data = request.json
    logging.debug(f"Received /submit_combined_score data: {data}")
    player_id = data.get('player_id')
    player_name = data.get('player_name')
    player_type = data.get('player_type') # 'couple', 'single', 'couple2', 'single2'
    timer_duration_str = data.get('timer_duration_minutes')
    official_score_str = data.get('official_score_minutes')
    mid_time_approx = None # Potrebbe servire per record_couple_game? Vediamo...

    # Validazione input base
    if not all([player_id, player_name, player_type,
                timer_duration_str is not None, official_score_str is not None]):
        logging.warning("Submit combined score failed: Missing data.")
        return jsonify(success=False, qualified=False, reason=None, error="Dati punteggio finale mancanti."), 400

    try:
        timer_duration = float(timer_duration_str)
        official_score = float(official_score_str)
        now = backend.get_current_time()
        score_formatted = backend.format_time(official_score)

        logging.info(f"[COMBINED SCORE SUBMIT] Player: {player_id} ({player_name}), Type: {player_type}, Timer: {timer_duration:.4f}, Score: {official_score:.4f} ({score_formatted})")

        # 1. Salva Timer Duration nel DB per le medie
        try:
            with sqlite_lock:
                conn = sqlite3.connect(SQLITE_DB_PATH)
                cursor = conn.cursor()
                # Inserisci il record specifico del timer
                execute_with_retry(
                    cursor,
                    "INSERT INTO average_times (player_type, timer_duration_minutes, recorded_at) VALUES (?, ?, ?)",
                    (player_type, timer_duration, now)
                )
                conn.commit()
                conn.close()
            logging.info(f"[AVG TIME DB SAVE] Success for {player_id} ({player_type}).")
        except sqlite3.Error as db_err:
            logging.error(f"[AVG TIME DB SAVE] Failed for {player_id}: {db_err}", exc_info=True)
            # Potremmo decidere di continuare comunque o ritornare errore? Per ora continuiamo.
        except Exception as e:
            logging.error(f"[AVG TIME DB SAVE] Failed (General Error) for {player_id}: {e}", exc_info=True)
            # Continuiamo

        # 2. Salva Official Score nel DB per la classifica
        try:
            with sqlite_lock:
                conn = sqlite3.connect(SQLITE_DB_PATH)
                cursor = conn.cursor()
                # Determina il player_type corretto per la tabella scoring ('couple' o 'single')
                scoring_player_type = 'couple' if player_type in ('couple', 'couple2') else 'single'
                execute_with_retry(
                    cursor,
                    "INSERT INTO scoring (player_type, player_id, player_name, score, created_at) VALUES (?, ?, ?, ?, ?)",
                    (scoring_player_type, player_id, player_name, official_score, now)
                )
                conn.commit()
                conn.close()
            logging.info(f"[SCORING DB SAVE] Success for {player_id} ({scoring_player_type}).")
        except sqlite3.Error as db_err:
            logging.error(f"[SCORING DB SAVE] Failed for {player_id}: {db_err}", exc_info=True)
            return jsonify(success=False, qualified=False, reason=None, error=f"Errore DB salvataggio score: {db_err}"), 500
        except Exception as e:
            logging.error(f"[SCORING DB SAVE] Failed (General Error) for {player_id}: {e}", exc_info=True)
            return jsonify(success=False, qualified=False, reason=None, error=f"Errore generico salvataggio score: {e}"), 500


        # 3. Chiama il metodo backend per aggiornare medie e stato interno
        #    Passa SIA timer_duration SIA official_score
        try:
            if player_type == 'couple':
                # Calcola mid_time_approx se necessario per T_mid (come faceva prima button_press)
                # start_time = backend.player_start_times.get(player_id) # Start time dovrebbe essere già stato rimosso da record_...
                # alfa_avail = backend.localize_time(backend.ALFA_next_available)
                # mid_time_approx = (alfa_avail - start_time).total_seconds() / 60 if start_time and alfa_avail > start_time else backend.T_mid
                backend.record_couple_game(timer_duration, official_score)
            elif player_type == 'single':
                backend.record_single_game(timer_duration, official_score)
            elif player_type == 'couple2':
                backend.record_couple2_game(timer_duration, official_score)
            elif player_type == 'single2':
                backend.record_single2_game(timer_duration, official_score)
            logging.debug(f"Backend record method called successfully for {player_id}")
        except Exception as e:
             logging.error(f"Error calling backend record method for {player_id} ({player_type}): {e}", exc_info=True)
             # Anche se c'è errore qui, i dati sono salvati, quindi procedi col check qualifica


        # 4. Controlla la qualifica usando l'OFFICIAL SCORE
        scoring_player_type = 'couple' if player_type in ('couple', 'couple2') else 'single'
        logging.debug(f"Checking qualification for {player_id} with score={official_score}, type={scoring_player_type}") # Log prima del check
        is_qualified, reason = backend.check_qualification(official_score, scoring_player_type)
        logging.info(f"[COMBINED QUAL CHECK] Player: {player_id}, Score: {official_score:.4f}, Qualified: {is_qualified}, Reason: {reason}")


        # 5. Ritorna il risultato al frontend
        return jsonify(
            success=True,
            qualified=is_qualified,
            reason=reason,
            # Passa indietro i dati necessari per il modal contatti
            player_id=player_id,
            player_name=player_name,
            recorded_score=official_score, # Punteggio ufficiale che ha qualificato
            player_type=scoring_player_type # Tipo per il modal contatti ('couple' o 'single')
        )

    except ValueError as ve:
        logging.error(f"Invalid numeric format in submit_combined_score: {ve}. Data: {data}")
        return jsonify(success=False, qualified=False, reason=None, error=f"Formato numerico non valido: {ve}"), 400
    except Exception as e:
        logging.error(f"[COMBINED SCORE SUBMIT] Failed processing score for {player_id}: {e}", exc_info=True)
        return jsonify(success=False, qualified=False, reason=None, error=f"Errore elaborazione punteggio finale: {e}"), 500

@app.route('/submit_charlie_score', methods=['POST'])
def submit_charlie_score():
    data = request.json
    logging.debug(f"Received /submit_charlie_score data: {data}")
    player_id = data.get('player_id')
    player_name = data.get('player_name') # Ricevi anche il nome
    minutes_str = data.get('minutes')
    seconds_str = data.get('seconds')
    milliseconds_str = data.get('milliseconds')

    if not all([player_id, player_name is not None, minutes_str is not None, seconds_str is not None, milliseconds_str is not None]):
        logging.warning("Submit charlie score failed: Missing data.")
        return jsonify(success=False, qualified=False, reason=None, error="Dati punteggio mancanti."), 400

    try:
        minutes = int(minutes_str)
        seconds = int(seconds_str)
        milliseconds = int(milliseconds_str)

        if not (0 <= minutes < 60 and 0 <= seconds < 60 and 0 <= milliseconds < 1000):
             raise ValueError("Valori tempo fuori range.")

        # Calcola il punteggio ufficiale in minuti (float)
        manual_score_minutes = minutes + (seconds / 60.0) + (milliseconds / 60000.0)
        score_formatted = backend.format_time(manual_score_minutes)
        now = backend.get_current_time()

        logging.info(f"[CHARLIE SCORE SUBMIT] Player: {player_id} ({player_name}), Manual Score: {manual_score_minutes:.4f} min ({score_formatted})")

        # 1. Salva nella tabella scoring
        try:
            with sqlite_lock:
                conn = sqlite3.connect(SQLITE_DB_PATH)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO scoring (player_type, player_id, player_name, score, created_at) VALUES (?, ?, ?, ?, ?)",
                    ('charlie', player_id, player_name, manual_score_minutes, now)
                )
                conn.commit()
                conn.close()
            logging.info(f"[CHARLIE SCORE DB SAVE] Success for {player_id}.")
        except sqlite3.Error as db_err:
            logging.error(f"[CHARLIE SCORE DB SAVE] Failed for {player_id}: {db_err}", exc_info=True)
            return jsonify(success=False, qualified=False, reason=None, error=f"Errore DB salvataggio punteggio: {db_err}"), 500
        except Exception as e:
            logging.error(f"[CHARLIE SCORE DB SAVE] Failed (General Error) for {player_id}: {e}", exc_info=True)
            return jsonify(success=False, qualified=False, reason=None, error=f"Errore generico salvataggio punteggio: {e}"), 500

        # 2. Aggiungi alla history ufficiale per leaderboard in-memory (se get_leaderboard la usa)
        backend.charlie_history.append((player_id, manual_score_minutes))
        logging.debug(f"Added manual score to backend.charlie_history (new size: {len(backend.charlie_timer_history)})")

        # 3. Controlla la qualifica
        is_qualified, reason = backend.check_qualification(manual_score_minutes, 'charlie')
        logging.info(f"[CHARLIE QUAL CHECK] Player: {player_id}, Score: {manual_score_minutes:.4f}, Qualified: {is_qualified}, Reason: {reason}")

        # 4. Ritorna il risultato al frontend
        return jsonify(
            success=True,
            qualified=is_qualified,
            reason=reason,
            # Passa indietro i dati necessari per il modal contatti
            player_id=player_id,
            player_name=player_name,
            recorded_score=manual_score_minutes, # Il punteggio manuale
            player_type='charlie'
        )

    except ValueError as ve:
        logging.error(f"Invalid time format in submit_charlie_score: {ve}. Data: {data}")
        return jsonify(success=False, qualified=False, reason=None, error=f"Formato tempo non valido: {ve}"), 400
    except Exception as e:
        logging.error(f"[CHARLIE SCORE SUBMIT] Failed processing score for {player_id}: {e}", exc_info=True)
        return jsonify(success=False, qualified=False, reason=None, error=f"Errore elaborazione punteggio: {e}"), 500

@app.route('/check_qualification_status', methods=['POST'])
def check_qualification_status():
    data = request.json
    player_id = data.get('player_id')
    score_str = data.get('recorded_score') # Riceve come stringa o numero? Assumiamo numero
    player_type = data.get('player_type')
    logging.debug(f"/check_qualification_status called with: score={score_str}, type={player_type}")


    if not all([player_id, score_str is not None, player_type]):
        return jsonify(qualified=False, reason=None, error="Dati mancanti per controllo qualifica."), 400

    try:
        score_float = float(score_str)
        # Chiama il metodo nel backend
        is_qualified, reason = backend.check_qualification(score_float, player_type)
        return jsonify(qualified=is_qualified, reason=reason)
    except ValueError:
         logging.error(f"Invalid score format received: {score_str}")
         return jsonify(qualified=False, reason=None, error="Punteggio non valido."), 400
    except Exception as e:
        logging.error(f"Error during qualification check API call: {e}", exc_info=True)
        return jsonify(qualified=False, reason=None, error="Errore interno durante verifica qualifica."), 500

@app.route('/save_contact_info', methods=['POST'])
def save_contact_info():
    data = request.json
    logging.debug(f"Received data for /save_contact_info: {data}")
    player_id = data.get('player_id')           # Es. GIALLO 01
    player_name = data.get('player_name')       # Es. Nome Squadra (se esiste) o ID
    first_name = data.get('first_name')       # Nome contatto
    last_name = data.get('last_name')         # Cognome contatto
    phone_number = data.get('phone_number')   # Telefono contatto
    score_minutes_str = data.get('score_minutes') # Punteggio che ha qualificato
    player_type = data.get('player_type')       # couple / single / couple2 / single2
    qualification_reason = data.get('qualification_reason') # best_today / top_3_overall

    if not all([player_id, player_name, first_name, last_name, phone_number,
                score_minutes_str is not None, player_type, qualification_reason]):
        logging.warning("Save contact info failed: Missing data.")
        return jsonify(success=False, message="Dati di contatto mancanti o incompleti."), 400

    try:
        score_float = float(score_minutes_str)
        score_formatted = backend.format_time(score_float)
        qualification_date = backend.get_current_time().strftime('%Y-%m-%d')
        timestamp = backend.get_current_time()

        # Normalize player_type to match the allowed values in the database
        normalized_player_type = player_type.lower()
        if normalized_player_type in ('couple2', 'single2'):
            normalized_player_type = normalized_player_type[:-1]  # Rimuove il "2"

        if normalized_player_type not in ('couple', 'single',        'charlie'):
            logging.error(f"Invalid player_type: {normalized_player_type}")
            return jsonify(success=False, message="Tipo giocatore non valido."), 400

        with sqlite_lock:  # Ensure the lock is used to serialize database access
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            logging.info(f"[CONTACT SAVE] ID={player_id}, Contact={first_name} {last_name}, Phone={phone_number}, Score={score_formatted}, Reason={qualification_reason}")
            execute_with_retry(
                cursor,
                """
                INSERT INTO qualified_players
                (player_id, player_name, first_name, last_name, phone_number, score_minutes, score_formatted, player_type, qualification_reason, qualification_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    player_id, player_name, first_name, last_name, phone_number,
                    score_float, score_formatted, normalized_player_type, qualification_reason,
                    qualification_date, timestamp
                )
            )
            conn.commit()
            conn.close()
        logging.info("[CONTACT SAVE] Success.")
        return jsonify(success=True, message="Dati di contatto salvati con successo!")

    except ValueError:
         logging.error(f"Invalid score format in save_contact_info: {score_minutes_str}")
         return jsonify(success=False, message="Punteggio non valido nel salvataggio contatti."), 400
    except Exception as e:
        logging.error(f"[CONTACT SAVE] Failed for {player_id}: {e}", exc_info=True)
        return jsonify(success=False, message=f"Errore DB durante salvataggio dati: {e}"), 500



@app.route('/skip_next_player_alfa_bravo', methods=['POST'])
def skip_next_player_alfa_bravo():
    player_id = request.json.get('id')
    if player_id:
        backend.skip_player(player_id)
        return jsonify(
            success=True,
            next_player_alfa_bravo_id=backend.next_player_alfa_bravo_id,
            next_player_alfa_bravo_name=backend.next_player_alfa_bravo_name
        )
    return jsonify(success=False, error="Player ID is required"), 400

@app.route('/skip_next_player_alfa_bravo2', methods=['POST'])
def skip_next_player_alfa_bravo2():
    player_id = request.json.get('id')
    if player_id:
        try:
            backend.skip_player2(player_id) # Chiama la funzione specifica per il set 2
            logging.info(f"Skipped player {player_id} from Alfa/Bravo 2 queue.") # Log
            # Restituisci il nuovo prossimo giocatore per il set 2
            return jsonify(
                success=True,
                next_player_alfa_bravo_id2=backend.next_player_alfa_bravo_id2,
                next_player_alfa_bravo_name2=backend.get_player_name(backend.next_player_alfa_bravo_id2)
            )
        except Exception as e:
             logging.error(f"Errore durante skip_player2 per ID {player_id}: {e}", exc_info=True) # Log con traceback
             return jsonify(success=False, error=f"Errore backend skip: {e}"), 500
    logging.warning("Richiesta skip_next_player_alfa_bravo2 senza ID.") # Log
    return jsonify(success=False, error="Player ID is required"), 400 

@app.route('/skip_charlie_player', methods=['POST'])
def skip_charlie_player():
    player_id = request.json.get('id')
    if player_id:
        backend.skip_charlie_player(player_id)
        return jsonify(
            success=True,
            next_player_charlie_id=backend.next_player_charlie_id,
            next_player_charlie_name=backend.next_player_charlie_name
        )
    return jsonify(success=False, error="Player ID is required"), 400



@app.route('/get_skipped', methods=['GET'])
def get_skipped():
    return jsonify({
        'couples': [{'id': c['id']} for c in backend.skipped_couples],
        'singles': [{'id': s['id']} for s in backend.skipped_singles],
        'couples2': [{'id': c2['id']} for c2 in backend.skipped_couples2],
        'singles2': [{'id': s2['id']} for s2 in backend.skipped_singles2],
        'charlie': [{'id': p['id']} for p in backend.skipped_charlie],
        'statico': [{'id': p['id']} for p in backend.skipped_statico]
    })


@app.route('/restore_skipped_as_next', methods=['POST'])
def restore_skipped():
    player_id = request.json.get('id')
    if player_id:
        backend.restore_skipped_as_next(player_id)
        return jsonify(success=True)
    return jsonify(success=False, error="Player ID is required"), 400


@app.route('/check_availability', methods=['GET'])
def check_availability():
    now = backend.get_current_time()

    alfa_available = (backend.current_player_alfa is None)
    bravo_available = (backend.current_player_bravo is None)

    return jsonify({
        'can_start_couple': alfa_available and bravo_available,
        'can_start_single': alfa_available,
        'alfa_status': 'Libera' if alfa_available else 'Occupata',
        'bravo_status': 'Libera' if bravo_available else 'Occupata'
    })

@app.route('/check_availability2', methods=['GET'])
def check_availability2():
    now = backend.get_current_time()

    alfa2_available = (backend.current_player_alfa2 is None)
    bravo2_available = (backend.current_player_bravo2 is None)      

    return jsonify({
        'can_start_couple2': alfa2_available and bravo2_available,
        'can_start_single2': alfa2_available,
        'alfa2_status': 'Libera' if alfa2_available else 'Occupata',
        'bravo2_status': 'Libera' if bravo2_available else 'Occupata'
    })

@app.route('/start_game', methods=['POST'])
def start_game_route():
    try:
        is_couple = request.json.get('is_couple', False)
        backend.start_game(is_couple)
        return jsonify(success=True)
    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400
    except Exception as e:
        return jsonify(success=False, error="An unexpected error occurred."), 500

@app.route('/start_game2', methods=['POST'])
def start_game_route2():
    try:
        is_couple = request.json.get('is_couple', False)
        backend.start_game2(is_couple)
        return jsonify(success=True)    
    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400
    except Exception as e:
        return jsonify(success=False, error="An unexpected error occurred."), 500


@app.route('/get_status', methods=['GET'])
def get_status():
    now = backend.get_current_time()
    charlie_remaining = max(0, (backend.CHARLIE_next_available - now).total_seconds() / 60)
    charlie_status = 'Occupata' if charlie_remaining > 0 else 'Libera'

    return jsonify({
        'charlie_status': charlie_status,
        'charlie_remaining': f"{int(charlie_remaining)}min" if charlie_remaining > 0 else "0min"
    })


@app.route('/delete_player', methods=['POST'])
def delete_player():
    player_id = request.json.get('id')
    if player_id:
        backend.delete_player(player_id)
        return jsonify(success=True)
    return jsonify(success=False, error="Player ID is required"), 400


def execute_with_retry(cursor, query, params=(), retries=5, delay=0.1):
    """
    Executes a database query with retry logic to handle 'database is locked' errors.
    """
    for attempt in range(retries):
        try:
            cursor.execute(query, params)
            return
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                if attempt < retries - 1:
                    time.sleep(delay)  # Wait before retrying
                else:
                    raise
            else:
                raise


if __name__ == '__main__':
    app.secret_key = os.urandom(12)

    log = logging.getLogger('werkzeug')
    # log.setLevel(logging.ERROR)
    # Esegui Flask con il riavvio automatico disabilitato
    app.run(host='0.0.0.0', port=2000, debug=True, use_reloader=False)
    print('localost:2000')
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Indirizzo IP: http://{ip_address}")
