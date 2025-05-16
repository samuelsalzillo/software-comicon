from datetime import datetime
from pytz import timezone

from ..database.initialize_table import db

# Modello del Database
class TreasureHunt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chiave_esterna = db.Column(db.String(80), unique=True, nullable=False)
    valore = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone('Europe/Rome')))

    def __repr__(self):
        return f"<TreasureHunt {self.chiave_esterna}>"