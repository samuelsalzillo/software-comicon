# Funzione per caricare le code dal database all'avvio
import os
import sqlite3


def load_queues_from_db(backend):
    try:
        conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
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
