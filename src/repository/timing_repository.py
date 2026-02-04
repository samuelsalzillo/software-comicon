"""
Timing Repository.

Repository for managing timing-related data including average times and mid times.
"""
import logging
from typing import Dict, List, Optional

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class AverageTimesRepository(BaseRepository[Dict]):
    """Repository for average_times table."""

    @property
    def table_name(self) -> str:
        return 'average_times'

    def find_by_player_type(self, player_type: str) -> Optional[Dict]:
        """
        Find average times by player type.

        Args:
            player_type: Player type (couple, single, charlie, statico)

        Returns:
            Average times record or None
        """
        return self.find_by_id(player_type)

    def save_average(
        self,
        player_type: str,
        timer_duration_minutes: float,
        official_score_minutes: float
    ) -> int:
        """
        Save average time for a player type.

        Args:
            player_type: Player type
            timer_duration_minutes: Average timer duration
            official_score_minutes: Average official score

        Returns:
            Row ID
        """
        entity = {
            'player_type': player_type,
            'timer_duration_minutes': timer_duration_minutes,
            'official_score_minutes': official_score_minutes
        }
        return self.save(entity)

    def get_all_averages(self) -> Dict[str, Dict]:
        """
        Get all average times indexed by player type.

        Returns:
            Dictionary with player types as keys
        """
        results = self.find_all()
        return {r['player_type']: r for r in results}

    def update_timer_average(
        self,
        player_type: str,
        timer_duration_minutes: float
    ) -> bool:
        """
        Update timer average for a player type.

        Args:
            player_type: Player type
            timer_duration_minutes: New average timer duration

        Returns:
            True if updated, False if not found
        """
        if not self.exists(player_type):
            return False

        query = """
            UPDATE average_times
            SET timer_duration_minutes = ?
            WHERE player_type = ?
        """
        self.execute_query(query, (timer_duration_minutes, player_type), fetch_all=False)
        return True

    def update_score_average(
        self,
        player_type: str,
        official_score_minutes: float
    ) -> bool:
        """
        Update score average for a player type.

        Args:
            player_type: Player type
            official_score_minutes: New average official score

        Returns:
            True if updated, False if not found
        """
        if not self.exists(player_type):
            return False

        query = """
            UPDATE average_times
            SET official_score_minutes = ?
            WHERE player_type = ?
        """
        self.execute_query(query, (official_score_minutes, player_type), fetch_all=False)
        return True


class MidTimesRepository(BaseRepository[Dict]):
    """Repository for mid_times table."""

    @property
    def table_name(self) -> str:
        return 'mid_times'

    def save_mid_time(
        self,
        couple_type: str,
        mid_duration_minutes: float
    ) -> int:
        """
        Save a mid time record.

        Args:
            couple_type: Couple type (couple1, couple2)
            mid_duration_minutes: Mid duration in minutes

        Returns:
            Row ID
        """
        entity = {
            'couple_type': couple_type,
            'mid_duration_minutes': mid_duration_minutes
        }
        return self.insert(entity)

    def get_mid_times_by_type(
        self,
        couple_type: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get mid times for a couple type.

        Args:
            couple_type: Couple type
            limit: Maximum results

        Returns:
            List of mid time records
        """
        return self.find_by_criteria(
            {'couple_type': couple_type},
            limit=limit,
            order_by="id DESC"
        )

    def get_recent_mid_times(
        self,
        couple_type: str,
        count: int = 10
    ) -> List[float]:
        """
        Get recent mid times for calculation.

        Args:
            couple_type: Couple type
            count: Number of recent records

        Returns:
            List of mid durations
        """
        records = self.get_mid_times_by_type(couple_type, limit=count)
        return [r['mid_duration_minutes'] for r in records]

    def get_average_mid_time(self, couple_type: str, last_n: int = 10) -> Optional[float]:
        """
        Calculate average mid time from recent records.

        Args:
            couple_type: Couple type
            last_n: Number of recent records to average

        Returns:
            Average mid time or None
        """
        durations = self.get_recent_mid_times(couple_type, count=last_n)

        if not durations:
            return None

        return sum(durations) / len(durations)


class CharlieTimerRepository(BaseRepository[Dict]):
    """Repository for charlie_timer table."""

    @property
    def table_name(self) -> str:
        return 'charlie_timer'

    def save_charlie_timer(
        self,
        player_id: str,
        timer_duration_minutes: float
    ) -> int:
        """
        Save a Charlie timer record.

        Args:
            player_id: Player identifier
            timer_duration_minutes: Timer duration

        Returns:
            Row ID
        """
        entity = {
            'player_id': player_id,
            'timer_duration_minutes': timer_duration_minutes
        }
        return self.insert(entity)

    def get_charlie_times(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get Charlie timer records.

        Args:
            limit: Maximum results

        Returns:
            List of Charlie timer records
        """
        return self.find_all(limit=limit)

    def get_recent_charlie_times(self, count: int = 10) -> List[float]:
        """
        Get recent Charlie times for calculation.

        Args:
            count: Number of recent records

        Returns:
            List of timer durations
        """
        query = f"""
            SELECT timer_duration_minutes
            FROM {self.table_name}
            ORDER BY id DESC
            LIMIT ?
        """
        results = self.execute_query(query, (count,), fetch_all=True)
        return [r['timer_duration_minutes'] for r in results]

    def get_average_charlie_time(self, last_n: int = 10) -> Optional[float]:
        """
        Calculate average Charlie time from recent records.

        Args:
            last_n: Number of recent records to average

        Returns:
            Average Charlie time or None
        """
        durations = self.get_recent_charlie_times(count=last_n)

        if not durations:
            return None

        return sum(durations) / len(durations)

    def get_charlie_time_by_player(self, player_id: str) -> Optional[Dict]:
        """
        Get Charlie time for a specific player.

        Args:
            player_id: Player identifier

        Returns:
            Charlie timer record or None
        """
        results = self.find_by_criteria({'player_id': player_id}, limit=1)
        return results[0] if results else None


class TimingHistoryRepository(BaseRepository[Dict]):
    """
    Generic repository for timing history.

    Can be used for couple_history, single_history, etc.
    """

    def __init__(self, table_name: str, db_path: Optional[str] = None):
        """
        Initialize with specific table name.

        Args:
            table_name: Name of the timing history table
            db_path: Optional database path
        """
        self._table_name = table_name
        super().__init__(db_path)

    @property
    def table_name(self) -> str:
        return self._table_name

    def save_timing(
        self,
        player_id: str,
        timer_duration_minutes: float,
        official_score_minutes: float
    ) -> int:
        """
        Save a timing record.

        Args:
            player_id: Player identifier
            timer_duration_minutes: Timer duration
            official_score_minutes: Official score

        Returns:
            Row ID
        """
        entity = {
            'player_id': player_id,
            'timer_duration_minutes': timer_duration_minutes,
            'official_score_minutes': official_score_minutes
        }
        return self.insert(entity)

    def get_recent_timings(self, count: int = 10) -> List[Dict]:
        """
        Get recent timing records.

        Args:
            count: Number of recent records

        Returns:
            List of timing records
        """
        query = f"""
            SELECT *
            FROM {self.table_name}
            ORDER BY id DESC
            LIMIT ?
        """
        return self.execute_query(query, (count,), fetch_all=True)

    def get_player_timings(self, player_id: str) -> List[Dict]:
        """
        Get all timings for a specific player.

        Args:
            player_id: Player identifier

        Returns:
            List of timing records
        """
        return self.find_by_criteria({'player_id': player_id}, order_by="id DESC")

    def calculate_average_timer(self, last_n: int = 10) -> Optional[float]:
        """
        Calculate average timer duration from recent records.

        Args:
            last_n: Number of recent records

        Returns:
            Average timer duration or None
        """
        records = self.get_recent_timings(count=last_n)

        if not records:
            return None

        durations = [r['timer_duration_minutes'] for r in records]
        return sum(durations) / len(durations)

    def calculate_average_score(self, last_n: int = 10) -> Optional[float]:
        """
        Calculate average official score from recent records.

        Args:
            last_n: Number of recent records

        Returns:
            Average official score or None
        """
        records = self.get_recent_timings(count=last_n)

        if not records:
            return None

        scores = [r['official_score_minutes'] for r in records]
        return sum(scores) / len(scores)
