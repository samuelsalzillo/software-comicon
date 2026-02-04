"""
Configuration Constants.

This module defines all configuration constants and enumerations
used throughout the application.
"""
from enum import Enum
from typing import Final


class PlayerType(Enum):
    """Player type enumeration."""
    COUPLE = 'couple'
    SINGLE = 'single'
    CHARLIE = 'charlie'
    STATICO = 'statico'


class TrackName(Enum):
    """Track name enumeration."""
    ALFA = 'alfa'
    BRAVO = 'bravo'
    ALFA2 = 'alfa2'
    BRAVO2 = 'bravo2'
    CHARLIE = 'charlie'
    DELTA = 'delta'
    ECHO = 'echo'


class QueueName(Enum):
    """Queue name enumeration."""
    COUPLES = 'couples'
    SINGLES = 'singles'
    COUPLES2 = 'couples2'
    SINGLES2 = 'singles2'
    CHARLIE = 'charlie'
    STATICO = 'statico'


class ColorCode(Enum):
    """Player color codes."""
    GIALLO = 'GIALLO'  # Yellow - Couples Track 1
    BLU = 'BLU'  # Blue - Singles Track 1
    ROSA = 'ROSA'  # Pink - Couples Track 2
    ARANCIO = 'ARANCIO'  # Orange - Singles Track 2
    VERDE = 'VERDE'  # Green - Charlie Track
    BIANCO = 'BIANCO'  # White - Statico Track


class QualificationReason(Enum):
    """Qualification reasons for leaderboard."""
    BEST_TODAY = 'best_today'
    TOP_3_OVERALL = 'top_3_overall'
    BEATS_CURRENT_TOP_3 = 'beats_current_top_3'
    FILLS_TOP_3 = 'fills_top_3'
    NOT_QUALIFIED = 'Non qualificato'


# Default timing values (in minutes)
class DefaultTimings:
    """Default timing values for different game types."""
    T_MID: Final[float] = 2.0  # Time to third button for couples
    T_TOTAL: Final[float] = 5.0  # Total time for couples
    T_SINGLE: Final[float] = 2.0  # Time for singles
    T_CHARLIE: Final[float] = 3.0  # Time for Charlie track
    T_STATICO: Final[float] = 5.0  # Time for Statico track


# Game configuration
class GameConfig:
    """Game configuration constants."""
    MIN_GAMES_FOR_AVERAGE: Final[int] = 5  # Minimum games to calculate averages
    ENTRY_THRESHOLD_MINUTES: Final[float] = 2.0  # Minutes threshold for imminent entry
    PENALTY_HOURS: Final[int] = 60  # Penalty hours for wrong QR code
    PENALTY_SECONDS: Final[int] = 216000  # Penalty in seconds (60 hours)


# Database configuration
class DatabaseConfig:
    """Database configuration constants."""
    DEFAULT_DB_PATH: Final[str] = 'stand.db'
    DB_TIMEOUT: Final[int] = 10  # Seconds
    MAX_RETRY_ATTEMPTS: Final[int] = 3
    RETRY_DELAY: Final[float] = 0.1  # Seconds


# Backup configuration
class BackupConfig:
    """Backup configuration constants."""
    DEFAULT_BACKUP_DIR: Final[str] = 'backup'
    DEFAULT_MAX_BACKUPS: Final[int] = 10
    DEFAULT_BACKUP_INTERVAL: Final[int] = 3600  # Seconds (1 hour)


# Server configuration
class ServerConfig:
    """Server configuration constants."""
    DEFAULT_HOST: Final[str] = '0.0.0.0'
    DEFAULT_PORT: Final[int] = 2000
    DEBUG_MODE: Final[bool] = True
    USE_RELOADER: Final[bool] = False


# Timezone configuration
class TimezoneConfig:
    """Timezone configuration."""
    ROME_TZ: Final[str] = 'Europe/Rome'


# Logging configuration
class LoggingConfig:
    """Logging configuration."""
    LOG_LEVEL: Final[str] = 'DEBUG'
    LOG_FORMAT: Final[str] = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT: Final[str] = '%Y-%m-%d %H:%M:%S'


# Leaderboard configuration
class LeaderboardConfig:
    """Leaderboard configuration."""
    TOP_N_PLAYERS: Final[int] = 10  # Number of players to show in leaderboard
    QUALIFIED_PLAYERS_LIMIT: Final[int] = 3  # Number of qualified players per type
