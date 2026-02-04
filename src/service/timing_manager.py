"""
Timing Manager Service.

This module manages game timing statistics, averages, and history tracking.
"""
import logging
from typing import List, Tuple, Dict, Optional
from statistics import mean

logger = logging.getLogger(__name__)


class TimingManager:
    """
    Manages game timing statistics and averages.

    This class tracks timing history for different game types and calculates
    dynamic averages for scheduling and estimation purposes.
    """

    def __init__(self):
        """Initialize timing manager with default values."""
        # Default timing values (in minutes)
        self.default_t_mid = 2.0
        self.default_t_total = 5.0
        self.default_t_single = 2.0
        self.default_t_charlie = 3.0
        self.default_t_statico = 5.0

        # Current timing values (updated from history)
        self.t_mid = self.default_t_mid
        self.t_total = self.default_t_total
        self.t_single = self.default_t_single
        self.t_mid2 = self.default_t_mid
        self.t_single2 = self.default_t_single
        self.t_charlie = self.default_t_charlie
        self.t_statico = self.default_t_statico

        # History tracking - Timer durations (for averages)
        self.couple_timer_history: List[float] = []
        self.single_timer_history: List[float] = []
        self.single_timer_history2: List[float] = []
        self.charlie_timer_history: List[float] = []

        # History tracking - Mid times (time to third button)
        self.couple_history_mid: List[float] = []
        self.couple_history_mid2: List[float] = []

        # History tracking - Official scores (with penalties)
        self.couple_history_total: List[Tuple[str, float]] = []
        self.single_history: List[Tuple[str, float]] = []
        self.couple_history_total2: List[Tuple[str, float]] = []
        self.single_history2: List[Tuple[str, float]] = []
        self.charlie_history: List[Tuple[str, float]] = []
        self.statico_history: List[Tuple[str, float]] = []

        # Minimum number of games required to calculate averages
        self.min_games_for_avg = 5

        logger.info("TimingManager initialized with default values")

    def record_couple_game(
        self,
        player_id: str,
        timer_duration: float,
        official_score: float,
        track_set: int = 1
    ) -> None:
        """
        Record timing data for a couple game.

        Args:
            player_id: Player identifier
            timer_duration: Actual timer duration (for averages)
            official_score: Official score with penalties (for leaderboard)
            track_set: 1 for first track set, 2 for second
        """
        # Record timer duration for averages
        self.couple_timer_history.append(timer_duration)

        # Record official score for leaderboard
        if track_set == 1:
            self.couple_history_total.append((player_id, official_score))
        else:
            self.couple_history_total2.append((player_id, official_score))

        logger.info(
            f"Recorded couple game (set {track_set}): "
            f"player={player_id}, timer={timer_duration:.2f}m, score={official_score:.2f}m"
        )

    def record_single_game(
        self,
        player_id: str,
        timer_duration: float,
        official_score: float,
        track_set: int = 1
    ) -> None:
        """
        Record timing data for a single game.

        Args:
            player_id: Player identifier
            timer_duration: Actual timer duration
            official_score: Official score with penalties
            track_set: 1 for first track set, 2 for second
        """
        if track_set == 1:
            self.single_timer_history.append(timer_duration)
            self.single_history.append((player_id, official_score))
        else:
            self.single_timer_history2.append(timer_duration)
            self.single_history2.append((player_id, official_score))

        logger.info(
            f"Recorded single game (set {track_set}): "
            f"player={player_id}, timer={timer_duration:.2f}m, score={official_score:.2f}m"
        )

    def record_charlie_game(
        self,
        player_id: str,
        timer_duration: float,
        official_score: Optional[float] = None
    ) -> None:
        """
        Record timing data for a Charlie game.

        Args:
            player_id: Player identifier
            timer_duration: Actual timer duration
            official_score: Optional official score (uses timer_duration if not provided)
        """
        self.charlie_timer_history.append(timer_duration)

        score = official_score if official_score is not None else timer_duration
        self.charlie_history.append((player_id, score))

        logger.info(
            f"Recorded charlie game: player={player_id}, "
            f"timer={timer_duration:.2f}m, score={score:.2f}m"
        )

    def record_statico_game(self, player_id: str, game_time: float) -> None:
        """
        Record timing data for a Statico game.

        Args:
            player_id: Player identifier
            game_time: Game duration
        """
        self.statico_history.append((player_id, game_time))
        logger.info(f"Recorded statico game: player={player_id}, time={game_time:.2f}m")

    def record_mid_time(self, mid_duration: float, track_set: int = 1) -> None:
        """
        Record mid-time (time to third button) for couples.

        Args:
            mid_duration: Duration until third button press
            track_set: 1 for first track set, 2 for second
        """
        if track_set == 1:
            self.couple_history_mid.append(mid_duration)
            logger.debug(f"Recorded mid time (set 1): {mid_duration:.2f}m")
        else:
            self.couple_history_mid2.append(mid_duration)
            logger.debug(f"Recorded mid time (set 2): {mid_duration:.2f}m")

    def update_averages(self) -> None:
        """
        Update all timing averages based on recorded history.

        This method recalculates average times using recent game data,
        falling back to defaults if insufficient data is available.
        """
        logger.debug("Updating timing averages...")

        # T_mid (Set 1) - based on mid times
        if len(self.couple_history_mid) >= self.min_games_for_avg:
            self.t_mid = mean(self.couple_history_mid)
            logger.debug(f"Calculated t_mid: {self.t_mid:.2f}m from {len(self.couple_history_mid)} records")
        else:
            self.t_mid = self.default_t_mid
            logger.debug(f"Using default t_mid: {self.t_mid:.2f}m")

        # T_mid2 (Set 2)
        if len(self.couple_history_mid2) >= self.min_games_for_avg:
            self.t_mid2 = mean(self.couple_history_mid2)
            logger.debug(f"Calculated t_mid2: {self.t_mid2:.2f}m from {len(self.couple_history_mid2)} records")
        else:
            self.t_mid2 = self.default_t_mid
            logger.debug(f"Using default t_mid2: {self.t_mid2:.2f}m")

        # T_total - based on timer history for couples
        if len(self.couple_timer_history) >= self.min_games_for_avg:
            self.t_total = mean(self.couple_timer_history)
            logger.debug(f"Calculated t_total: {self.t_total:.2f}m from {len(self.couple_timer_history)} records")
        else:
            self.t_total = self.default_t_total
            logger.debug(f"Using default t_total: {self.t_total:.2f}m")

        # T_single (Set 1)
        if len(self.single_timer_history) >= self.min_games_for_avg:
            self.t_single = mean(self.single_timer_history)
            logger.debug(f"Calculated t_single: {self.t_single:.2f}m from {len(self.single_timer_history)} records")
        else:
            self.t_single = self.default_t_single
            logger.debug(f"Using default t_single: {self.t_single:.2f}m")

        # T_single2 (Set 2)
        if len(self.single_timer_history2) >= self.min_games_for_avg:
            self.t_single2 = mean(self.single_timer_history2)
            logger.debug(f"Calculated t_single2: {self.t_single2:.2f}m from {len(self.single_timer_history2)} records")
        else:
            self.t_single2 = self.default_t_single
            logger.debug(f"Using default t_single2: {self.t_single2:.2f}m")

        # T_charlie
        if len(self.charlie_timer_history) >= self.min_games_for_avg:
            self.t_charlie = mean(self.charlie_timer_history)
            logger.debug(f"Calculated t_charlie: {self.t_charlie:.2f}m from {len(self.charlie_timer_history)} records")
        else:
            self.t_charlie = self.default_t_charlie
            logger.debug(f"Using default t_charlie: {self.t_charlie:.2f}m")

        # T_statico
        if len(self.statico_history) >= self.min_games_for_avg:
            statico_times = [time for _, time in self.statico_history]
            self.t_statico = mean(statico_times)
            logger.debug(f"Calculated t_statico: {self.t_statico:.2f}m from {len(statico_times)} records")
        else:
            self.t_statico = self.default_t_statico
            logger.debug(f"Using default t_statico: {self.t_statico:.2f}m")

        logger.info(
            f"Averages updated: t_mid={self.t_mid:.2f}, t_total={self.t_total:.2f}, "
            f"t_single={self.t_single:.2f}, t_charlie={self.t_charlie:.2f}, "
            f"t_statico={self.t_statico:.2f}"
        )

    def get_timing_stats(self) -> Dict[str, Dict]:
        """
        Get detailed timing statistics.

        Returns:
            Dictionary with current values, defaults, and history sizes
        """
        return {
            'couple': {
                'current': {
                    't_mid': self.t_mid,
                    't_mid2': self.t_mid2,
                    't_total': self.t_total
                },
                'defaults': {
                    't_mid': self.default_t_mid,
                    't_total': self.default_t_total
                },
                'history_size': {
                    'mid': len(self.couple_history_mid),
                    'mid2': len(self.couple_history_mid2),
                    'timer': len(self.couple_timer_history),
                    'scores': len(self.couple_history_total) + len(self.couple_history_total2)
                }
            },
            'single': {
                'current': {
                    't_single': self.t_single,
                    't_single2': self.t_single2
                },
                'defaults': {
                    't_single': self.default_t_single
                },
                'history_size': {
                    'timer': len(self.single_timer_history),
                    'timer2': len(self.single_timer_history2),
                    'scores': len(self.single_history) + len(self.single_history2)
                }
            },
            'charlie': {
                'current': {'t_charlie': self.t_charlie},
                'defaults': {'t_charlie': self.default_t_charlie},
                'history_size': {
                    'timer': len(self.charlie_timer_history),
                    'scores': len(self.charlie_history)
                }
            },
            'statico': {
                'current': {'t_statico': self.t_statico},
                'defaults': {'t_statico': self.default_t_statico},
                'history_size': {'scores': len(self.statico_history)}
            }
        }
