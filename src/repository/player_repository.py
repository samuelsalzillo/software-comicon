"""
Player Repository.

Repository for managing player-related data including scoring and qualified players.
"""
import logging
from typing import Dict, List, Optional

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ScoringRepository(BaseRepository[Dict]):
    """Repository for scoring table."""

    @property
    def table_name(self) -> str:
        return 'scoring'

    def _get_id_column(self) -> str:
        return 'player_id'

    def find_by_player_id(self, player_id: str) -> Optional[Dict]:
        """
        Find scoring record by player ID.

        Args:
            player_id: Player identifier

        Returns:
            Scoring record or None
        """
        return self.find_by_id(player_id)

    def find_by_type(
        self,
        player_type: str,
        limit: Optional[int] = None,
        order_by: str = "score ASC"
    ) -> List[Dict]:
        """
        Find players by type.

        Args:
            player_type: Player type (couple, single, charlie, statico)
            limit: Maximum results
            order_by: Order clause

        Returns:
            List of scoring records
        """
        return self.find_by_criteria(
            {'player_type': player_type},
            limit=limit,
            order_by=order_by
        )

    def get_leaderboard(
        self,
        player_type: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get leaderboard (top players) for a type.

        Args:
            player_type: Player type
            limit: Number of top players

        Returns:
            List of top players ordered by score
        """
        return self.find_by_type(player_type, limit=limit, order_by="score ASC")

    def get_top_score(self, player_type: str) -> Optional[float]:
        """
        Get the best (lowest) score for a player type.

        Args:
            player_type: Player type

        Returns:
            Best score or None
        """
        query = """
            SELECT MIN(score) as best_score
            FROM scoring
            WHERE player_type = ?
        """
        result = self.execute_query(query, (player_type,), fetch_one=True)
        return result['best_score'] if result else None

    def save_score(
        self,
        player_id: str,
        player_name: str,
        player_type: str,
        score: float
    ) -> int:
        """
        Save or update a player's score.

        Args:
            player_id: Player identifier
            player_name: Player name
            player_type: Player type
            score: Score in minutes

        Returns:
            Row ID
        """
        entity = {
            'player_id': player_id,
            'player_name': player_name,
            'player_type': player_type,
            'score': score
        }
        return self.save(entity)

    def get_player_ranking(self, player_id: str) -> Optional[int]:
        """
        Get player's ranking (position) in their type leaderboard.

        Args:
            player_id: Player identifier

        Returns:
            Ranking position (1-indexed) or None
        """
        player = self.find_by_player_id(player_id)
        if not player:
            return None

        query = """
            SELECT COUNT(*) + 1 as rank
            FROM scoring
            WHERE player_type = ? AND score < ?
        """
        result = self.execute_query(
            query,
            (player['player_type'], player['score']),
            fetch_one=True
        )
        return result['rank'] if result else None


class QualifiedPlayersRepository(BaseRepository[Dict]):
    """Repository for qualified_players table."""

    @property
    def table_name(self) -> str:
        return 'qualified_players'

    def _get_id_column(self) -> str:
        return 'player_id'

    def find_by_player_id(self, player_id: str) -> Optional[Dict]:
        """
        Find qualified player by ID.

        Args:
            player_id: Player identifier

        Returns:
            Qualified player record or None
        """
        return self.find_by_id(player_id)

    def find_qualified_by_type(
        self,
        player_type: str,
        limit: int = 3
    ) -> List[Dict]:
        """
        Find qualified players by type.

        Args:
            player_type: Player type
            limit: Maximum results (default 3 for top 3)

        Returns:
            List of qualified players
        """
        return self.find_by_criteria(
            {'player_type': player_type},
            limit=limit,
            order_by="score_minutes ASC"
        )

    def save_qualified_player(
        self,
        player_id: str,
        player_name: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        score_minutes: float,
        score_formatted: str,
        player_type: str,
        qualification_reason: str,
        qualification_date: str,
        created_at: str
    ) -> int:
        """
        Save a qualified player's contact information.

        Args:
            player_id: Player identifier
            player_name: Team/player name
            first_name: Contact first name
            last_name: Contact last name
            phone_number: Contact phone
            score_minutes: Qualifying score
            score_formatted: Formatted score (MM:SS)
            player_type: Player type
            qualification_reason: Reason for qualification
            qualification_date: Date of qualification
            created_at: Creation timestamp

        Returns:
            Row ID
        """
        entity = {
            'player_id': player_id,
            'player_name': player_name,
            'first_name': first_name,
            'last_name': last_name,
            'phone_number': phone_number,
            'score_minutes': score_minutes,
            'score_formatted': score_formatted,
            'player_type': player_type,
            'qualification_reason': qualification_reason,
            'qualification_date': qualification_date,
            'created_at': created_at
        }
        return self.save(entity)

    def is_player_qualified(self, player_id: str) -> bool:
        """
        Check if a player is qualified.

        Args:
            player_id: Player identifier

        Returns:
            True if qualified, False otherwise
        """
        return self.exists(player_id)

    def get_top_qualified_scores(
        self,
        player_type: str,
        limit: int = 3
    ) -> List[float]:
        """
        Get top qualified scores for a player type.

        Args:
            player_type: Player type
            limit: Number of scores

        Returns:
            List of scores
        """
        query = """
            SELECT score_minutes
            FROM qualified_players
            WHERE player_type = ?
            ORDER BY score_minutes ASC
            LIMIT ?
        """
        results = self.execute_query(query, (player_type, limit), fetch_all=True)
        return [r['score_minutes'] for r in results]

    def update_treasure_hunt_status(
        self,
        player_id: str,
        treasure_hunt_updated: str
    ) -> bool:
        """
        Update treasure hunt completion status for qualified player.

        Args:
            player_id: Player identifier
            treasure_hunt_updated: Timestamp of update

        Returns:
            True if updated, False if not found
        """
        if not self.exists(player_id):
            return False

        query = """
            UPDATE qualified_players
            SET treasure_hunt_updated = ?
            WHERE player_id = ?
        """
        self.execute_query(query, (treasure_hunt_updated, player_id), fetch_all=False)
        return True


class QueueRepository(BaseRepository[Dict]):
    """Repository for queue table."""

    @property
    def table_name(self) -> str:
        return 'queue'

    def _get_id_column(self) -> str:
        return 'player_id'

    def find_by_player_id(self, player_id: str) -> Optional[Dict]:
        """Find queue entry by player ID."""
        return self.find_by_id(player_id)

    def find_by_queue_type(
        self,
        queue_type: str,
        order_by: str = "position ASC"
    ) -> List[Dict]:
        """
        Find all players in a specific queue.

        Args:
            queue_type: Queue type (couples, singles, charlie, etc.)
            order_by: Order clause

        Returns:
            List of queue entries
        """
        return self.find_by_criteria(
            {'queue_type': queue_type},
            order_by=order_by
        )

    def add_to_queue(
        self,
        player_id: str,
        player_name: str,
        queue_type: str,
        position: int,
        arrival_time: str
    ) -> int:
        """
        Add a player to a queue.

        Args:
            player_id: Player identifier
            player_name: Player name
            queue_type: Queue type
            position: Position in queue
            arrival_time: Arrival timestamp

        Returns:
            Row ID
        """
        entity = {
            'player_id': player_id,
            'player_name': player_name,
            'queue_type': queue_type,
            'position': position,
            'arrival_time': arrival_time
        }
        return self.save(entity)

    def remove_from_queue(self, player_id: str) -> bool:
        """
        Remove a player from queue.

        Args:
            player_id: Player identifier

        Returns:
            True if removed, False if not found
        """
        return self.delete(player_id)

    def get_queue_length(self, queue_type: str) -> int:
        """
        Get length of a specific queue.

        Args:
            queue_type: Queue type

        Returns:
            Number of players in queue
        """
        return self.count({'queue_type': queue_type})

    def clear_queue(self, queue_type: str) -> int:
        """
        Clear all players from a queue.

        Args:
            queue_type: Queue type

        Returns:
            Number of players removed
        """
        return self.delete_by_criteria({'queue_type': queue_type})


class SkippedPlayersRepository(BaseRepository[Dict]):
    """Repository for skipped_players table."""

    @property
    def table_name(self) -> str:
        return 'skipped'

    def _get_id_column(self) -> str:
        return 'player_id'

    def find_by_queue_type(self, queue_type: str) -> List[Dict]:
        """
        Find skipped players by queue type.

        Args:
            queue_type: Queue type

        Returns:
            List of skipped players
        """
        return self.find_by_criteria(
            {'queue_type': queue_type},
            order_by="skipped_at DESC"
        )

    def add_skipped(
        self,
        player_id: str,
        player_name: str,
        queue_type: str,
        skipped_at: str
    ) -> int:
        """
        Add a player to skipped list.

        Args:
            player_id: Player identifier
            player_name: Player name
            queue_type: Original queue type
            skipped_at: Skip timestamp

        Returns:
            Row ID
        """
        entity = {
            'player_id': player_id,
            'player_name': player_name,
            'queue_type': queue_type,
            'skipped_at': skipped_at
        }
        return self.save(entity)

    def remove_skipped(self, player_id: str) -> bool:
        """
        Remove a player from skipped list.

        Args:
            player_id: Player identifier

        Returns:
            True if removed, False if not found
        """
        return self.delete(player_id)

    def get_all_skipped(self) -> Dict[str, List[Dict]]:
        """
        Get all skipped players grouped by queue type.

        Returns:
            Dictionary with queue types as keys and player lists as values
        """
        all_skipped = self.find_all()

        grouped = {}
        for player in all_skipped:
            queue_type = player['queue_type']
            if queue_type not in grouped:
                grouped[queue_type] = []
            grouped[queue_type].append(player)

        return grouped
