from flask import render_template, Blueprint

from ...utils.model import get_game_backend
leaderboard = Blueprint('leaderboard', __name__, url_prefix='')

@leaderboard.route('/scoring')
def get_scoring(): # messo un get
    scoring = get_game_backend().get_leaderboard()
    return render_template('scoring.html', leaderboard=scoring)