import logging

from flask import Blueprint, request, jsonify
from ...utils.model import get_game_backend, set_game_backend
from ...utils import date
from ...service import service_player

player = Blueprint('player',__name__)

@player.route('/add_couple', methods=['POST'])
def add_couple():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id >100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    couple_id = f"{name.upper()} {int(id):03d}"
    get_game_backend().add_couple(couple_id, name)
    return jsonify(success=True)


@player.route('/add_single', methods=['POST'])
def add_single():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id >100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    single_id = f"{name.upper()} {int(id):03d}"
    get_game_backend().add_single(single_id, name)
    return jsonify(success=True)


@player.route('/add_couple2', methods=['POST'])
def add_couple2():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id >100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    couple2_id = f"{name.upper()} {int(id):03d}"
    get_game_backend().add_couple2(couple2_id, name)
    return jsonify(success=True)


@player.route('/add_single2', methods=['POST'])
def add_single2():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id >100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    single2_id = f"{name.upper()} {int(id):03d}"
    get_game_backend().add_single2(single2_id, name)
    return jsonify(success=True)


@player.route('/add_charlie', methods=['POST'])
def add_charlie():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id >100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    charlie_id = f"{name.upper()} {int(id):03d}"
    get_game_backend().add_charlie_player(charlie_id, name)
    return jsonify(success=True)


@player.route('/add_charlie_player', methods=['POST'])
def add_charlie_player():
    backend = get_game_backend()
    name = request.json.get('name')
    id = request.json.get('id')
    if not name or not id:
        return jsonify(success=False, error="Name and id are required"), 400
    if id >100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    player_id = f"{name.upper()} {int(id):03d}"
    backend.add_charlie_player(player_id, name)

    if not backend.next_player_charlie_id and backend.queue_charlie:
        backend.next_player_charlie_id = backend.queue_charlie[0]['id']
        backend.next_player_charlie_name = backend.get_player_name(backend.next_player_charlie_id)
        backend.next_player_charlie_locked = True
    set_game_backend(backend)
    return jsonify(success=True, player_id=player_id, name=name)

@player.route('/simulate', methods=['GET'])
def simulate():
    return service_player.simulate_player()


@player.route('/button_press', methods=['POST'])
def button_press():
   return service_player.service_button_press()


@player.route('/save_contact_info', methods=['POST'])
def save_contact_info():
    return service_player.service_save_contact()

@player.route('/skip_next_player_alfa_bravo', methods=['POST'])
def skip_next_player_alfa_bravo():
    backend = get_game_backend()
    player_id = request.json.get('id')
    if player_id:
        backend.skip_player(player_id)
        set_game_backend(backend)
        return jsonify(
            success=True,
            next_player_alfa_bravo_id=backend.next_player_alfa_bravo_id,
            next_player_alfa_bravo_name=backend.next_player_alfa_bravo_name
        )
    return jsonify(success=False, error="Player ID is required"), 400

@player.route('/skip_next_player_alfa_bravo2', methods=['POST'])
def skip_next_player_alfa_bravo2():
    backend = get_game_backend()
    player_id = request.json.get('id')
    if player_id:
        try:
            backend.skip_player2(player_id) # Chiama la funzione specifica per il set 2
            logging.info(f"Skipped player {player_id} from Alfa/Bravo 2 queue.") # Log
            # Restituisci il nuovo prossimo giocatore per il set 2
            set_game_backend(backend)
            return jsonify(
                success=True,
                next_player_alfa_bravo_id2=backend.next_player_alfa_bravo_id2,
                next_player_alfa_bravo_name2=backend.get_player_name(backend.next_player_alfa_bravo_id2)
            )
        except Exception as e:
             logging.error(f"Errore durante skip_player2 per ID {player_id}: {e}", exc_info=True) # Log con traceback
             return jsonify(success=False, error=f"Errore backend skip: {e}"), 500
    logging.warning("Richiesta skip_next_player_alfa_bravo2 senza ID.") # Log
    return jsonify(success=False, error="Player ID is required"), 400

@player.route('/skip_charlie_player', methods=['POST'])
def skip_charlie_player():
    backend = get_game_backend()
    player_id = request.json.get('id')
    if player_id:
        backend.skip_charlie_player(player_id)
        set_game_backend(backend)
        return jsonify(
            success=True,
            next_player_charlie_id=backend.next_player_charlie_id,
            next_player_charlie_name=backend.next_player_charlie_name
        )
    return jsonify(success=False, error="Player ID is required"), 400



@player.route('/get_skipped', methods=['GET'])
def get_skipped():
    return service_player.get_skipped()


@player.route('/restore_skipped_as_next', methods=['POST'])
def restore_skipped():
    backend = get_game_backend()
    player_id = request.json.get('id')
    if player_id:
        backend.restore_skipped_as_next(player_id)
        set_game_backend(backend)
        return jsonify(success=True)
    return jsonify(success=False, error="Player ID is required"), 400


@player.route('/check_availability', methods=['GET'])
def check_availability():
    backend = get_game_backend()

    alfa_available = (backend.current_player_alfa is None)
    bravo_available = (backend.current_player_bravo is None)
    set_game_backend(backend)
    return jsonify({
        'can_start_couple': alfa_available and bravo_available,
        'can_start_single': alfa_available,
        'alfa_status': 'Libera' if alfa_available else 'Occupata',
        'bravo_status': 'Libera' if bravo_available else 'Occupata'
    })

@player.route('/check_availability2', methods=['GET'])
def check_availability2():
    backend = get_game_backend()

    alfa2_available = (backend.current_player_alfa2 is None)
    bravo2_available = (backend.current_player_bravo2 is None)
    set_game_backend(backend)
    return jsonify({
        'can_start_couple2': alfa2_available and bravo2_available,
        'can_start_single2': alfa2_available,
        'alfa2_status': 'Libera' if alfa2_available else 'Occupata',
        'bravo2_status': 'Libera' if bravo2_available else 'Occupata'
    })

@player.route('/start_game', methods=['POST'])
def start_game_route():
    backend = get_game_backend()
    try:
        is_couple = request.json.get('is_couple', False)
        backend.start_game(is_couple)
        set_game_backend(backend)
        return jsonify(success=True)
    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400
    except Exception as e:
        return jsonify(success=False, error="An unexpected error occurred."), 500

@player.route('/start_game2', methods=['POST'])
def start_game_route2():
    backend = get_game_backend()
    try:
        is_couple = request.json.get('is_couple', False)
        backend.start_game2(is_couple)
        set_game_backend(backend)
        return jsonify(success=True)
    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400
    except Exception as e:
        return jsonify(success=False, error="An unexpected error occurred."), 500


@player.route('/get_status', methods=['GET'])
def get_status():
    backend = get_game_backend()
    now = date.get_current_time()
    charlie_remaining = max(0, (backend.CHARLIE_next_available - now).total_seconds() / 60)
    charlie_status = 'Occupata' if charlie_remaining > 0 else 'Libera'
    set_game_backend(backend)
    return jsonify({
        'charlie_status': charlie_status,
        'charlie_remaining': f"{int(charlie_remaining)}min" if charlie_remaining > 0 else "0min"
    })

@player.route('/delete_player', methods=['POST'])
def delete_player():
    return service_player.service_delete_player()

@player.route('/add_statico', methods=['POST'])
def add_statico():
    return service_player.service_add_statico()

@player.route('/skip_statico_player', methods=['POST'])
def skip_statico_player():
    return service_player.service_skip_statico_player()