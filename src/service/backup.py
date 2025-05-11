import glob
import logging
import os
import shutil
import threading
import time
from threading import Timer
from datetime import datetime
from ..utils import timer


def backup_database_auto():
    try:
        # Crea la cartella backup se non esiste
        backup_dir = 'backup'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Crea un nome per il file di backup con data/ora
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"stand_db_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)

        # Effettua il backup
        shutil.copy2(os.environ.get('SQLITE_DB_PATH'), backup_path)
        logging.info(f"Backup automatico creato: {backup_filename}")

        # Gestione dei backup vecchi
        backup_files = glob.glob(os.path.join(backup_dir, 'stand_db_backup_*.db'))
        backup_files.sort(key=os.path.getmtime)  # Ordina per data di modifica (più vecchio prima)

        # Elimina i backup più vecchi se superiamo il massimo
        while len(backup_files) > int(os.environ.get('MAX_BACKUPS')):
            oldest_backup = backup_files.pop(0)
            os.remove(oldest_backup)
            logging.info(f"Rimosso backup vecchio: {os.path.basename(oldest_backup)}")
    except Exception as e:
        logging.error(f"Errore durante il backup automatico: {e}")
    finally:
        timer.timer_for_thread(int(os.environ.get('BACKUP_INTERVAL')),"backup")
        # Programma il prossimo backup
        backup_database_auto()