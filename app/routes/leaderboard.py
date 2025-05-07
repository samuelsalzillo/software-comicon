# app/routes/leaderboard.py

from flask import Blueprint, jsonify
import sqlite3
import logging
from app.db.init_db import SQLITE_DB_PATH
from threading import Lock

leaderboard_bp = Blueprint('leaderboard', __name__)
sqlite_lock = Lock()

@leaderboard_bp.route('/leaderboard/top3', methods=['GET'])
def get_top3_leaderboard():
    top3_data = {
        'couples': [],
        'singles': [],
        'charlie': []
    }
    player_types = ['couple', 'single', 'charlie']

    try:
        with sqlite_lock:
            conn = sqlite3.connect(SQLITE_DB_PATH, timeout=10)
            cursor = conn.cursor()

            for p_type in player_types:
                cursor.execute("""
                    SELECT player_id, first_name, last_name, score_formatted, score_minutes
                    FROM qualified_players
                    WHERE player_type = ?
                    ORDER BY score_minutes ASC
                    LIMIT 3
                """, (p_type,))
                rows = cursor.fetchall()

                for rank, row in enumerate(rows, start=1):
                    short_id, first_name, last_name, score_fmt, _ = row
                    entry = {
                        "rank": rank,
                        "id": short_id,
                        "name": f"{first_name} {last_name}",
                        "score": score_fmt
                    }
                    top3_data[p_type + 's'].append(entry)

            conn.close()

        return jsonify(top3_data)

    except sqlite3.Error as db_err:
        logging.error(f"Errore Database in /leaderboard/top3: {db_err}", exc_info=True)
        return jsonify(error=f"Errore database: {db_err}"), 500
    except Exception as e:
        logging.error(f"Errore generico in /leaderboard/top3: {e}", exc_info=True)
        return jsonify(error="Errore interno del server"), 500
