
import sys

from dotenv import load_dotenv

from flask import Flask
import logging
import os
import socket # per il print dell'ip

from src.database.init import init
from src.database.load import load
from src.batch import thread_queue
import src.routes.import_routes as routes
import src.batch.thread_backup as thread_backup
from src.database.initialize_table import db

# importo le variabili
load_dotenv()
# Ottieni il percorso assoluto della directory 'src'
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))

# Aggiungi 'src' al sys.path se non è già presente
if src_path not in sys.path:
    sys.path.insert(0, src_path)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Impostazioni logging
logging.basicConfig(level=logging.DEBUG) 

# INIZIALIZZAZIONE DATABASE
db.init_app(app)
with app.app_context():
    db.create_all()

init.init_database()

# LOAD DATABASE
load.load_database()

routes.register_root(app)

if __name__ == '__main__':

    thread_queue.start_thread()

    thread_backup.start_thread_backup()  # Avvia il ciclo di backup automatico

    app.secret_key = os.urandom(12)
    log = logging.getLogger('werkzeug')
    # log.setLevel(logging.ERROR)
    # Esegui Flask con il riavvio automatico disabilitato
    app.run(host='0.0.0.0', port=2000, debug=True, use_reloader=False)
    print('localost:2000')
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Indirizzo IP: http://{ip_address}")
