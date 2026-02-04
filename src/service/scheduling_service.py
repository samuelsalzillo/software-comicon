"""
Scheduling Service.

This module provides advanced scheduling capabilities for game tracks,
including waiting time calculations, schedule simulation, and entry time estimation.
"""
import datetime
import logging
from typing import List, Dict, Optional
from copy import deepcopy

from ..config import GameConfig
from ..exceptions import SchedulingError

logger = logging.getLogger(__name__)


class SchedulingService:
    """
    Service for scheduling and waiting time calculations.

    This class handles all scheduling logic including:
    - Waiting time calculations for players
    - Schedule simulation for multiple tracks
    - Entry time estimation
    - Queue optimization
    """

    def __init__(self):
        """Initialize SchedulingService."""
        logger.info("SchedulingService initialized")

    # ============================================================================
    # WAITING TIME CALCULATIONS
    # ============================================================================

    def calculate_waiting_time(
        self,
        player_type: str,
        position: int,
        queue_lengths: Dict[str, int],
        timing_params: Dict[str, float],
        current_track_state: Optional[Dict] = None
    ) -> float:
        """
        Calculate estimated waiting time for a player.

        Args:
            player_type: Type of player ('couple', 'single', 'charlie', 'statico')
            position: Position in queue (1-indexed)
            queue_lengths: Dictionary with lengths of all queues
            timing_params: Dictionary with timing parameters (t_mid, t_total, t_single, etc.)
            current_track_state: Optional current state of tracks

        Returns:
            Estimated waiting time in minutes

        Raises:
            SchedulingError: If calculation fails
        """
        logger.debug(f"Calculating wait time for {player_type} at position {position}")

        try:
            if player_type in ('couple', 'couple2'):
                return self._calculate_couple_waiting_time(
                    position,
                    queue_lengths,
                    timing_params,
                    track_set=2 if player_type == 'couple2' else 1
                )
            elif player_type in ('single', 'single2'):
                return self._calculate_single_waiting_time(
                    position,
                    queue_lengths,
                    timing_params,
                    track_set=2 if player_type == 'single2' else 1
                )
            elif player_type == 'charlie':
                return self._calculate_charlie_waiting_time(
                    position,
                    timing_params.get('t_charlie', GameConfig.MIN_GAMES_FOR_AVERAGE)
                )
            elif player_type == 'statico':
                return self._calculate_statico_waiting_time(
                    position,
                    timing_params.get('t_statico', 5.0),
                    current_track_state
                )
            else:
                raise SchedulingError(f"Unknown player type: {player_type}")
        except Exception as e:
            logger.error(f"Error calculating waiting time: {e}", exc_info=True)
            raise SchedulingError(f"Failed to calculate waiting time: {e}")

    def _calculate_couple_waiting_time(
        self,
        position: int,
        queue_lengths: Dict[str, int],
        timing_params: Dict[str, float],
        track_set: int = 1
    ) -> float:
        """
        Calculate waiting time for a couple.

        Uses the formula based on queue dynamics and timing parameters.

        Args:
            position: Position in couple queue (1-indexed)
            queue_lengths: All queue lengths
            timing_params: Timing parameters
            track_set: 1 or 2

        Returns:
            Waiting time in minutes
        """
        singles_key = 'singles' if track_set == 1 else 'singles2'
        len_singles = queue_lengths.get(singles_key, 0)

        t_mid = timing_params.get('t_mid' if track_set == 1 else 't_mid2', 2.0)
        t_total = timing_params.get('t_total', 5.0)
        t_single = timing_params.get('t_single' if track_set == 1 else 't_single2', 2.0)

        # Formula: considera interleaving con singles
        if t_total <= (t_single + t_mid) and position <= len_singles:
            wait_time = t_single * (position - 1) + t_mid * (position - 1)
        elif t_total <= (t_single + t_mid):
            wait_time = t_single * len_singles + t_mid * len_singles + t_total * (position - len_singles)
        else:
            wait_time = t_total * (position - 1)

        logger.debug(
            f"Couple (set {track_set}) wait time: position={position}, "
            f"singles={len_singles}, result={wait_time:.2f}min"
        )
        return wait_time

    def _calculate_single_waiting_time(
        self,
        position: int,
        queue_lengths: Dict[str, int],
        timing_params: Dict[str, float],
        track_set: int = 1
    ) -> float:
        """
        Calculate waiting time for a single player.

        Args:
            position: Position in single queue (1-indexed)
            queue_lengths: All queue lengths
            timing_params: Timing parameters
            track_set: 1 or 2

        Returns:
            Waiting time in minutes
        """
        couples_key = 'couples' if track_set == 1 else 'couples2'
        len_couples = queue_lengths.get(couples_key, 0)

        t_mid = timing_params.get('t_mid' if track_set == 1 else 't_mid2', 2.0)
        t_single = timing_params.get('t_single' if track_set == 1 else 't_single2', 2.0)

        # Formula: singles can enter during couple's first half
        if position <= len_couples:
            n_couples = position
        else:
            n_couples = len_couples

        wait_time = t_mid * n_couples + t_single * (position - 1)

        logger.debug(
            f"Single (set {track_set}) wait time: position={position}, "
            f"couples={len_couples}, result={wait_time:.2f}min"
        )
        return wait_time

    def _calculate_charlie_waiting_time(self, position: int, t_charlie: float) -> float:
        """
        Calculate waiting time for Charlie track.

        Args:
            position: Position in queue (1-indexed)
            t_charlie: Average game duration

        Returns:
            Waiting time in minutes
        """
        wait_time = t_charlie * (position - 1)
        logger.debug(f"Charlie wait time: position={position}, result={wait_time:.2f}min")
        return wait_time

    def _calculate_statico_waiting_time(
        self,
        position: int,
        t_statico: float,
        current_track_state: Optional[Dict] = None
    ) -> float:
        """
        Calculate waiting time for Statico track.

        Considers two parallel tracks (Delta and Echo).

        Args:
            position: Position in queue (1-indexed)
            t_statico: Average game duration
            current_track_state: Current state of Delta and Echo tracks

        Returns:
            Waiting time in minutes
        """
        # With 2 parallel tracks, waiting time is approximately halved
        # Formula: ceil(position/2) * t_statico - adjustment for current occupancy

        effective_position = (position + 1) // 2  # Ceil division by 2
        wait_time = t_statico * (effective_position - 1)

        # Adjust if tracks are currently occupied
        if current_track_state:
            delta_occupied = current_track_state.get('delta_occupied', False)
            echo_occupied = current_track_state.get('echo_occupied', False)

            if delta_occupied and echo_occupied:
                # Both occupied, add minimal wait
                wait_time += t_statico * 0.5
            elif delta_occupied or echo_occupied:
                # One occupied, slight adjustment
                wait_time += t_statico * 0.25

        logger.debug(f"Statico wait time: position={position}, result={wait_time:.2f}min")
        return wait_time

    # ============================================================================
    # SCHEDULE SIMULATION
    # ============================================================================

    def simulate_schedule_track_set_1(
        self,
        queue_couples: List[Dict],
        queue_singles: List[Dict],
        timing_params: Dict[str, float],
        current_time: datetime.datetime,
        alfa_available: datetime.datetime,
        bravo_available: datetime.datetime
    ) -> Dict[str, datetime.datetime]:
        """
        Simulate complete schedule for track set 1 (Alfa/Bravo).

        This method simulates the exact sequence of player entries considering:
        - Track availability times
        - Game durations
        - Interleaving of couples and singles

        Args:
            queue_couples: List of couples in queue
            queue_singles: List of singles in queue
            timing_params: Timing parameters
            current_time: Current time
            alfa_available: When Alfa track becomes available
            bravo_available: When Bravo track becomes available

        Returns:
            Dictionary mapping player_id to estimated entry time
        """
        logger.debug("Simulating schedule for track set 1")

        estimated_times = {}
        sim_time = max(current_time, alfa_available)
        bravo_avail = max(bravo_available, sim_time)

        # Get timing parameters
        t_mid = timing_params.get('t_mid', 2.0)
        t_total = timing_params.get('t_total', 5.0)
        t_single = timing_params.get('t_single', 2.0)

        dt_mid = datetime.timedelta(minutes=t_mid)
        dt_total = datetime.timedelta(minutes=t_total)
        dt_single = datetime.timedelta(minutes=t_single)

        # Deep copy to avoid modifying original queues
        couples = deepcopy(queue_couples)
        singles = deepcopy(queue_singles)

        # Simulation loop
        while couples or singles:
            # If no couples and singles exist, process single
            if not couples and singles:
                item = singles.pop(0)
                estimated_times[item['id']] = sim_time
                sim_time = sim_time + dt_single
                continue

            # If Bravo is available, prioritize couples
            if bravo_avail <= sim_time:
                if couples:
                    item = couples.pop(0)
                    estimated_times[item['id']] = sim_time
                    sim_time = sim_time + dt_mid
                    bravo_avail = estimated_times[item['id']] + dt_total
                    continue
                else:
                    if singles:
                        item = singles.pop(0)
                        estimated_times[item['id']] = sim_time
                        sim_time = sim_time + dt_single
                        continue
                    else:
                        break
            else:
                # Bravo occupied, can only process singles
                if singles:
                    item = singles.pop(0)
                    estimated_times[item['id']] = sim_time
                    sim_time = sim_time + dt_single
                    continue
                else:
                    # No singles, wait for Bravo
                    sim_time = bravo_avail
                    continue

        logger.debug(f"Track set 1 simulation complete: {len(estimated_times)} players scheduled")
        return estimated_times

    def simulate_schedule_track_set_2(
        self,
        queue_couples2: List[Dict],
        queue_singles2: List[Dict],
        timing_params: Dict[str, float],
        current_time: datetime.datetime,
        alfa2_available: datetime.datetime,
        bravo2_available: datetime.datetime
    ) -> Dict[str, datetime.datetime]:
        """
        Simulate complete schedule for track set 2 (Alfa2/Bravo2).

        Similar to track set 1 but uses track set 2 parameters.

        Args:
            queue_couples2: List of couples2 in queue
            queue_singles2: List of singles2 in queue
            timing_params: Timing parameters
            current_time: Current time
            alfa2_available: When Alfa2 track becomes available
            bravo2_available: When Bravo2 track becomes available

        Returns:
            Dictionary mapping player_id to estimated entry time
        """
        logger.debug("Simulating schedule for track set 2")

        estimated_times = {}
        sim_time = max(current_time, alfa2_available)
        bravo_avail = max(bravo2_available, sim_time)

        # Get timing parameters
        t_mid2 = timing_params.get('t_mid2', 2.0)
        t_total = timing_params.get('t_total', 5.0)
        t_single2 = timing_params.get('t_single2', 2.0)

        dt_mid2 = datetime.timedelta(minutes=t_mid2)
        dt_total = datetime.timedelta(minutes=t_total)
        dt_single2 = datetime.timedelta(minutes=t_single2)

        couples = deepcopy(queue_couples2)
        singles = deepcopy(queue_singles2)

        while couples or singles:
            if not couples and singles:
                item = singles.pop(0)
                estimated_times[item['id']] = sim_time
                sim_time = sim_time + dt_single2
                continue

            if bravo_avail <= sim_time:
                if couples:
                    item = couples.pop(0)
                    estimated_times[item['id']] = sim_time
                    sim_time = sim_time + dt_mid2
                    bravo_avail = estimated_times[item['id']] + dt_total
                    continue
                else:
                    if singles:
                        item = singles.pop(0)
                        estimated_times[item['id']] = sim_time
                        sim_time = sim_time + dt_single2
                        continue
                    else:
                        break
            else:
                if singles:
                    item = singles.pop(0)
                    estimated_times[item['id']] = sim_time
                    sim_time = sim_time + dt_single2
                    continue
                else:
                    sim_time = bravo_avail
                    continue

        logger.debug(f"Track set 2 simulation complete: {len(estimated_times)} players scheduled")
        return estimated_times

    def simulate_schedule_charlie(
        self,
        queue_charlie: List[Dict],
        timing_params: Dict[str, float],
        current_time: datetime.datetime,
        charlie_available: datetime.datetime
    ) -> Dict[str, datetime.datetime]:
        """
        Simulate schedule for Charlie track.

        Args:
            queue_charlie: List of Charlie players in queue
            timing_params: Timing parameters
            current_time: Current time
            charlie_available: When Charlie track becomes available

        Returns:
            Dictionary mapping player_id to estimated entry time
        """
        logger.debug("Simulating schedule for Charlie track")

        estimated_times = {}
        sim_time = max(current_time, charlie_available)
        t_charlie = timing_params.get('t_charlie', 3.0)
        dt_charlie = datetime.timedelta(minutes=t_charlie)

        for player in queue_charlie:
            estimated_times[player['id']] = sim_time
            sim_time = sim_time + dt_charlie

        logger.debug(f"Charlie simulation complete: {len(estimated_times)} players scheduled")
        return estimated_times

    def simulate_schedule_statico(
        self,
        queue_statico: List[Dict],
        timing_params: Dict[str, float],
        current_time: datetime.datetime,
        delta_available: datetime.datetime,
        echo_available: datetime.datetime
    ) -> Dict[str, datetime.datetime]:
        """
        Simulate schedule for Statico tracks (Delta and Echo).

        Considers two parallel tracks for optimal scheduling.

        Args:
            queue_statico: List of Statico players in queue
            timing_params: Timing parameters
            current_time: Current time
            delta_available: When Delta track becomes available
            echo_available: When Echo track becomes available

        Returns:
            Dictionary mapping player_id to estimated entry time
        """
        logger.debug("Simulating schedule for Statico tracks")

        estimated_times = {}
        t_statico = timing_params.get('t_statico', 5.0)
        dt_statico = datetime.timedelta(minutes=t_statico)

        # Track availability times
        delta_avail = max(current_time, delta_available)
        echo_avail = max(current_time, echo_available)

        # Distribute players across two tracks
        for player in queue_statico:
            # Use the track that becomes available first
            if delta_avail <= echo_avail:
                estimated_times[player['id']] = delta_avail
                delta_avail = delta_avail + dt_statico
            else:
                estimated_times[player['id']] = echo_avail
                echo_avail = echo_avail + dt_statico

        logger.debug(f"Statico simulation complete: {len(estimated_times)} players scheduled")
        return estimated_times

    # ============================================================================
    # ENTRY TIME ESTIMATION
    # ============================================================================

    def get_next_entry_candidates(
        self,
        estimated_times: Dict[str, datetime.datetime],
        current_time: datetime.datetime,
        threshold_minutes: float = 2.0
    ) -> List[str]:
        """
        Get list of players who are candidates for imminent entry.

        Args:
            estimated_times: Dictionary of player_id to estimated entry time
            current_time: Current time
            threshold_minutes: Minutes threshold for "imminent" entry

        Returns:
            List of player IDs who should enter soon
        """
        threshold = datetime.timedelta(minutes=threshold_minutes)
        candidates = []

        for player_id, entry_time in estimated_times.items():
            if entry_time <= current_time + threshold:
                candidates.append(player_id)

        logger.debug(f"Found {len(candidates)} entry candidates within {threshold_minutes}min")
        return candidates

    def format_entry_time(
        self,
        entry_time: datetime.datetime,
        current_time: datetime.datetime,
        is_next: bool = False
    ) -> str:
        """
        Format entry time for display.

        Args:
            entry_time: Estimated entry time
            current_time: Current time
            is_next: Whether this is the next player

        Returns:
            Formatted time string
        """
        if is_next:
            return "PROSSIMO INGRESSO"

        # Calculate minutes until entry
        delta = (entry_time - current_time).total_seconds() / 60

        if delta < 1:
            return "IMMINENTE"
        elif delta < 60:
            return f"~{int(delta)}min"
        else:
            return entry_time.strftime('%H:%M')

    # ============================================================================
    # QUEUE OPTIMIZATION
    # ============================================================================

    def suggest_queue_optimization(
        self,
        queue_lengths: Dict[str, int],
        timing_params: Dict[str, float],
        track_availability: Dict[str, bool]
    ) -> Dict[str, str]:
        """
        Suggest optimizations for queue management.

        Analyzes current queue state and suggests actions to optimize flow.

        Args:
            queue_lengths: Current queue lengths
            timing_params: Timing parameters
            track_availability: Track availability status

        Returns:
            Dictionary with optimization suggestions
        """
        suggestions = {}

        # Check for imbalance between track sets
        couples1 = queue_lengths.get('couples', 0)
        couples2 = queue_lengths.get('couples2', 0)
        singles1 = queue_lengths.get('singles', 0)
        singles2 = queue_lengths.get('singles2', 0)

        # Suggest redistribution if imbalance is significant
        if couples1 > couples2 + 3:
            suggestions['couples'] = f"Considera di redistribuire alcune coppie al set 2 (diff: {couples1 - couples2})"
        elif couples2 > couples1 + 3:
            suggestions['couples'] = f"Considera di redistribuire alcune coppie al set 1 (diff: {couples2 - couples1})"

        if singles1 > singles2 + 3:
            suggestions['singles'] = f"Considera di redistribuire alcuni singoli al set 2 (diff: {singles1 - singles2})"
        elif singles2 > singles1 + 3:
            suggestions['singles'] = f"Considera di redistribuire alcuni singoli al set 1 (diff: {singles2 - singles1})"

        # Check for long queues
        charlie_len = queue_lengths.get('charlie', 0)
        if charlie_len > 5:
            avg_wait = charlie_len * timing_params.get('t_charlie', 3.0)
            suggestions['charlie'] = f"Coda lunga ({charlie_len} giocatori, ~{int(avg_wait)}min attesa)"

        statico_len = queue_lengths.get('statico', 0)
        if statico_len > 8:  # With 2 tracks, this is concerning
            avg_wait = (statico_len / 2) * timing_params.get('t_statico', 5.0)
            suggestions['statico'] = f"Coda lunga ({statico_len} giocatori, ~{int(avg_wait)}min attesa)"

        logger.info(f"Generated {len(suggestions)} optimization suggestions")
        return suggestions

    # ============================================================================
    # STATISTICS & ANALYTICS
    # ============================================================================

    def calculate_throughput(
        self,
        timing_params: Dict[str, float],
        track_set: int = 1
    ) -> Dict[str, float]:
        """
        Calculate theoretical throughput for a track set.

        Args:
            timing_params: Timing parameters
            track_set: Track set number (1 or 2)

        Returns:
            Dictionary with throughput metrics (players per hour)
        """
        t_mid = timing_params.get(f't_mid{"" if track_set == 1 else "2"}', 2.0)
        t_total = timing_params.get('t_total', 5.0)
        t_single = timing_params.get(f't_single{"" if track_set == 1 else "2"}', 2.0)

        # Couples throughput (limited by Bravo)
        couples_per_hour = 60.0 / t_total if t_total > 0 else 0

        # Singles throughput (can interleave with couples)
        # Assuming optimal interleaving
        singles_per_hour = 60.0 / t_single if t_single > 0 else 0

        # Combined optimal throughput
        # This is a simplified calculation
        combined_per_hour = (60.0 / max(t_mid, t_single)) if max(t_mid, t_single) > 0 else 0

        return {
            'couples_per_hour': couples_per_hour,
            'singles_per_hour': singles_per_hour,
            'combined_optimal_per_hour': combined_per_hour,
            'track_set': track_set
        }

    def estimate_queue_clear_time(
        self,
        queue_lengths: Dict[str, int],
        timing_params: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Estimate time to clear all queues.

        Args:
            queue_lengths: Current queue lengths
            timing_params: Timing parameters

        Returns:
            Dictionary with estimated clear times in minutes
        """
        clear_times = {}

        # Track set 1
        couples1 = queue_lengths.get('couples', 0)
        singles1 = queue_lengths.get('singles', 0)
        if couples1 > 0 or singles1 > 0:
            t_total = timing_params.get('t_total', 5.0)
            t_single = timing_params.get('t_single', 2.0)
            # Simplified: assume optimal interleaving
            clear_times['track_set_1'] = max(couples1 * t_total, singles1 * t_single)

        # Track set 2
        couples2 = queue_lengths.get('couples2', 0)
        singles2 = queue_lengths.get('singles2', 0)
        if couples2 > 0 or singles2 > 0:
            t_total = timing_params.get('t_total', 5.0)
            t_single2 = timing_params.get('t_single2', 2.0)
            clear_times['track_set_2'] = max(couples2 * t_total, singles2 * t_single2)

        # Charlie
        charlie_len = queue_lengths.get('charlie', 0)
        if charlie_len > 0:
            t_charlie = timing_params.get('t_charlie', 3.0)
            clear_times['charlie'] = charlie_len * t_charlie

        # Statico (2 parallel tracks)
        statico_len = queue_lengths.get('statico', 0)
        if statico_len > 0:
            t_statico = timing_params.get('t_statico', 5.0)
            clear_times['statico'] = ((statico_len + 1) // 2) * t_statico

        logger.debug(f"Estimated clear times: {clear_times}")
        return clear_times


# ============================================================================
# SINGLETON PATTERN
# ============================================================================

_scheduling_service: Optional[SchedulingService] = None


def get_scheduling_service() -> SchedulingService:
    """
    Get or create SchedulingService singleton instance.

    Returns:
        SchedulingService instance
    """
    global _scheduling_service
    if _scheduling_service is None:
        _scheduling_service = SchedulingService()
    return _scheduling_service
