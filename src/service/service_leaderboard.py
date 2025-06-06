"""
Recupera i primi 3 giocatori qualificati per tipo (couple, single, charlie)
basandosi sul tempo più basso registrato nella tabella qualified_players.
(Assume che la colonna player_id contenga l'ID CORTO: "COLORE NNN")
"""
import logging
import os
import sqlite3

from bottle import response

from ..utils.database import get_lock
from ..utils.date import convert_string_date_datetime_into_date, format_time_into_mmss, \
    converti_float_mmss_in_secondi_totali
from ..database.select.qualified_players import find_by_type_id_player, find_by_id_player
from ..database.save.save_qualified_players import update_score_formatted_and_score_minutes
from flask import jsonify
from .service_treasure_hunt import get_all_treasure_hunt
from ..database.save.save_scoring import update_score_formatted
from ..utils.model import get_game_backend, set_game_backend


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
                cursor.execute(f"""
                    SELECT player_id, first_name, last_name, score_formatted, score_minutes
                    FROM qualified_players
                    WHERE player_type = ?
                    {"AND treasure_hunt_updated is not null" if (os.environ.get("TREASURE_HUNT_ACTIVE") and (p_type == 'couple' or p_type == 'single')) else ""}
                    AND qualification_reason is not 'Non qualificato'
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

def sync_new_date():
    metadata = get_all_treasure_hunt()
    backend = get_game_backend()
    player_types = ['couple', 'single', 'charlie']  # Tipi da cercare
    try:
        for data in metadata:
            for player_type in player_types:
                row = find_by_type_id_player(player_type,data.id_player)
                if row:
                    player_id, player_name, score = row
                    if not find_by_id_player(player_id):
                        differenza_in_secondi = (data.timestamp_fine - data.timestamp_inizio).total_seconds()
                        if data.qr_code_founded != data.qr_code:
                            differenza_in_secondi = differenza_in_secondi + 0 # todo penalita
                        score_minutes = (differenza_in_secondi + converti_float_mmss_in_secondi_totali(score)) / 60
                        score_formatted = format_time_into_mmss(score_minutes)
                        if data.qr_code_founded != data.qr_code:
                            is_qualified, reason = False,"Non qualificato"
                        else:
                            is_qualified, reason=  backend.check_qualification(score_minutes,player_type)
                        update_score_formatted_and_score_minutes(player_id,player_name,player_type,data,score_formatted,score_minutes,reason if is_qualified else "Non qualificato")
                        update_score_formatted(backend,player_id,score_minutes)
                    if not response:
                        logging.error("problem")
                    logging.debug(f"Found {len(row)} and update results for {player_type}")
        return jsonify(error="Operazione completata con successo"), 200


    except Exception as e:
        logging.error(f"Errore generico in /leaderboard/top3: {e}", exc_info=True)
        return jsonify(error="Errore interno del server"), 500
