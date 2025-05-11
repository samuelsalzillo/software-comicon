# Aggiungi questa funzione per caricare gli skippati all'avvio
import os
import sqlite3


def load_skipped_from_db(backend):
    try:
        conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
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

