"""
Game Backend Service.

This module provides utility functions and services for game backend operations,
including formatting player lists and retrieving player data.
"""
from typing import List, Dict, Optional, Tuple
from ..database.select.scoring import get_scoring_by_player_id


class GameBackendService:
    """Service class for game backend operations."""

    @staticmethod
    def format_player_list(
        player_list: List[Tuple[int, str, str]],
        player_names: Dict[str, str]
    ) -> List[Dict[str, any]]:
        """
        Format a list of players with their queue information.

        Args:
            player_list: List of tuples (position, player_id, estimated_time)
            player_names: Dictionary mapping player IDs to display names

        Returns:
            List of dictionaries with formatted player information
        """
        formatted_list = []

        for pos, player_id, time_est in player_list:
            player_info = {
                'position': pos,
                'id': player_id,
                'name': player_names.get(player_id, player_id),
                'estimated_time': time_est
            }
            formatted_list.append(player_info)

        return formatted_list

    @staticmethod
    def get_player_score_data(player_id: str) -> Optional[Dict]:
        """
        Retrieve score data for a specific player.

        Args:
            player_id: Unique player identifier

        Returns:
            Dictionary with player score data, or None if not found
        """
        return get_scoring_by_player_id(player_id)

    @staticmethod
    def format_time_display(seconds: float) -> str:
        """
        Format time in seconds to MM:SS display format.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string (MM:SS)
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def calculate_score_with_penalty(
        base_time: float,
        penalty_seconds: float = 0
    ) -> float:
        """
        Calculate final score by adding penalties to base time.

        Args:
            base_time: Base time in minutes
            penalty_seconds: Penalty time in seconds to add

        Returns:
            Total score in minutes
        """
        penalty_minutes = penalty_seconds / 60.0
        return base_time + penalty_minutes


# Legacy function aliases for backward compatibility
def format_list(player_list, player_names: Dict[str, str]) -> List[Dict]:
    """
    Legacy function for formatting player lists.

    Deprecated: Use GameBackendService.format_player_list() instead.
    """
    # Convert to proper type if needed
    formatted_player_list = []
    for item in player_list:
        if len(item) >= 3:
            pos, player_id, time_est = item[0], item[1], item[2]
            formatted_player_list.append((pos, player_id, time_est))

    return GameBackendService.format_player_list(formatted_player_list, player_names)


def get_date_for_player_id(player_id: str) -> Optional[Dict]:
    """
    Legacy function for getting player score data.

    Deprecated: Use GameBackendService.get_player_score_data() instead.
    """
    return GameBackendService.get_player_score_data(player_id)


