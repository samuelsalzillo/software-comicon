"""
Recupera i primi 3 giocatori qualificati per tipo (couple, single, charlie)
basandosi sul tempo più basso registrato nella tabella qualified_players.
(Assume che la colonna player_id contenga l'ID CORTO: "COLORE NNN")
"""
import logging
import os
import sqlite3
from ..utils.database import get_lock
from flask import jsonify


def get_top3_leaderboard():
    top3_data = {
        'couples': [],
        'singles': [],
        'charlie': []
    }
    player_types = ['couple', 'single', 'charlie'] # Tipi da cercare
    sqlite_lock = get_lock()
    try:
        with sqlite_lock: # Usa il lock per l'accesso al DB
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'), timeout=10)
            cursor = conn.cursor()

            for p_type in player_types:
                logging.debug(f"Querying top 3 for type: {p_type} (using short ID from DB)")
                # --- Query che assume player_id è l'ID CORTO ---
                cursor.execute("""
                    SELECT player_id, first_name, last_name, score_formatted, score_minutes
                    FROM qualified_players
                    WHERE player_type = ?
                    ORDER BY score_minutes ASC
                    LIMIT 3
                """, (p_type,))
                rows = cursor.fetchall()
                logging.debug(f"Found {len(rows)} results for {p_type}")

                rank = 1
                for row in rows:
                    # Legge direttamente l'ID corto dal DB
                    short_player_id, first_name, last_name, score_formatted, score_minutes = row
                    player_entry = {
                        "rank": rank,
                        "id": short_player_id, # Usa direttamente l'ID letto
                        "name": f"{first_name} {last_name}", # Nome del contatto
                        "score": score_formatted,
                        # "score_minutes": score_minutes # Opzionale: se serve al frontend
                    }
                    # Aggiunge alla lista corretta (couples, singles, charlies)
                    if p_type in top3_data:
                        top3_data[p_type].append(player_entry)
                    elif p_type + 's' in top3_data: # Gestisce plurale automatico
                         top3_data[p_type + 's'].append(player_entry)
                    rank += 1

            conn.close() # Chiudi connessione dopo tutte le query

        return jsonify(top3_data)

    except sqlite3.Error as db_err:
        logging.error(f"Errore Database in /leaderboard/top3: {db_err}", exc_info=True)
        return jsonify(error=f"Errore database: {db_err}"), 500
    except Exception as e:
        logging.error(f"Errore generico in /leaderboard/top3: {e}", exc_info=True)
        return jsonify(error="Errore interno del server"), 500