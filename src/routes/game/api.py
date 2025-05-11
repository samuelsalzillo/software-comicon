from flask import Blueprint, jsonify
from ...utils.model import get_game_backend, set_game_backend
from ...utils import date

game = Blueprint('game',__name__,url_prefix='')

@game.route('/statico_start', methods=['POST'])
def statico_start():
    backend = get_game_backend()
    if not backend.queue_statico:
        return jsonify(success=False, error="La coda di Statico è vuota. Non è possibile avviare il gioco.")
    backend.start_statico_game()
    set_game_backend(backend)
    return jsonify(success=True, current_player_delta=backend.current_player_delta,
                  current_player_echo=backend.current_player_echo)

@game.route('/statico_stop', methods=['POST'])
def statico_stop():
    backend = get_game_backend()
    if backend.current_player_delta or backend.current_player_echo:
        player_id = backend.current_player_delta['id'] if backend.current_player_delta else backend.current_player_echo['id']
        now = date.get_current_time()
        if player_id and player_id in backend.player_start_times:
            backend.record_statico_game((now - backend.player_start_times[player_id]).total_seconds() / 60)
            backend.current_player_delta = None
            backend.current_player_echo = None
            set_game_backend(backend)
            return jsonify(success=True)
        else:
            return jsonify(success=False, error="Errore nel recupero del tempo di inizio del giocatore Statico.")
    return jsonify(success=False, error="Nessun giocatore Statico in pista.")
