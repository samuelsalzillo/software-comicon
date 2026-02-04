"""
Treasure Hunt Player Model.

This module defines the TreasureHunt database model for tracking
players participating in the treasure hunt activity.
"""
from datetime import datetime
from pytz import timezone

from ..database.initialize_table import db

# Rome timezone for consistent datetime handling
ROME_TZ = timezone('Europe/Rome')


class TreasureHunt(db.Model):
    """
    Model representing a treasure hunt player entry.

    Attributes:
        id: Primary key
        id_player: Player identifier (color + number format)
        chiave_esterna: External key, unique identifier from external system
        nome: Player's first name
        cognome: Player's last name
        qr_code_founded: QR code that was actually found by player
        qr_code: Expected QR code for the player
        timestamp_inizio: Start timestamp of treasure hunt
        timestamp_fine: End timestamp of treasure hunt
        telefono: Player's phone number
    """
    __tablename__ = 'treasure_hunt'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_player = db.Column(db.Text, nullable=False, index=True)
    chiave_esterna = db.Column(db.String(80), unique=True, nullable=False, index=True)
    nome = db.Column(db.Text, nullable=True)
    cognome = db.Column(db.Text, nullable=True)
    qr_code_founded = db.Column(db.Text, nullable=True)
    qr_code = db.Column(db.Text, nullable=True)
    timestamp_inizio = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ROME_TZ),
        nullable=False
    )
    timestamp_fine = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ROME_TZ),
        nullable=False
    )
    telefono = db.Column(db.Text, nullable=True)

    def __repr__(self) -> str:
        """String representation of TreasureHunt instance."""
        return f"<TreasureHunt(id={self.id}, player={self.id_player}, key={self.chiave_esterna})>"

    @property
    def full_name(self) -> str:
        """Get player's full name."""
        if self.nome and self.cognome:
            return f"{self.nome} {self.cognome}"
        return self.nome or self.cognome or "N/A"

    @property
    def duration_seconds(self) -> float:
        """Calculate duration of treasure hunt in seconds."""
        if self.timestamp_fine and self.timestamp_inizio:
            return (self.timestamp_fine - self.timestamp_inizio).total_seconds()
        return 0.0

    @property
    def is_qr_code_correct(self) -> bool:
        """Check if player found the correct QR code."""
        return self.qr_code_founded == self.qr_code

    def to_dict(self) -> dict:
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary representation of the treasure hunt entry
        """
        return {
            'id': self.id,
            'id_player': self.id_player,
            'chiave_esterna': self.chiave_esterna,
            'nome': self.nome,
            'cognome': self.cognome,
            'full_name': self.full_name,
            'qr_code_founded': self.qr_code_founded,
            'qr_code': self.qr_code,
            'is_qr_correct': self.is_qr_code_correct,
            'timestamp_inizio': self.timestamp_inizio.isoformat() if self.timestamp_inizio else None,
            'timestamp_fine': self.timestamp_fine.isoformat() if self.timestamp_fine else None,
            'duration_seconds': self.duration_seconds,
            'telefono': self.telefono
        }

