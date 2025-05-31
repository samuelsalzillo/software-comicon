import logging
import os
import sqlite3

from flask import jsonify

from ...utils.database import get_lock


def find_by_id_and_today(player_id):
    sqlite_lock = get_lock()
    try:
        with sqlite_lock:  # Usa il lock per l'accesso al DB
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'), timeout=10)
            cursor = conn.cursor()
            cursor.execute("""
                                                SELECT *
                                                FROM treasure_hunt
                                                where chiave_esterna = ?
                                                """, player_id)
            rows = cursor.fetchall()
            if rows:
                return rows[0]
            return None
    except sqlite3.Error as db_err:
        logging.error(f"Errore Database in /leaderboard/top3: {db_err}", exc_info=True)
        return jsonify(error=f"Errore database: {db_err}"), 500

    except Exception as e:
        logging.error(f"Errore generico in /leaderboard/top3: {e}", exc_info=True)
        return jsonify(error="Errore interno del server"), 500
