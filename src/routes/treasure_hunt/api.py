from flask import Blueprint
from ...service import service_treasure_hunt

treasure_hunt = Blueprint('treasure_hunt',__name__,url_prefix='/aggiorna-dati')

@treasure_hunt.route('', methods=['POST'])
def aggiorna_dati():
    return service_treasure_hunt.service_treasure_hunt()

