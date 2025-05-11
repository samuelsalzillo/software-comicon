# --- NUOVA ROUTE PER LEADERBOARD TOP 3 QUALIFICATI (con ID Corto nel DB) ---
import logging

from flask import jsonify, request, Blueprint
from ...service.service_leaderboard import get_top3_leaderboard as service_get_top3
from ...utils.model import get_game_backend, set_game_backend

leaderboard_api = Blueprint('leaderboard_api', __name__, url_prefix='')

@leaderboard_api.route('/leaderboard/top3', methods=['GET'])
def get_top3_leaderboard():
    return service_get_top3()

@leaderboard_api.route('/get_scores', methods=['GET'])
def get_scores():
    scores = get_game_backend().get_leaderboard()
    return jsonify(scores)

@leaderboard_api.route('/check_qualification_status', methods=['POST'])
def check_qualification_status():
    backend = get_game_backend()
    data = request.json
    player_id = data.get('player_id')
    score_str = data.get('recorded_score') # Riceve come stringa o numero? Assumiamo numero
    player_type = data.get('player_type')
    logging.debug(f"/check_qualification_status called with: score={score_str}, type={player_type}")
    if not all([player_id, score_str is not None, player_type]):
        return jsonify(qualified=False, reason=None, error="Dati mancanti per controllo qualifica."), 400

    try:
        score_float = float(score_str)
        # Chiama il metodo nel backend
        is_qualified, reason = backend.check_qualification(score_float, player_type)
        set_game_backend(backend)
        return jsonify(qualified=is_qualified, reason=reason)
    except ValueError:
         logging.error(f"Invalid score format received: {score_str}")
         return jsonify(qualified=False, reason=None, error="Punteggio non valido."), 400
    except Exception as e:
        logging.error(f"Error during qualification check API call: {e}", exc_info=True)
        return jsonify(qualified=False, reason=None, error="Errore interno durante verifica qualifica."), 500