# app/routes/button_actions.py

from flask import Blueprint, request, jsonify
from main import GameBackend
from datetime import datetime

buttons_bp = Blueprint('buttons', __name__)
backend = GameBackend()

@buttons_bp.route('/button_press', methods=['POST'])
def button_press():
    button = request.json.get('button')
    now = backend.get_current_time()

    # Solo un esempio semplificato per i pulsanti più importanti
    if button == 'first_start':
        if not backend.queue_couples:
            return jsonify(success=False, error="Coda vuota")
        backend.start_game(is_couple=True)
        return jsonify(success=True)

    elif button == 'second_start':
        if not backend.queue_singles:
            return jsonify(success=False, error="Coda vuota")
        backend.start_game(is_couple=False)
        return jsonify(success=True)

    elif button == 'third':
        try:
            backend.button_third_pressed()
            return jsonify(success=True)
        except Exception as e:
            return jsonify(success=False, error=str(e))

    elif button == 'charlie_start':
        if not backend.queue_charlie:
            return jsonify(success=False, error="Coda Charlie vuota")
        backend.start_charlie_game()
        return jsonify(success=True, current_player_charlie=backend.current_player_charlie)

    elif button == 'charlie_stop':
        player_info = backend.current_player_charlie
        if player_info and player_info.get('id'):
            player_id = player_info['id']
            start_time = backend.player_start_times.get(player_id)
            if start_time:
                duration = (now - start_time).total_seconds() / 60.0
                backend.record_charlie_game(duration)
                return jsonify(success=True)
        return jsonify(success=False, error="Nessun giocatore Charlie attivo")

    return jsonify(success=False, error="Comando non gestito")
