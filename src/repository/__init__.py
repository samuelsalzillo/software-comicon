"""
Repository Package.

This package provides the Repository Pattern implementation for clean database access.
"""
from .base_repository import BaseRepository, RepositoryFactory
from .player_repository import (
    ScoringRepository,
    QualifiedPlayersRepository,
    QueueRepository,
    SkippedPlayersRepository
)
from .timing_repository import (
    AverageTimesRepository,
    MidTimesRepository,
    CharlieTimerRepository,
    TimingHistoryRepository
)

__all__ = [
    # Base
    'BaseRepository',
    'RepositoryFactory',
    # Player
    'ScoringRepository',
    'QualifiedPlayersRepository',
    'QueueRepository',
    'SkippedPlayersRepository',
    # Timing
    'AverageTimesRepository',
    'MidTimesRepository',
    'CharlieTimerRepository',
    'TimingHistoryRepository',
]


# Convenience factory functions
def get_scoring_repository() -> ScoringRepository:
    """Get ScoringRepository instance."""
    return RepositoryFactory.get_repository(ScoringRepository)


def get_qualified_players_repository() -> QualifiedPlayersRepository:
    """Get QualifiedPlayersRepository instance."""
    return RepositoryFactory.get_repository(QualifiedPlayersRepository)


def get_queue_repository() -> QueueRepository:
    """Get QueueRepository instance."""
    return RepositoryFactory.get_repository(QueueRepository)


def get_skipped_players_repository() -> SkippedPlayersRepository:
    """Get SkippedPlayersRepository instance."""
    return RepositoryFactory.get_repository(SkippedPlayersRepository)


def get_average_times_repository() -> AverageTimesRepository:
    """Get AverageTimesRepository instance."""
    return RepositoryFactory.get_repository(AverageTimesRepository)


def get_mid_times_repository() -> MidTimesRepository:
    """Get MidTimesRepository instance."""
    return RepositoryFactory.get_repository(MidTimesRepository)


def get_charlie_timer_repository() -> CharlieTimerRepository:
    """Get CharlieTimerRepository instance."""
    return RepositoryFactory.get_repository(CharlieTimerRepository)


def get_timing_history_repository(table_name: str) -> TimingHistoryRepository:
    """
    Get TimingHistoryRepository instance for a specific table.

    Args:
        table_name: Name of timing history table

    Returns:
        TimingHistoryRepository instance
    """
    # For dynamic table names, create directly
    return TimingHistoryRepository(table_name)
