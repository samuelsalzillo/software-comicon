import os
import time

from flask import jsonify

from ..service.external import service_php
from ..utils.date import convert_string_date_into_date
from ..model.TreasureHunt import db,TreasureHunt
from ..utils.model import format_id_number

def service_treasure_hunt(app_instance):
    with app_instance.app_context():
        time.sleep(60)
        response_php = service_php.call_for_take_records()
        if response_php and os.environ.get('TREASURE_HUNT_ACTIVE'):
            try:
                for item in response_php:
                    chiave = item.get('id')
                    id_player = item.get('id_player')
                    nome = item.get('nome')
                    cognome = item.get('cognome')
                    telefono = item.get('telefono')
                    qr_code = item.get('qrcode')
                    qr_code_founded = item.get('qrcodeFounded')
                    colore = item.get('colore')
                    timestamp_inizio = convert_string_date_into_date(item.get('timestamp_inizio'))
                    timestamp_fine = convert_string_date_into_date(item.get('timestamp_fine'))
                    if chiave:
                        existing_data = TreasureHunt.query.filter_by(chiave_esterna=int(chiave)).first()
                        if existing_data:
                            existing_data.nome = nome
                            existing_data.id_player = colore.upper() + " " + format_id_number(id_player)
                            existing_data.cognome = cognome
                            existing_data.telefono = telefono
                            existing_data.qr_code = qr_code
                            existing_data.colore = colore
                            existing_data.qr_code_founded = qr_code_founded
                            existing_data.timestamp_inizio = existing_data.timestamp_inizio
                            existing_data.timestamp_fine = existing_data.timestamp_fine
                            db.session.commit()
                            print(f"Dato con chiave '{chiave}' aggiornato.")
                        else:
                            treasure_hunt = TreasureHunt(chiave_esterna=int(chiave),nome=nome,cognome=cognome,telefono = telefono,qr_code = qr_code,qr_code_founded = qr_code_founded,timestamp_inizio = timestamp_inizio,timestamp_fine = timestamp_fine,id_player= colore.upper() + " " + format_id_number(id_player) )
                            db.session.add(treasure_hunt)
                            db.session.commit()
                            print(f"Nuovo dato con chiave '{chiave}' salvato.")
                print({'messaggio': 'Dati esterni recuperati e salvati/aggiornati con successo'})
            except Exception as e:
                db.session.rollback()
                print({'errore': f'Errore durante il salvataggio nel database: {e}'})
        else:
            print({'messaggio': 'Nessun dato recuperato dalla chiamata esterna o servizio non attivo'})
        service_treasure_hunt(app_instance)

# Metodo per recuperare tutti i record senza salvarli in memoria, solo db
def get_all_treasure_hunt():
    try:
        return TreasureHunt.query.all()
    except Exception as e:
        db.session.rollback()
        return jsonify({'errore': f'Errore durante il salvataggio nel database: {e}'}), 500


