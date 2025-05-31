import datetime
import logging
import os
import sqlite3
from ...utils.model import get_game_backend
from . import save_scoring
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

            refresh_queues([("couple",backend.queue_couples),("single",backend.queue_singles),("couple",backend.queue_couples2),("single",backend.queue_singles2),("charlie",backend.queue_charlie),("statico",backend.queue_statico)],backend,conn)

            # Salva gli score
            cursor.execute("DELETE FROM scoring")
            conn.commit()

            save_scoring.refresh_scoring([("couple",backend.couple_history_total),("single",backend.single_history),("couple",backend.couple_history_total2),("single",backend.single_history2),("charlie",backend.charlie_history),("statico",backend.statico_history)],backend,cursor)

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

def refresh_queues(queue_list, backend, cursor):
    # Salva le code
    for queue in queue_list:
        if queue[1] and len(queue) > 0:
            for single_queue in queue[1]:
                cursor.execute(
                    "INSERT INTO queues (player_type, player_id, player_name, arrival_time) VALUES (?, ?, ?, ?) ",
                    (queue[0], single_queue['id'], backend.get_player_name(single_queue['id']), single_queue['arrival'])
                )