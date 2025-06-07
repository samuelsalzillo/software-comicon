import os
import shutil

from flask import Blueprint, jsonify
from datetime import datetime

backup = Blueprint('backup',__name__,url_prefix='')

@backup.route('/backup_database', methods=['GET'])
def backup_database():
    try:
        # Crea la cartella backup se non esiste
        backup_dir = 'backup'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Crea un nome per il file di backup con data/ora
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Usa dt invece di datetime.datetime
        backup_filename = f"stand_db_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)

        # Effettua il backup
        shutil.copy2(os.environ.get('SQLITE_DB_PATH'), backup_path)

        return jsonify(success=True, message=f"Backup creato con successo: {backup_filename}")
    except Exception as e:
        return jsonify(success=False, error=f"Errore durante il backup: {str(e)}"), 500