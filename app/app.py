from flask import Flask
from .routes import all_blueprints  # Use relative import for consistency
from app.db.init_db import initialize_database
from app.db.loaders import (
    load_mid_times_from_db,
    load_average_times_from_db,
    load_skipped_from_db,
    load_scores_from_db,
    load_queues_from_db,
    load_charlie_timer_history_from_db,
    start_save_thread,
)

app = Flask(__name__)
initialize_database()

# Carica dati iniziali
load_mid_times_from_db()
load_average_times_from_db()
load_skipped_from_db()
load_scores_from_db()
load_queues_from_db()
load_charlie_timer_history_from_db()
start_save_thread()

# Registra tutte le route
for bp in all_blueprints:
    app.register_blueprint(bp)
