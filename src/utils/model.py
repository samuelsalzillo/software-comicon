from ..model.GameBackend import GameBackend
__game_backend = GameBackend()

def get_game_backend():
    global __game_backend
    return __game_backend

def set_game_backend(game_backend):
    global __game_backend
    __game_backend = game_backend

def format_id_number(id_player):
    while len(id_player) < 3:
        id_player =  '0' + id_player
    return id_player