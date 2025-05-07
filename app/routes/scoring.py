# app/routes/scoring.py

from flask import Blueprint, jsonify, render_template, request
from main import GameBackend

scoring_bp = Blueprint('scoring', __name__)
backend = GameBackend()

@scoring_bp.route('/scoring')
def scoring():
    leaderboard = backend.get_leaderboard()
    return render_template('scoring.html', leaderboard=leaderboard)

@scoring_bp.route('/get_scores', methods=['GET'])
def get_scores():
    leaderboard = backend.get_leaderboard()
    return jsonify(leaderboard)

@scoring_bp.route('/submit_combined_score', methods=['POST'])
def submit_combined_score():
    data = request.json
    player_id = data.get('player_id')
    player_name = data.get('player_name')
    player_type = data.get('player_type')
    timer_duration_str = data.get('timer_duration_minutes')
    official_score_str = data.get('official_score_minutes')

    if not all([player_id, player_name, player_type, timer_duration_str, official_score_str]):
        return jsonify(success=False, qualified=False, reason=None, error="Dati punteggio finale mancanti."), 400

    try:
        timer_duration = float(timer_duration_str)
        official_score = float(official_score_str)
        backend.record_score(player_id, player_name, player_type, timer_duration, official_score)
        is_qualified, reason = backend.check_qualification(official_score, player_type)

        return jsonify(
            success=True,
            qualified=is_qualified,
            reason=reason,
            player_id=player_id,
            player_name=player_name,
            recorded_score=official_score,
            player_type=player_type
        )
    except Exception as e:
        return jsonify(success=False, qualified=False, reason=None, error=str(e)), 500


@scoring_bp.route('/submit_charlie_score', methods=['POST'])
def submit_charlie_score():
    data = request.json
    player_id = data.get('player_id')
    player_name = data.get('player_name')
    minutes_str = data.get('minutes')
    seconds_str = data.get('seconds')
    milliseconds_str = data.get('milliseconds')

    if not all([player_id, player_name, minutes_str, seconds_str, milliseconds_str]):
        return jsonify(success=False, qualified=False, reason=None, error="Dati punteggio mancanti."), 400

    try:
        minutes = int(minutes_str)
        seconds = int(seconds_str)
        milliseconds = int(milliseconds_str)
        total_score = minutes + seconds / 60 + milliseconds / 60000
        backend.record_charlie_score(player_id, player_name, total_score)
        is_qualified, reason = backend.check_qualification(total_score, 'charlie')

        return jsonify(success=True, qualified=is_qualified, reason=reason)
    except Exception as e:
        return jsonify(success=False, qualified=False, reason=None, error=str(e)), 500
