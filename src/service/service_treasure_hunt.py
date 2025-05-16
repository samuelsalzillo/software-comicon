from flask import jsonify

from ..service.external import service_php
from ..model.TreasureHunt import TreasureHunt,db

def service_treasure_hunt():
    response_php = service_php.call_for_take_records()
    if response_php:
        try:
            for item in response_php:
                chiave = item.get('id')
                valore = None
                #todo qui da inserire gli altri item
                if chiave:
                    existing_data = TreasureHunt.query.filter_by(chiave_esterna=chiave).first()
                    if existing_data:
                        #todo qui la modifica
                        existing_data.valore = valore
                        db.session.commit()
                        print(f"Dato con chiave '{chiave}' aggiornato.")
                    else:
                        treasure_hunt = TreasureHunt(chiave_esterna=chiave,valore=valore)
                        db.session.add(treasure_hunt)
                        db.session.commit()
                        print(f"Nuovo dato con chiave '{chiave}' salvato.")
            return jsonify({'messaggio': 'Dati esterni recuperati e salvati/aggiornati con successo'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'errore': f'Errore durante il salvataggio nel database: {e}'}), 500
    else:
        return jsonify({'messaggio': 'Nessun dato recuperato dalla chiamata esterna'}), 200

# Metodo per recuperare tutti i record senza salvarli in memoria, solo db
def get_all_treasure_hunt():
    try:
        return TreasureHunt.query.all()
    except Exception as e:
        db.session.rollback()
        return jsonify({'errore': f'Errore durante il salvataggio nel database: {e}'}), 500