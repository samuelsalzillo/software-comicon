from datetime import datetime
from pytz import timezone

from ..database.initialize_table import db

# Modello del Database
class TreasureHunt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_player = db.Column(db.Text, nullable=False)
    chiave_esterna = db.Column(db.String(80), unique=True, nullable=False)
    nome = db.Column(db.Text, nullable=True)
    cognome = db.Column(db.Text, nullable=True)
    qr_code_founded = db.Column(db.Text, nullable=True)
    qr_code = db.Column(db.Text, nullable=True)
    timestamp_inizio = db.Column(db.DateTime, default=lambda: datetime.now(timezone('Europe/Rome')))
    timestamp_fine = db.Column(db.DateTime, default=lambda: datetime.now(timezone('Europe/Rome')))
    telefono = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<TreasureHunt {self.chiave_esterna}>"