from .backup.api import backup
from .game.api import game
from .leaderboard.api import leaderboard_api
from .player.api import player
from .submit.api import submit
from .treasure_hunt.api import treasure_hunt

from .controls.views import controls
from .dashboard.views import dashboard
from .leaderboard.views import leaderboard
from .keypad.views import keypad

def register_root(app):
    app.register_blueprint(backup)
    app.register_blueprint(leaderboard_api)
    app.register_blueprint(game)
    app.register_blueprint(player)
    app.register_blueprint(submit)
    app.register_blueprint(treasure_hunt)

    app.register_blueprint(controls)
    app.register_blueprint(dashboard)
    app.register_blueprint(leaderboard)
    app.register_blueprint(keypad)

