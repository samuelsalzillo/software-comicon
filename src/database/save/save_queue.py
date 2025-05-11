import datetime
import logging
import os
import sqlite3
import threading
import time
from ...utils.model import get_game_backend
from ...utils import timer

def save_queues_to_db():
    backend = get_game_backend()
    is_alive = True
    while is_alive:
        try:
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
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
        timer.timer_for_thread(10,"save_queue")  # Salva ogni 10 secondi