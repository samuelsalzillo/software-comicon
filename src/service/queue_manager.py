"""
Queue Manager Service.

This module handles all queue-related operations for the game system,
separating queue management logic from the main GameBackend class.
"""
import logging
from typing import List, Dict, Optional
from ..utils import date

logger = logging.getLogger(__name__)


class QueueManager:
    """
    Manages player queues for different game tracks.

    This class handles adding, removing, and managing players in various
    queues (couples, singles, charlie, statico) for different game tracks.
    """

    def __init__(self):
        """Initialize queue manager with empty queues."""
        # Active queues
        self.queue_couples: List[Dict] = []
        self.queue_singles: List[Dict] = []
        self.queue_couples2: List[Dict] = []
        self.queue_singles2: List[Dict] = []
        self.queue_charlie: List[Dict] = []
        self.queue_statico: List[Dict] = []

        # Skipped players
        self.skipped_couples: List[Dict] = []
        self.skipped_singles: List[Dict] = []
        self.skipped_couples2: List[Dict] = []
        self.skipped_singles2: List[Dict] = []
        self.skipped_charlie: List[Dict] = []
        self.skipped_statico: List[Dict] = []

        # Player names mapping
        self.player_names: Dict[str, str] = {}

        logger.info("QueueManager initialized")

    def add_to_queue(
        self,
        queue_name: str,
        player_id: str,
        player_name: str
    ) -> bool:
        """
        Add a player to a specific queue.

        Args:
            queue_name: Name of the queue ('couples', 'singles', etc.)
            player_id: Unique player identifier
            player_name: Display name for the player

        Returns:
            True if player was added successfully, False if already in queue
        """
        queue = self._get_queue(queue_name)
        if queue is None:
            logger.error(f"Invalid queue name: {queue_name}")
            return False

        # Check if player already in queue
        if any(p['id'] == player_id for p in queue):
            logger.warning(f"Player {player_id} already in {queue_name}")
            return False

        # Add player to queue
        queue.append({
            'id': player_id,
            'arrival': date.get_current_time(),
            'name': player_name
        })
        self.player_names[player_id] = player_name

        logger.info(f"Added player {player_id} ({player_name}) to {queue_name}")
        return True

    def remove_from_queue(self, queue_name: str, player_id: str) -> Optional[Dict]:
        """
        Remove a player from a specific queue.

        Args:
            queue_name: Name of the queue
            player_id: Unique player identifier

        Returns:
            Removed player dict if found, None otherwise
        """
        queue = self._get_queue(queue_name)
        if queue is None:
            return None

        for i, player in enumerate(queue):
            if player['id'] == player_id:
                removed = queue.pop(i)
                logger.info(f"Removed player {player_id} from {queue_name}")
                return removed

        logger.warning(f"Player {player_id} not found in {queue_name}")
        return None

    def skip_player(self, player_id: str) -> bool:
        """
        Move a player from active queue to skipped list.

        Args:
            player_id: Unique player identifier

        Returns:
            True if player was skipped, False if not found
        """
        # Try to find and skip player in all queues
        queue_pairs = [
            ('couples', 'skipped_couples'),
            ('singles', 'skipped_singles'),
            ('couples2', 'skipped_couples2'),
            ('singles2', 'skipped_singles2'),
            ('charlie', 'skipped_charlie'),
            ('statico', 'skipped_statico')
        ]

        for queue_name, skipped_name in queue_pairs:
            player = self.remove_from_queue(queue_name, player_id)
            if player:
                skipped_queue = self._get_queue(skipped_name)
                if skipped_queue is not None:
                    skipped_queue.append(player)
                    logger.info(f"Player {player_id} moved to {skipped_name}")
                    return True

        logger.warning(f"Could not skip player {player_id} - not found in any queue")
        return False

    def restore_skipped(self, player_id: str, as_next: bool = False) -> bool:
        """
        Restore a skipped player back to their queue.

        Args:
            player_id: Unique player identifier
            as_next: If True, insert at front of queue; otherwise at back

        Returns:
            True if player was restored, False if not found
        """
        skipped_pairs = [
            ('skipped_couples', 'couples'),
            ('skipped_singles', 'singles'),
            ('skipped_couples2', 'couples2'),
            ('skipped_singles2', 'singles2'),
            ('skipped_charlie', 'charlie'),
            ('skipped_statico', 'statico')
        ]

        for skipped_name, queue_name in skipped_pairs:
            player = self.remove_from_queue(skipped_name, player_id)
            if player:
                queue = self._get_queue(queue_name)
                if queue is not None:
                    if as_next:
                        queue.insert(0, player)
                        logger.info(f"Restored player {player_id} to front of {queue_name}")
                    else:
                        queue.append(player)
                        logger.info(f"Restored player {player_id} to back of {queue_name}")
                    return True

        logger.warning(f"Could not restore player {player_id} - not found in skipped lists")
        return False

    def delete_player(self, player_id: str) -> bool:
        """
        Completely remove a player from all queues and skipped lists.

        Args:
            player_id: Unique player identifier

        Returns:
            True if player was found and deleted
        """
        found = False
        all_queues = [
            'couples', 'singles', 'couples2', 'singles2', 'charlie', 'statico',
            'skipped_couples', 'skipped_singles', 'skipped_couples2',
            'skipped_singles2', 'skipped_charlie', 'skipped_statico'
        ]

        for queue_name in all_queues:
            if self.remove_from_queue(queue_name, player_id):
                found = True

        # Remove from player names
        if player_id in self.player_names:
            del self.player_names[player_id]
            found = True

        if found:
            logger.info(f"Deleted player {player_id} from all queues")
        else:
            logger.warning(f"Player {player_id} not found in any queue")

        return found

    def get_queue_length(self, queue_name: str) -> int:
        """Get the length of a specific queue."""
        queue = self._get_queue(queue_name)
        return len(queue) if queue is not None else 0

    def get_player_position(self, queue_name: str, player_id: str) -> Optional[int]:
        """
        Get the position of a player in a queue (1-indexed).

        Returns:
            Position (1-indexed) or None if not found
        """
        queue = self._get_queue(queue_name)
        if queue is None:
            return None

        for i, player in enumerate(queue):
            if player['id'] == player_id:
                return i + 1
        return None

    def _get_queue(self, queue_name: str) -> Optional[List[Dict]]:
        """
        Internal method to get queue reference by name.

        Args:
            queue_name: Name of the queue

        Returns:
            Reference to the queue list or None if invalid name
        """
        queue_map = {
            'couples': self.queue_couples,
            'singles': self.queue_singles,
            'couples2': self.queue_couples2,
            'singles2': self.queue_singles2,
            'charlie': self.queue_charlie,
            'statico': self.queue_statico,
            'skipped_couples': self.skipped_couples,
            'skipped_singles': self.skipped_singles,
            'skipped_couples2': self.skipped_couples2,
            'skipped_singles2': self.skipped_singles2,
            'skipped_charlie': self.skipped_charlie,
            'skipped_statico': self.skipped_statico
        }
        return queue_map.get(queue_name)

    def get_all_queue_stats(self) -> Dict[str, int]:
        """
        Get statistics for all queues.

        Returns:
            Dictionary with queue names and their lengths
        """
        return {
            'couples': len(self.queue_couples),
            'singles': len(self.queue_singles),
            'couples2': len(self.queue_couples2),
            'singles2': len(self.queue_singles2),
            'charlie': len(self.queue_charlie),
            'statico': len(self.queue_statico),
            'skipped_couples': len(self.skipped_couples),
            'skipped_singles': len(self.skipped_singles),
            'skipped_couples2': len(self.skipped_couples2),
            'skipped_singles2': len(self.skipped_singles2),
            'skipped_charlie': len(self.skipped_charlie),
            'skipped_statico': len(self.skipped_statico)
        }
