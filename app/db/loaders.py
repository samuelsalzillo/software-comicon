# app/db/loaders.py

import sqlite3
import logging
import datetime
import time
import os
from threading import Lock, Thread
from threading import Timer
import shutil
import glob

from datetime import datetime as dt

from app.db.init_db import SQLITE_DB_PATH
from main import GameBackend

sqlite_lock = Lock()
backend = GameBackend()

def load_mid_times_from_db():
    with sqlite_lock:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT couple_type, mid_duration_minutes FROM mid_times ORDER BY recorded_at ASC
        """)
        rows = cursor.fetchall()
        conn.close()

    backend.couple_history_mid.clear()
    backend.couple_history_mid2.clear()

    for couple_type, duration in rows:
        if couple_type == 'couple1':
            backend.couple_history_mid.append(float(duration))
        elif couple_type == 'couple2':
            backend.couple_history_mid2.append(float(duration))

def load_average_times_from_db():
    with sqlite_lock:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT player_type, timer_duration_minutes FROM average_times ORDER BY recorded_at ASC
        """)
        rows = cursor.fetchall()
        conn.close()

    backend.couple_timer_history.clear()
    backend.single_timer_history.clear()
    backend.single_timer_history2.clear()

    for player_type, duration in rows:
        duration = float(duration)
        if player_type in ('couple', 'couple2'):
            backend.couple_timer_history.append(duration)
        elif player_type == 'single':
            backend.single_timer_history.append(duration)
        elif player_type == 'single2':
            backend.single_timer_history2.append(duration)

    backend.update_averages()

def load_skipped_from_db():
    with sqlite_lock:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT player_type, player_id, player_name FROM skipped_players ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

    backend.skipped_couples.clear()
    backend.skipped_singles.clear()
    backend.skipped_couples2.clear()
    backend.skipped_singles2.clear()
    backend.skipped_charlie.clear()
    backend.skipped_statico.clear()

    for player_type, player_id, player_name in rows:
        player = {'id': player_id, 'name': player_name}
        getattr(backend, f'skipped_{player_type}s').append(player)

def load_scores_from_db():
    with sqlite_lock:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT player_type, player_id, score FROM scoring
            WHERE score IS NOT NULL ORDER BY created_at ASC
        """)
        rows = cursor.fetchall()
        conn.close()

    backend.couple_history_total.clear()
    backend.single_history.clear()
    backend.couple_history_total2.clear()
    backend.single_history2.clear()
    backend.charlie_history.clear()
    backend.statico_history.clear()

    for player_type, player_id, score in rows:
        entry = (player_id, float(score))
        if player_type == 'couple':
            backend.couple_history_total.append(entry)
        elif player_type == 'single':
            backend.single_history.append(entry)
        elif player_type == 'couple2':
            backend.couple_history_total2.append(entry)
        elif player_type == 'single2':
            backend.single_history2.append(entry)
        elif player_type == 'charlie':
            backend.charlie_history.append(entry)
        elif player_type == 'statico':
            backend.statico_history.append(entry)

    backend.update_averages()

def load_queues_from_db():
    with sqlite_lock:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT player_type, player_id, player_name, arrival_time FROM queues ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()

    backend.queue_couples.clear()
    backend.queue_singles.clear()
    backend.queue_couples2.clear()
    backend.queue_singles2.clear()
    backend.queue_charlie.clear()
    backend.queue_statico.clear()

    for player_type, player_id, player_name, arrival_time in rows:
        queue_name = f'queue_{player_type}s' if player_type not in ['charlie', 'statico'] else f'queue_{player_type}'
        getattr(backend, queue_name).append({'id': player_id, 'arrival': arrival_time})
        backend.player_names[player_id] = player_name

def load_charlie_timer_history_from_db():
    with sqlite_lock:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timer_duration_minutes FROM charlie_timer_scores ORDER BY recorded_at ASC
        """)
        rows = cursor.fetchall()
        conn.close()

    backend.charlie_timer_history.clear()

    for (duration,) in rows:
        try:
            backend.charlie_timer_history.append(float(duration))
        except Exception:
            pass

    backend.update_averages()

def save_queues_to_db():
    while True:
        try:
            with sqlite_lock:
                conn = sqlite3.connect(SQLITE_DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM queues")
                for queue_attr, player_type in [
                    ('queue_couples', 'couple'),
                    ('queue_singles', 'single'),
                    ('queue_couples2', 'couple2'),
                    ('queue_singles2', 'single2'),
                    ('queue_charlie', 'charlie'),
                    ('queue_statico', 'statico'),
                ]:
                    for player in getattr(backend, queue_attr):
                        cursor.execute(
                            "INSERT INTO queues (player_type, player_id, player_name, arrival_time) VALUES (?, ?, ?, ?)",
                            (player_type, player['id'], backend.get_player_name(player['id']), player['arrival'])
                        )
                conn.commit()
                conn.close()
        except Exception as e:
            logging.error(f"[SAVE QUEUES] Errore salvataggio: {e}")
        time.sleep(10)

def start_save_thread():
    thread = Thread(target=save_queues_to_db, daemon=True)
    thread.start()
