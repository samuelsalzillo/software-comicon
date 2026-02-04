import os

from flask import Blueprint

config = Blueprint('config',__name__,url_prefix='/config')

# Aggiungi queste route
@config.route('/treasure_hunt_active')
def controls_statico():
    return  "1" if os.environ.get("TREASURE_HUNT_ACTIVE")  is not None else "0"