# Avvia il thread per il salvataggio periodico
from threading import Thread
from ..database.save.save import save_queues_to_db

def start_thread():
    save_thread = Thread(target=save_queues_to_db, daemon=True)
    save_thread.start()

