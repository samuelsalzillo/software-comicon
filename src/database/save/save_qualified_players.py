import logging
import os
import sqlite3

from flask import jsonify

from ...utils.database import get_lock
from ...utils.date import get_current_time
from ...database.select.qualified_players import find_by_id_player

def update_score_formatted_and_score_minutes(player_id,player_name,player_type,data,score_formatted,score_minutes):
    sqlite_lock = get_lock()
    try:

        with sqlite_lock:  # Usa il lock per l'accesso al DB
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'), timeout=10)
            cursor = conn.cursor()
            cursor.execute("""
                                INSERT INTO qualified_players
                                (player_id, player_name, first_name, last_name, phone_number, score_minutes, score_formatted, player_type, qualification_reason, qualification_date, treasure_hunt_updated, created_at)
                                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
""", (player_id, player_name,data.nome,data.cognome,data.telefono,score_minutes,score_formatted,player_type,"",data.timestamp_fine,"AGGIORNATO",get_current_time()))
            conn.commit()
            conn.close()
        return True
    except sqlite3.Error as db_err:
        logging.error(f"Errore Database in /leaderboard/top3: {db_err}", exc_info=True)
        return jsonify(error=f"Errore database: {db_err}"), 500

    except Exception as e:
        logging.error(f"Errore generico in /leaderboard/top3: {e}", exc_info=True)
        return jsonify(error="Errore interno del server"), 500