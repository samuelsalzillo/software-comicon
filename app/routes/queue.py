# app/routes/queue.py

from flask import Blueprint, jsonify, render_template, request
from main import GameBackend

queue_bp = Blueprint('queue', __name__)
backend = GameBackend()

@queue_bp.route('/queue')
def queue():
    return render_template('queue.html')

@queue_bp.route('/add_couple', methods=['POST'])
def add_couple():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id > 100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    couple_id = f"{name.upper()} {int(id):03d}"
    backend.add_couple(couple_id, name)
    return jsonify(success=True)

@queue_bp.route('/add_single', methods=['POST'])
def add_single():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id > 100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    single_id = f"{name.upper()} {int(id):03d}"
    backend.add_single(single_id, name)
    return jsonify(success=True)

@queue_bp.route('/add_couple2', methods=['POST'])
def add_couple2():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id > 100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    couple2_id = f"{name.upper()} {int(id):03d}"
    backend.add_couple2(couple2_id, name)
    return jsonify(success=True)

@queue_bp.route('/add_single2', methods=['POST'])
def add_single2():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id > 100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    single2_id = f"{name.upper()} {int(id):03d}"
    backend.add_single2(single2_id, name)
    return jsonify(success=True)

@queue_bp.route('/add_charlie', methods=['POST'])
def add_charlie():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id > 100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    charlie_id = f"{name.upper()} {int(id):03d}"
    backend.add_charlie_player(charlie_id, name)
    return jsonify(success=True)

@queue_bp.route('/add_statico', methods=['POST'])
def add_statico():
    id = request.json.get('id')
    name = request.json.get('name')
    if not id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if id > 100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    statico_id = f"{name.upper()} {int(id):03d}"
    backend.add_statico_player(statico_id, name)
    return jsonify(success=True)

@queue_bp.route('/skip_statico_player', methods=['POST'])
def skip_statico_player():
    player_id = request.json.get('id')
    if player_id:
        backend.skip_statico_player(player_id)
        return jsonify(
            success=True,
            next_player_statico_id=backend.next_player_statico_id,
            next_player_statico_name=backend.next_player_statico_name
        )
    return jsonify(success=False, error="Player ID is required"), 400
