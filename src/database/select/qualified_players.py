import datetime
import logging
import os
import sqlite3

from flask import jsonify

from ...utils.database import get_lock
from ...utils.date import get_current_time


def find_by_type_id_player(player_type, id_player):
    sqlite_lock = get_lock()
    try:
        with sqlite_lock:  # Usa il lock per l'accesso al DB
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'), timeout=10)
            cursor = conn.cursor()
            cursor.execute("""
                                                SELECT player_id, player_name, score
                                                FROM scoring
                                                WHERE player_type = ?
                                                AND player_id = ?
                                                order by id desc
                                            """, (player_type, id_player,))
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

def find_by_id_player(id_player):
    sqlite_lock = get_lock()
    try:
        with sqlite_lock:  # Usa il lock per l'accesso al DB
            today_date_str = get_current_time().strftime('%Y-%m-%d')
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'), timeout=10)
            cursor = conn.cursor()
            cursor.execute("""
                                                SELECT player_id
                                                FROM qualified_players
                                                WHERE player_id = ?
                                                AND SUBSTR(created_at, 1, 10) = ?
                                            """, (id_player,today_date_str))
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
