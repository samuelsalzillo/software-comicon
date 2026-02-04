"""
Refactored Game Backend - Facade Pattern.

This module provides the main GameBackend class that coordinates all game operations
using the new manager classes. It acts as a facade to maintain backward compatibility
while delegating responsibilities to specialized managers.
"""
import logging
import os
import sqlite3
import datetime
from copy import deepcopy
from threading import Lock
from typing import Optional, List, Dict, Tuple, Union

import pytz

from ..service.queue_manager import QueueManager
from ..service.track_manager import TrackManager
from ..service.timing_manager import TimingManager
from ..utils import date
from ..config import PlayerType, GameConfig
from ..exceptions import (
    PlayerNotFoundError,
    TrackOccupiedError,
    QueueError,
    TrackError
)

logger = logging.getLogger(__name__)


class GameBackend:
    """
    Main game backend coordinator using Facade pattern.
    
    This class acts as a facade that coordinates operations between
    QueueManager, TrackManager, and TimingManager while maintaining
    backward compatibility with existing code.
    
    Attributes:
        queue_manager: Manages all player queues
        track_manager: Manages all game tracks
        timing_manager: Manages timing statistics and averages
        rome_tz: Rome timezone for datetime operations
    """
    
    def __init__(self) -> None:
        """Initialize GameBackend with all managers."""
        logger.info("Initializing GameBackend with manager architecture")
        
        # Initialize managers
        self.queue_manager = QueueManager()
        self.track_manager = TrackManager()
        self.timing_manager = TimingManager()
        
        # Rome timezone
        self.rome_tz = pytz.timezone('Europe/Rome')
        
        # Next player tracking (coordinated across managers)
        self.next_player_alfa_bravo_id: Optional[str] = None
        self.next_player_alfa_bravo_locked: bool = False
        self.next_player_alfa_bravo_name: Optional[str] = None
        self.next_player_alfa_bravo_id2: Optional[str] = None
        self.next_player_alfa_bravo_locked2: bool = False
        self.next_player_alfa_bravo_name2: Optional[str] = None
        self.next_player_charlie_id: Optional[str] = None
        self.next_player_charlie_locked: bool = False
        self.next_player_charlie_name: Optional[str] = None
        self.next_player_statico_id: Optional[str] = None
        self.next_player_statico_locked: bool = False
        self.next_player_statico_name: Optional[str] = None
        
        logger.info("GameBackend initialized successfully")
    
    # ============================================================================
    # BACKWARD COMPATIBILITY: Properties that delegate to managers
    # ============================================================================
    
    @property
    def queue_couples(self) -> List[Dict]:
        """Delegate to queue_manager."""
        return self.queue_manager.queue_couples
    
    @property
    def queue_singles(self) -> List[Dict]:
        """Delegate to queue_manager."""
        return self.queue_manager.queue_singles
    
    @property
    def queue_couples2(self) -> List[Dict]:
        """Delegate to queue_manager."""
        return self.queue_manager.queue_couples2
    
    @property
    def queue_singles2(self) -> List[Dict]:
        """Delegate to queue_manager."""
        return self.queue_manager.queue_singles2
    
    @property
    def queue_charlie(self) -> List[Dict]:
        """Delegate to queue_manager."""
        return self.queue_manager.queue_charlie
    
    @property
    def queue_statico(self) -> List[Dict]:
        """Delegate to queue_manager."""
        return self.queue_manager.queue_statico
    
    @property
    def skipped_couples(self) -> List[Dict]:
        """Delegate to queue_manager."""
        return self.queue_manager.skipped_couples
    
    @property
    def skipped_singles(self) -> List[Dict]:
        """Delegate to queue_manager."""
        return self.queue_manager.skipped_singles
    
    @property
    def skipped_couples2(self) -> List[Dict]:
        """Delegate to queue_manager."""
        return self.queue_manager.skipped_couples2
    
    @property
    def skipped_singles2(self) -> List[Dict]:
        """Delegate to queue_manager."""
        return self.queue_manager.skipped_singles2
    
    @property
    def skipped_charlie(self) -> List[Dict]:
        """Delegate to queue_manager."""
        return self.queue_manager.skipped_charlie
    
    @property
    def skipped_statico(self) -> List[Dict]:
        """Delegate to queue_manager."""
        return self.queue_manager.skipped_statico
    
    @property
    def player_names(self) -> Dict[str, str]:
        """Delegate to queue_manager."""
        return self.queue_manager.player_names
    
    # Track properties
    @property
    def current_player_alfa(self) -> Optional[Dict]:
        """Delegate to track_manager."""
        return self.track_manager.current_player_alfa
    
    @current_player_alfa.setter
    def current_player_alfa(self, value: Optional[Dict]):
        """Delegate to track_manager."""
        self.track_manager.current_player_alfa = value
    
    @property
    def current_player_bravo(self) -> Optional[Dict]:
        """Delegate to track_manager."""
        return self.track_manager.current_player_bravo
    
    @current_player_bravo.setter
    def current_player_bravo(self, value: Optional[Dict]):
        """Delegate to track_manager."""
        self.track_manager.current_player_bravo = value
    
    @property
    def current_player_alfa2(self) -> Optional[Dict]:
        """Delegate to track_manager."""
        return self.track_manager.current_player_alfa2
    
    @current_player_alfa2.setter
    def current_player_alfa2(self, value: Optional[Dict]):
        """Delegate to track_manager."""
        self.track_manager.current_player_alfa2 = value
    
    @property
    def current_player_bravo2(self) -> Optional[Dict]:
        """Delegate to track_manager."""
        return self.track_manager.current_player_bravo2
    
    @current_player_bravo2.setter
    def current_player_bravo2(self, value: Optional[Dict]):
        """Delegate to track_manager."""
        self.track_manager.current_player_bravo2 = value
    
    @property
    def current_player_charlie(self) -> Optional[Dict]:
        """Delegate to track_manager."""
        return self.track_manager.current_player_charlie
    
    @current_player_charlie.setter
    def current_player_charlie(self, value: Optional[Dict]):
        """Delegate to track_manager."""
        self.track_manager.current_player_charlie = value
    
    @property
    def current_player_delta(self) -> Optional[Dict]:
        """Delegate to track_manager."""
        return self.track_manager.current_player_delta
    
    @current_player_delta.setter
    def current_player_delta(self, value: Optional[Dict]):
        """Delegate to track_manager."""
        self.track_manager.current_player_delta = value
    
    @property
    def current_player_echo(self) -> Optional[Dict]:
        """Delegate to track_manager."""
        return self.track_manager.current_player_echo
    
    @current_player_echo.setter
    def current_player_echo(self, value: Optional[Dict]):
        """Delegate to track_manager."""
        self.track_manager.current_player_echo = value
    
    @property
    def current_player_couple(self) -> Optional[Dict]:
        """Delegate to track_manager."""
        return self.track_manager.current_player_couple
    
    @current_player_couple.setter
    def current_player_couple(self, value: Optional[Dict]):
        """Delegate to track_manager."""
        self.track_manager.current_player_couple = value
    
    @property
    def current_player_couple2(self) -> Optional[Dict]:
        """Delegate to track_manager."""
        return self.track_manager.current_player_couple2
    
    @current_player_couple2.setter
    def current_player_couple2(self, value: Optional[Dict]):
        """Delegate to track_manager."""
        self.track_manager.current_player_couple2 = value
    
    # Track state flags
    @property
    def couple_in_alfa(self) -> bool:
        """Delegate to track_manager."""
        return self.track_manager.couple_in_alfa
    
    @couple_in_alfa.setter
    def couple_in_alfa(self, value: bool):
        """Delegate to track_manager."""
        self.track_manager.couple_in_alfa = value
    
    @property
    def couple_in_bravo(self) -> bool:
        """Delegate to track_manager."""
        return self.track_manager.couple_in_bravo
    
    @couple_in_bravo.setter
    def couple_in_bravo(self, value: bool):
        """Delegate to track_manager."""
        self.track_manager.couple_in_bravo = value
    
    @property
    def single_in_alfa(self) -> bool:
        """Delegate to track_manager."""
        return self.track_manager.single_in_alfa
    
    @single_in_alfa.setter
    def single_in_alfa(self, value: bool):
        """Delegate to track_manager."""
        self.track_manager.single_in_alfa = value
    
    @property
    def couple_in_alfa2(self) -> bool:
        """Delegate to track_manager."""
        return self.track_manager.couple_in_alfa2
    
    @couple_in_alfa2.setter
    def couple_in_alfa2(self, value: bool):
        """Delegate to track_manager."""
        self.track_manager.couple_in_alfa2 = value
    
    @property
    def couple_in_bravo2(self) -> bool:
        """Delegate to track_manager."""
        return self.track_manager.couple_in_bravo2
    
    @couple_in_bravo2.setter
    def couple_in_bravo2(self, value: bool):
        """Delegate to track_manager."""
        self.track_manager.couple_in_bravo2 = value
    
    @property
    def single_in_alfa2(self) -> bool:
        """Delegate to track_manager."""
        return self.track_manager.single_in_alfa2
    
    @single_in_alfa2.setter
    def single_in_alfa2(self, value: bool):
        """Delegate to track_manager."""
        self.track_manager.single_in_alfa2 = value
    
    @property
    def third_button_pressed(self) -> bool:
        """Delegate to track_manager."""
        return self.track_manager.third_button_pressed
    
    @third_button_pressed.setter
    def third_button_pressed(self, value: bool):
        """Delegate to track_manager."""
        self.track_manager.third_button_pressed = value
    
    @property
    def third_button_pressed2(self) -> bool:
        """Delegate to track_manager."""
        return self.track_manager.third_button_pressed2
    
    @third_button_pressed2.setter
    def third_button_pressed2(self, value: bool):
        """Delegate to track_manager."""
        self.track_manager.third_button_pressed2 = value
    
    @property
    def player_in_charlie(self) -> bool:
        """Delegate to track_manager."""
        return self.track_manager.player_in_charlie
    
    @player_in_charlie.setter
    def player_in_charlie(self, value: bool):
        """Delegate to track_manager."""
        self.track_manager.player_in_charlie = value
    
    @property
    def statico_in_delta(self) -> bool:
        """Delegate to track_manager."""
        return self.track_manager.statico_in_delta
    
    @statico_in_delta.setter
    def statico_in_delta(self, value: bool):
        """Delegate to track_manager."""
        self.track_manager.statico_in_delta = value
    
    @property
    def statico_in_echo(self) -> bool:
        """Delegate to track_manager."""
        return self.track_manager.statico_in_echo
    
    @statico_in_echo.setter
    def statico_in_echo(self, value: bool):
        """Delegate to track_manager."""
        self.track_manager.statico_in_echo = value
    
    # Track availability times
    @property
    def ALFA_next_available(self) -> datetime.datetime:
        """Delegate to track_manager."""
        return self.track_manager.ALFA_next_available

    @ALFA_next_available.setter
    def ALFA_next_available(self, value: datetime.datetime):
        """Delegate to track_manager."""
        self.track_manager.ALFA_next_available = value

    @property
    def BRAVO_next_available(self) -> datetime.datetime:
        """Delegate to track_manager."""
        return self.track_manager.BRAVO_next_available

    @BRAVO_next_available.setter
    def BRAVO_next_available(self, value: datetime.datetime):
        """Delegate to track_manager."""
        self.track_manager.BRAVO_next_available = value

    @property
    def ALFA_next_available2(self) -> datetime.datetime:
        """Delegate to track_manager."""
        return self.track_manager.ALFA_next_available2

    @ALFA_next_available2.setter
    def ALFA_next_available2(self, value: datetime.datetime):
        """Delegate to track_manager."""
        self.track_manager.ALFA_next_available2 = value

    @property
    def BRAVO_next_available2(self) -> datetime.datetime:
        """Delegate to track_manager."""
        return self.track_manager.BRAVO_next_available2

    @BRAVO_next_available2.setter
    def BRAVO_next_available2(self, value: datetime.datetime):
        """Delegate to track_manager."""
        self.track_manager.BRAVO_next_available2 = value

    @property
    def CHARLIE_next_available(self) -> datetime.datetime:
        """Delegate to track_manager."""
        return self.track_manager.CHARLIE_next_available

    @CHARLIE_next_available.setter
    def CHARLIE_next_available(self, value: datetime.datetime):
        """Delegate to track_manager."""
        self.track_manager.CHARLIE_next_available = value

    @property
    def DELTA_next_available(self) -> datetime.datetime:
        """Delegate to track_manager."""
        return self.track_manager.DELTA_next_available

    @DELTA_next_available.setter
    def DELTA_next_available(self, value: datetime.datetime):
        """Delegate to track_manager."""
        self.track_manager.DELTA_next_available = value

    @property
    def ECHO_next_available(self) -> datetime.datetime:
        """Delegate to track_manager."""
        return self.track_manager.ECHO_next_available

    @ECHO_next_available.setter
    def ECHO_next_available(self, value: datetime.datetime):
        """Delegate to track_manager."""
        self.track_manager.ECHO_next_available = value

    # Timing properties
    @property
    def T_mid(self) -> float:
        """Delegate to timing_manager."""
        return self.timing_manager.t_mid
    
    @T_mid.setter
    def T_mid(self, value: float):
        """Delegate to timing_manager."""
        self.timing_manager.t_mid = value
    
    @property
    def T_total(self) -> float:
        """Delegate to timing_manager."""
        return self.timing_manager.t_total
    
    @T_total.setter
    def T_total(self, value: float):
        """Delegate to timing_manager."""
        self.timing_manager.t_total = value
    
    @property
    def T_single(self) -> float:
        """Delegate to timing_manager."""
        return self.timing_manager.t_single
    
    @T_single.setter
    def T_single(self, value: float):
        """Delegate to timing_manager."""
        self.timing_manager.t_single = value
    
    @property
    def T_mid2(self) -> float:
        """Delegate to timing_manager."""
        return self.timing_manager.t_mid2
    
    @T_mid2.setter
    def T_mid2(self, value: float):
        """Delegate to timing_manager."""
        self.timing_manager.t_mid2 = value
    
    @property
    def T_single2(self) -> float:
        """Delegate to timing_manager."""
        return self.timing_manager.t_single2
    
    @T_single2.setter
    def T_single2(self, value: float):
        """Delegate to timing_manager."""
        self.timing_manager.t_single2 = value
    
    @property
    def T_charlie(self) -> float:
        """Delegate to timing_manager."""
        return self.timing_manager.t_charlie
    
    @T_charlie.setter
    def T_charlie(self, value: float):
        """Delegate to timing_manager."""
        self.timing_manager.t_charlie = value
    
    @property
    def T_statico(self) -> float:
        """Delegate to timing_manager."""
        return self.timing_manager.t_statico
    
    @T_statico.setter
    def T_statico(self, value: float):
        """Delegate to timing_manager."""
        self.timing_manager.t_statico = value
    
    # Default timing values
    @property
    def default_T_mid(self) -> float:
        """Delegate to timing_manager."""
        return self.timing_manager.default_t_mid
    
    @property
    def default_T_total(self) -> float:
        """Delegate to timing_manager."""
        return self.timing_manager.default_t_total
    
    @property
    def default_T_single(self) -> float:
        """Delegate to timing_manager."""
        return self.timing_manager.default_t_single
    
    @property
    def default_T_charlie(self) -> float:
        """Delegate to timing_manager."""
        return self.timing_manager.default_t_charlie
    
    @property
    def default_T_statico(self) -> float:
        """Delegate to timing_manager."""
        return self.timing_manager.default_t_statico
    
    # Timing history
    @property
    def couple_history_mid(self) -> List[float]:
        """Delegate to timing_manager."""
        return self.timing_manager.couple_history_mid
    
    @property
    def couple_history_mid2(self) -> List[float]:
        """Delegate to timing_manager."""
        return self.timing_manager.couple_history_mid2
    
    @property
    def couple_history_total(self) -> List[Tuple[str, float]]:
        """Delegate to timing_manager."""
        return self.timing_manager.couple_history_total
    
    @property
    def couple_history_total2(self) -> List[Tuple[str, float]]:
        """Delegate to timing_manager."""
        return self.timing_manager.couple_history_total2
    
    @property
    def single_history(self) -> List[Tuple[str, float]]:
        """Delegate to timing_manager."""
        return self.timing_manager.single_history
    
    @property
    def single_history2(self) -> List[Tuple[str, float]]:
        """Delegate to timing_manager."""
        return self.timing_manager.single_history2
    
    @property
    def charlie_history(self) -> List[Tuple[str, float]]:
        """Delegate to timing_manager."""
        return self.timing_manager.charlie_history
    
    @property
    def statico_history(self) -> List[Tuple[str, float]]:
        """Delegate to timing_manager."""
        return self.timing_manager.statico_history
    
    @property
    def couple_timer_history(self) -> List[float]:
        """Delegate to timing_manager."""
        return self.timing_manager.couple_timer_history
    
    @property
    def single_timer_history(self) -> List[float]:
        """Delegate to timing_manager."""
        return self.timing_manager.single_timer_history
    
    @property
    def single_timer_history2(self) -> List[float]:
        """Delegate to timing_manager."""
        return self.timing_manager.single_timer_history2
    
    @property
    def charlie_timer_history(self) -> List[float]:
        """Delegate to timing_manager."""
        return self.timing_manager.charlie_timer_history
    
    @property
    def player_start_times(self) -> Dict[str, datetime.datetime]:
        """Delegate to track_manager."""
        return self.track_manager.player_start_times
    
    @property
    def player_durations(self) -> Dict[str, float]:
        """Delegate to track_manager."""
        return self.track_manager.player_durations
    
    # ============================================================================
    # QUEUE OPERATIONS: Delegate to QueueManager
    # ============================================================================
    
    def add_couple(self, couple_id: str, name: str) -> None:
        """Add couple to queue. Delegates to queue_manager."""
        self.queue_manager.add_to_queue('couples', couple_id, name)
        logger.info(f"Added couple {couple_id} ({name}) to queue")
    
    def add_single(self, single_id: str, name: str) -> None:
        """Add single player to queue. Delegates to queue_manager."""
        self.queue_manager.add_to_queue('singles', single_id, name)
        logger.info(f"Added single {single_id} ({name}) to queue")
    
    def add_couple2(self, couple_id: str, name: str) -> None:
        """Add couple 2 to queue. Delegates to queue_manager."""
        self.queue_manager.add_to_queue('couples2', couple_id, name)
        logger.info(f"Added couple2 {couple_id} ({name}) to queue")
    
    def add_single2(self, single_id: str, name: str) -> None:
        """Add single 2 to queue. Delegates to queue_manager."""
        self.queue_manager.add_to_queue('singles2', single_id, name)
        logger.info(f"Added single2 {single_id} ({name}) to queue")
    
    def add_charlie_player(self, player_id: str, name: str) -> None:
        """Add Charlie player to queue. Delegates to queue_manager."""
        success = self.queue_manager.add_to_queue('charlie', player_id, name)
        if success and not self.next_player_charlie_id and not self.next_player_charlie_locked:
            self.next_player_charlie_id = player_id
            self.next_player_charlie_name = name
            self.next_player_charlie_locked = True
        logger.info(f"Added charlie player {player_id} ({name}) to queue")
    
    def add_statico_player(self, player_id: str, name: str) -> None:
        """Add Statico player to queue. Delegates to queue_manager."""
        success = self.queue_manager.add_to_queue('statico', player_id, name)
        if success and not self.next_player_statico_id and not self.next_player_statico_locked:
            self.next_player_statico_id = player_id
            self.next_player_statico_name = name
            self.next_player_statico_locked = True
        logger.info(f"Added statico player {player_id} ({name}) to queue")
    
    def skip_player(self, player_id: str) -> None:
        """Skip a player. Delegates to queue_manager and updates next player."""
        self.queue_manager.skip_player(player_id)
        
        # Update next player if needed
        if self.next_player_alfa_bravo_id == player_id:
            self.update_next_player()
        elif self.next_player_alfa_bravo_id2 == player_id:
            self.update_next_player2()
        elif self.next_player_charlie_id == player_id:
            self.update_next_charlie_player()
        elif self.next_player_statico_id == player_id:
            if self.queue_statico:
                self.next_player_statico_id = self.queue_statico[0]['id']
                self.next_player_statico_name = self.get_player_name(self.next_player_statico_id)
                self.next_player_statico_locked = True
            else:
                self.next_player_statico_id = None
                self.next_player_statico_name = None
                self.next_player_statico_locked = False
        
        logger.info(f"Skipped player {player_id}")
    
    def skip_player2(self, player_id: str) -> None:
        """Skip a player from track 2."""
        # Find and skip in appropriate queue
        player = next((c for c in self.queue_couples2 if c['id'] == player_id), None)
        if player:
            self.queue_manager.remove_from_queue('couples2', player_id)
            self.queue_manager.skipped_couples2.append(player)
            if self.queue_couples2:
                self.next_player_alfa_bravo_id2 = self.queue_couples2[0]['id']
                self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2)
                self.next_player_alfa_bravo_locked2 = True
            else:
                self.next_player_alfa_bravo_id2 = None
                self.next_player_alfa_bravo_name2 = None
                self.next_player_alfa_bravo_locked2 = False
        else:
            player = next((s for s in self.queue_singles2 if s['id'] == player_id), None)
            if player:
                self.queue_manager.remove_from_queue('singles2', player_id)
                self.queue_manager.skipped_singles2.append(player)
                if self.queue_singles2:
                    self.next_player_alfa_bravo_id2 = self.queue_singles2[0]['id']
                    self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2)
                    self.next_player_alfa_bravo_locked2 = True
                elif self.queue_couples2:
                    self.next_player_alfa_bravo_id2 = self.queue_couples2[0]['id']
                    self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2)
                    self.next_player_alfa_bravo_locked2 = True
                else:
                    self.next_player_alfa_bravo_id2 = None
                    self.next_player_alfa_bravo_name2 = None
                    self.next_player_alfa_bravo_locked2 = False
    
    def skip_charlie_player(self, player_id: str) -> None:
        """Skip a Charlie player."""
        player = next((p for p in self.queue_charlie if p['id'] == player_id), None)
        if player:
            self.queue_manager.remove_from_queue('charlie', player_id)
            self.queue_manager.skipped_charlie.append(player)
            if self.queue_charlie:
                self.next_player_charlie_id = self.queue_charlie[0]['id']
                self.next_player_charlie_name = self.get_player_name(self.next_player_charlie_id)
                self.next_player_charlie_locked = True
            else:
                self.next_player_charlie_id = None
                self.next_player_charlie_name = None
                self.next_player_charlie_locked = False
    
    def skip_statico_player(self, player_id: str) -> None:
        """Skip a Statico player."""
        player = next((p for p in self.queue_statico if p['id'] == player_id), None)
        if player:
            self.queue_manager.remove_from_queue('statico', player_id)
            self.queue_manager.skipped_statico.append(player)
            if self.queue_statico:
                self.next_player_statico_id = self.queue_statico[0]['id']
                self.next_player_statico_name = self.get_player_name(self.next_player_statico_id)
                self.next_player_statico_locked = True
            else:
                self.next_player_statico_id = None
                self.next_player_statico_name = None
                self.next_player_statico_locked = False
    
    def restore_skipped(self, player_id: str) -> None:
        """Restore a skipped player to their queue."""
        self.queue_manager.restore_skipped(player_id, as_next=False)
        logger.info(f"Restored skipped player {player_id}")
    
    def restore_skipped_as_next(self, player_id: str) -> None:
        """Restore a skipped player as next in queue."""
        self.queue_manager.restore_skipped(player_id, as_next=True)
        
        # Update next player tracking
        if any(p['id'] == player_id for p in self.queue_couples):
            self.next_player_alfa_bravo_id = player_id
            self.next_player_alfa_bravo_name = self.get_player_name(player_id)
            self.next_player_alfa_bravo_locked = True
        elif any(p['id'] == player_id for p in self.queue_singles):
            self.next_player_alfa_bravo_id = player_id
            self.next_player_alfa_bravo_name = self.get_player_name(player_id)
            self.next_player_alfa_bravo_locked = True
        elif any(p['id'] == player_id for p in self.queue_couples2):
            self.next_player_alfa_bravo_id2 = player_id
            self.next_player_alfa_bravo_name2 = self.get_player_name(player_id)
            self.next_player_alfa_bravo_locked2 = True
        elif any(p['id'] == player_id for p in self.queue_singles2):
            self.next_player_alfa_bravo_id2 = player_id
            self.next_player_alfa_bravo_name2 = self.get_player_name(player_id)
            self.next_player_alfa_bravo_locked2 = True
        elif any(p['id'] == player_id for p in self.queue_charlie):
            self.next_player_charlie_id = player_id
            self.next_player_charlie_name = self.get_player_name(player_id)
            self.next_player_charlie_locked = True
        elif any(p['id'] == player_id for p in self.queue_statico):
            self.next_player_statico_id = player_id
            self.next_player_statico_name = self.get_player_name(player_id)
            self.next_player_statico_locked = True
        
        logger.info(f"Restored player {player_id} as next")
    
    def delete_player(self, player_id: str) -> None:
        """Delete a player from all queues."""
        self.queue_manager.delete_player(player_id)
        
        # Update next player tracking if necessary
        if self.next_player_alfa_bravo_id == player_id:
            self.next_player_alfa_bravo_id = None
            self.next_player_alfa_bravo_name = None
            self.next_player_alfa_bravo_locked = False
            self.update_next_player()
        
        if self.next_player_alfa_bravo_id2 == player_id:
            self.next_player_alfa_bravo_id2 = None
            self.next_player_alfa_bravo_name2 = None
            self.next_player_alfa_bravo_locked2 = False
            self.update_next_player2()
        
        if self.next_player_charlie_id == player_id:
            self.next_player_charlie_id = None
            self.next_player_charlie_name = None
            self.next_player_charlie_locked = False
            self.update_next_charlie_player()
        
        if self.next_player_statico_id == player_id:
            self.next_player_statico_id = None
            self.next_player_statico_name = None
            self.next_player_statico_locked = False
        
        logger.info(f"Deleted player {player_id}")
    
    def get_player_name(self, player_id: Optional[str]) -> str:
        """Get player name by ID."""
        if player_id is None:
            return "N/D"
        return self.player_names.get(player_id, player_id)
    
    # ============================================================================
    # GAME RECORDING: Delegate to TimingManager
    # ============================================================================
    
    def record_couple_game(self, timer_duration: float, official_score: float) -> None:
        """Record couple game timing."""
        if not self.current_player_couple:
            logger.warning("record_couple_game called but no couple is playing")
            return
        
        player_id = self.current_player_couple['id']
        self.timing_manager.record_couple_game(player_id, timer_duration, official_score, track_set=1)
        
        # Update track manager
        self.track_manager.record_player_duration(player_id, official_score)
        
        # Reset state
        self.current_player_couple = None
        self.current_player_bravo = None
        self.couple_in_bravo = False
        self.third_button_pressed = False
        
        # Update averages and next player
        self.timing_manager.update_averages()
        self.update_next_player()
        
        logger.info(f"Recorded couple game for {player_id}")
    
    def record_single_game(self, timer_duration: float, official_score: float) -> None:
        """Record single game timing."""
        if not self.current_player_alfa or not self.current_player_alfa.get('id', '').startswith("BLU"):
            logger.warning("record_single_game called but no BLU player in ALFA")
            return
        
        player_id = self.current_player_alfa['id']
        self.timing_manager.record_single_game(player_id, timer_duration, official_score, track_set=1)
        
        # Update track manager
        self.track_manager.record_player_duration(player_id, official_score)
        
        # Reset state
        self.current_player_alfa = None
        self.single_in_alfa = False
        
        # Update averages and next player
        self.timing_manager.update_averages()
        self.update_next_player()
        
        logger.info(f"Recorded single game for {player_id}")
    
    def record_couple2_game(self, timer_duration: float, official_score: float) -> None:
        """Record couple 2 game timing."""
        if not self.current_player_couple2:
            logger.warning("record_couple2_game called but no couple2 is playing")
            return
        
        player_id = self.current_player_couple2['id']
        self.timing_manager.record_couple_game(player_id, timer_duration, official_score, track_set=2)
        
        # Update track manager
        self.track_manager.record_player_duration(player_id, official_score)
        
        # Reset state
        self.current_player_couple2 = None
        self.current_player_bravo2 = None
        self.couple_in_bravo2 = False
        self.third_button_pressed2 = False
        
        # Update averages and next player
        self.timing_manager.update_averages()
        self.update_next_player2()
        
        logger.info(f"Recorded couple2 game for {player_id}")
    
    def record_single2_game(self, timer_duration: float, official_score: float) -> None:
        """Record single 2 game timing."""
        if not self.current_player_alfa2:
            logger.warning("record_single2_game called but no player in ALFA2")
            return
        
        player_id = self.current_player_alfa2['id']
        self.timing_manager.record_single_game(player_id, timer_duration, official_score, track_set=2)
        
        # Update track manager
        self.track_manager.record_player_duration(player_id, official_score)
        
        # Reset state
        self.current_player_alfa2 = None
        self.single_in_alfa2 = False
        
        # Update averages and next player
        self.timing_manager.update_averages()
        self.update_next_player2()
        
        logger.info(f"Recorded single2 game for {player_id}")
    
    def record_charlie_game(self, timer_duration: float) -> None:
        """Record Charlie game timing."""
        if not self.current_player_charlie:
            logger.warning("record_charlie_game called but no charlie player")
            return
        
        player_id = self.current_player_charlie['id']
        self.timing_manager.record_charlie_game(player_id, timer_duration)
        
        # Clean up
        self.current_player_charlie = None
        self.player_in_charlie = False
        self.track_manager.player_start_times.pop(player_id, None)
        self.track_manager.player_durations.pop(player_id, None)
        
        # Update averages and next player
        self.timing_manager.update_averages()
        self.update_next_charlie_player()
        
        logger.info(f"Recorded charlie game for {player_id}")
    
    def record_statico_game(self, game_time: float, pista: str) -> None:
        """Record Statico game timing."""
        if pista == 'delta' and self.current_player_delta:
            player_id = self.current_player_delta['id']
            self.timing_manager.record_statico_game(player_id, game_time)
            self.timing_manager.update_averages()
            self.track_manager.player_start_times.pop(player_id, None)
            self.current_player_delta = None
            logger.info(f"Recorded statico game for {player_id} on delta")
        elif pista == 'echo' and self.current_player_echo:
            player_id = self.current_player_echo['id']
            self.timing_manager.record_statico_game(player_id, game_time)
            self.timing_manager.update_averages()
            self.track_manager.player_start_times.pop(player_id, None)
            self.current_player_echo = None
            logger.info(f"Recorded statico game for {player_id} on echo")
    
    # ============================================================================
    # GAME STARTING: Coordinate between managers
    # ============================================================================
    
    def start_game(self, is_couple: bool) -> None:
        """
        Start a game on track set 1.

        LOGICA CORRETTA:
        - Se coppia: Occupa sia Alfa che Bravo
        - Se singolo: Occupa solo Alfa
        - Usa update_next_player() per determinare il prossimo in coda
        """
        now = date.get_current_time()
        
        if is_couple:
            if not self.queue_couples:
                raise QueueError("No couples in queue to start the game")
            
            self.current_player_couple = self.queue_couples.pop(0)
            self.ALFA_next_available = now + datetime.timedelta(minutes=self.T_mid)
            self.BRAVO_next_available = now + datetime.timedelta(minutes=self.T_total)
            self.current_player_alfa = self.current_player_couple
            self.current_player_bravo = self.current_player_couple
            self.couple_in_alfa = True
            self.couple_in_bravo = True
            self.player_start_times[self.current_player_couple['id']] = now
            
            logger.info(f"Started couple game for {self.current_player_couple['id']}")

            # Usa la logica corretta per determinare il prossimo giocatore
            self.update_next_player()
        else:
            if not self.queue_singles:
                raise QueueError("No singles in queue to start the game")
            
            self.current_player_alfa = self.queue_singles.pop(0)
            self.single_in_alfa = True
            self.ALFA_next_available = now + datetime.timedelta(minutes=self.T_single)
            self.player_start_times[self.current_player_alfa['id']] = now
            
            logger.info(f"Started single game for {self.current_player_alfa['id']}")

            # Usa la logica corretta per determinare il prossimo giocatore
            self.update_next_player()

    def start_game2(self, is_couple: bool) -> None:
        """
        Start a game on track set 2.

        LOGICA CORRETTA:
        - Se coppia: Occupa sia Alfa2 che Bravo2
        - Se singolo: Occupa solo Alfa2
        - Usa update_next_player2() per determinare il prossimo in coda
        """
        now = date.get_current_time()
        
        if is_couple:
            if not self.queue_couples2:
                raise QueueError("No couples2 in queue to start the game")
            
            self.current_player_couple2 = self.queue_couples2.pop(0)
            self.ALFA_next_available2 = now + datetime.timedelta(minutes=self.T_mid)
            self.BRAVO_next_available2 = now + datetime.timedelta(minutes=self.T_total)
            self.current_player_alfa2 = self.current_player_couple2
            self.current_player_bravo2 = self.current_player_couple2
            self.couple_in_alfa2 = True
            self.couple_in_bravo2 = True
            self.player_start_times[self.current_player_couple2['id']] = now
            
            logger.info(f"Started couple2 game for {self.current_player_couple2['id']}")

            # Usa la logica corretta per determinare il prossimo giocatore
            self.update_next_player2()
        else:
            if not self.queue_singles2:
                raise QueueError("No singles2 in queue to start the game")
            
            self.current_player_alfa2 = self.queue_singles2.pop(0)
            self.single_in_alfa2 = True
            self.ALFA_next_available2 = now + datetime.timedelta(minutes=self.T_single)
            self.player_start_times[self.current_player_alfa2['id']] = now
            
            logger.info(f"Started single2 game for {self.current_player_alfa2['id']}")

            # Usa la logica corretta per determinare il prossimo giocatore
            self.update_next_player2()

    def start_charlie_game(self) -> None:
        """Start a game on Charlie track."""
        if not self.next_player_charlie_id:
            raise QueueError("No charlie player available to start")
        
        self.current_player_charlie = {'id': self.next_player_charlie_id, 'arrival': date.get_current_time()}
        self.CHARLIE_next_available = date.get_current_time() + datetime.timedelta(minutes=self.T_charlie)
        self.player_start_times[self.current_player_charlie['id']] = date.get_current_time()
        self.player_in_charlie = True
        
        # Remove from queue using queue_manager
        self.queue_manager.remove_from_queue('charlie', self.next_player_charlie_id)

        # Update next player
        if self.queue_charlie:
            self.next_player_charlie_id = self.queue_charlie[0]['id']
            self.next_player_charlie_name = self.get_player_name(self.next_player_charlie_id)
            self.next_player_charlie_locked = True
        else:
            self.next_player_charlie_id = None
            self.next_player_charlie_name = None
            self.next_player_charlie_locked = False
        
        logger.info(f"Started charlie game for {self.current_player_charlie['id']}")
    
    def start_statico_game(self, pista: str) -> None:
        """Start a game on Statico track."""
        if not self.queue_statico:
            raise QueueError("No statico players in queue")
        
        # Get first player from queue
        first_player = self.queue_statico[0]
        player_id = first_player['id']

        if pista == 'delta' and not self.current_player_delta:
            self.current_player_delta = {
                'id': player_id,
                'arrival': date.get_current_time()
            }
            self.DELTA_next_available = date.get_current_time() + datetime.timedelta(minutes=self.T_statico)
            self.player_start_times[player_id] = date.get_current_time()

            # Remove from queue using queue_manager
            self.queue_manager.remove_from_queue('statico', player_id)

            logger.info(f"Started statico game on delta for {player_id}")
        elif pista == 'echo' and not self.current_player_echo:
            self.current_player_echo = {
                'id': player_id,
                'arrival': date.get_current_time()
            }
            self.ECHO_next_available = date.get_current_time() + datetime.timedelta(minutes=self.T_statico)
            self.player_start_times[player_id] = date.get_current_time()

            # Remove from queue using queue_manager
            self.queue_manager.remove_from_queue('statico', player_id)

            logger.info(f"Started statico game on echo for {player_id}")

        # Update next player
        if self.queue_statico:
            self.next_player_statico_id = self.queue_statico[0]['id']
            self.next_player_statico_name = self.get_player_name(self.next_player_statico_id)
            self.next_player_statico_locked = True
        else:
            self.next_player_statico_id = None
            self.next_player_statico_name = None
            self.next_player_statico_locked = False
    
    # ============================================================================
    # BUTTON HANDLING
    # ============================================================================
    
    def button_third_pressed(self) -> None:
        """Handle third button press for couple track 1."""
        now = date.get_current_time()
        logger.debug(f"[Button Third 1] Pressed at {now.isoformat()}")
        
        if self.current_player_alfa and self.current_player_alfa.get("id", "").startswith("GIALLO"):
            player_id = self.current_player_alfa['id']
            player_name = self.get_player_name(player_id)
            logger.info(f"[Button Third 1] Processing for couple: {player_id} ({player_name})")
            
            start_time = self.player_start_times.get(player_id)
            
            if start_time:
                mid_duration_minutes = (now - start_time).total_seconds() / 60.0
                logger.debug(f"[Button Third 1 {player_id}] Mid duration: {mid_duration_minutes:.4f} min")
                
                # Record mid time
                self.timing_manager.record_mid_time(mid_duration_minutes, track_set=1)
                
                # Save to database
                try:
                    sqlite_lock = Lock()
                    with sqlite_lock:
                        conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO mid_times (couple_type, mid_duration_minutes) VALUES (?, ?)",
                            ("couple1", mid_duration_minutes)
                        )
                        conn.commit()
                        conn.close()
                    logger.info(f"[Button Third 1] Mid time saved to DB for {player_id}")
                except Exception as e:
                    logger.error(f"[Button Third 1] DB save failed for {player_id}: {e}", exc_info=True)
            else:
                logger.error(f"[Button Third 1 {player_id}] Start time not found!")
            
            # Update state
            self.third_button_pressed = True
            self.couple_in_alfa = False
            self.current_player_alfa = None
            self.update_next_player()
            logger.info(f"[Button Third 1 {player_id}] Alfa track freed")
        else:
            current_id = self.current_player_alfa.get("id", "None") if self.current_player_alfa else "None"
            logger.warning(f"[Button Third 1] No GIALLO couple in ALFA. Current: {current_id}")
    
    def button_third_pressed2(self) -> None:
        """Handle third button press for couple track 2."""
        now = date.get_current_time()
        logger.debug(f"[Button Third 2] Pressed at {now.isoformat()}")
        
        if self.current_player_alfa2 and self.current_player_alfa2.get("id", "").startswith("ROSA"):
            player_id = self.current_player_alfa2['id']
            player_name = self.get_player_name(player_id)
            logger.info(f"[Button Third 2] Processing for couple2: {player_id} ({player_name})")
            
            start_time = self.player_start_times.get(player_id)
            
            if start_time:
                mid2_duration_minutes = (now - start_time).total_seconds() / 60.0
                logger.debug(f"[Button Third 2 {player_id}] Mid2 duration: {mid2_duration_minutes:.4f} min")
                
                # Record mid time
                self.timing_manager.record_mid_time(mid2_duration_minutes, track_set=2)
                
                # Save to database
                try:
                    sqlite_lock = Lock()
                    with sqlite_lock:
                        conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO mid_times (couple_type, mid_duration_minutes) VALUES (?, ?)",
                            ("couple2", mid2_duration_minutes)
                        )
                        conn.commit()
                        conn.close()
                    logger.info(f"[Button Third 2] Mid time saved to DB for {player_id}")
                except Exception as e:
                    logger.error(f"[Button Third 2] DB save failed for {player_id}: {e}", exc_info=True)
            else:
                logger.error(f"[Button Third 2 {player_id}] Start time not found!")
            
            # Update state
            self.third_button_pressed2 = True
            self.couple_in_alfa2 = False
            self.current_player_alfa2 = None
            self.update_next_player2()
            logger.info(f"[Button Third 2 {player_id}] Alfa2 track freed")
        else:
            current_id = self.current_player_alfa2.get("id", "None") if self.current_player_alfa2 else "None"
            logger.warning(f"[Button Third 2] No ROSA couple in ALFA2. Current: {current_id}")
    
    def can_stop_couple(self) -> bool:
        """Check if couple can stop on track 1."""
        return (
            self.third_button_pressed and
            self.current_player_bravo is not None and
            self.current_player_bravo.get("id", "").startswith("GIALLO") and
            self.current_player_couple is not None and
            self.current_player_couple.get("id", "") == self.current_player_bravo.get("id", "")
        )
    
    def can_stop_couple2(self) -> bool:
        """Check if couple can stop on track 2."""
        return (
            self.third_button_pressed2 and
            self.current_player_bravo2 is not None and
            self.current_player_bravo2.get("id", "").startswith("ROSA") and
            self.current_player_couple2 is not None and
            self.current_player_couple2.get("id", "") == self.current_player_bravo2.get("id", "")
        )
    
    # ============================================================================
    # NEXT PLAYER MANAGEMENT
    # ============================================================================
    
    def update_next_player(self) -> None:
        """
        Update next player for track set 1 based on track availability.

        LOGICA CORRETTA per evitare mescolamento code:
        1. Entrambe libere → Priorità COPPIE, poi SINGOLI
        2. Solo Alfa libera (Bravo occupata) → Solo SINGOLI (non possono entrare coppie)
        3. Solo Alfa occupata → Aspetta che si liberi, mostra prossima COPPIA o SINGOLO
        4. Entrambe occupate → Aspetta, mostra prossima COPPIA o SINGOLO
        """
        logger.debug(
            f"[UpdateNextPlayer1] Start. Alfa: {self.current_player_alfa is not None}, "
            f"Bravo: {self.current_player_bravo is not None}"
        )
        
        next_id = None
        next_name = None
        locked = False
        
        # Case 1: Entrambe le piste sono libere
        if self.current_player_alfa is None and self.current_player_bravo is None:
            logger.debug("[UpdateNextPlayer1] Case 1: Both Free - Priority COUPLES")
            # Priorità assoluta alle coppie
            if self.queue_couples:
                next_id = self.queue_couples[0]['id']
                locked = True
                logger.debug(f"[UpdateNextPlayer1] Next: COUPLE {next_id}")
            elif self.queue_singles:
                # Solo se non ci sono coppie, prendi singolo
                next_id = self.queue_singles[0]['id']
                locked = True
                logger.debug(f"[UpdateNextPlayer1] Next: SINGLE {next_id}")

        # Case 2: Solo Alfa è libera (Bravo occupata da una coppia)
        elif self.current_player_alfa is None and self.current_player_bravo is not None:
            logger.debug("[UpdateNextPlayer1] Case 2: Alfa Free, Bravo Occupied - SINGLES ONLY")
            # Solo i singoli possono entrare (le coppie hanno bisogno di entrambe le piste)
            if self.queue_singles:
                next_id = self.queue_singles[0]['id']
                locked = True
                logger.debug(f"[UpdateNextPlayer1] Next: SINGLE {next_id}")
            # NON mostrare coppie qui perché non possono entrare
            else:
                logger.debug("[UpdateNextPlayer1] No singles available, waiting for Bravo to free")

        # Case 3 & 4: Alfa è occupata (e Bravo può essere libera o occupata)
        elif self.current_player_alfa is not None:
            logger.debug("[UpdateNextPlayer1] Case 3/4: Alfa Occupied - Show next in queue")
            # Mostra il prossimo in coda, con priorità alle coppie
            if self.queue_couples:
                next_id = self.queue_couples[0]['id']
                locked = True
                logger.debug(f"[UpdateNextPlayer1] Next in queue: COUPLE {next_id}")
            elif self.queue_singles:
                next_id = self.queue_singles[0]['id']
                locked = True
                logger.debug(f"[UpdateNextPlayer1] Next in queue: SINGLE {next_id}")

        # Update state
        if next_id:
            next_name = self.get_player_name(next_id)
            logger.debug(f"[UpdateNextPlayer1] Result: {next_id} ({next_name}), Locked={locked}")
        else:
            logger.debug("[UpdateNextPlayer1] Result: No next player")
            next_name = None
            locked = False
        
        self.next_player_alfa_bravo_id = next_id
        self.next_player_alfa_bravo_name = next_name
        self.next_player_alfa_bravo_locked = locked
    
    def update_next_player2(self) -> None:
        """
        Update next player for track set 2 based on track availability.

        LOGICA CORRETTA per evitare mescolamento code:
        1. Entrambe libere → Priorità COPPIE2, poi SINGOLI2
        2. Solo Alfa2 libera (Bravo2 occupata) → Solo SINGOLI2 (non possono entrare coppie)
        3. Solo Alfa2 occupata → Aspetta che si liberi, mostra prossima COPPIA2 o SINGOLO2
        4. Entrambe occupate → Aspetta, mostra prossima COPPIA2 o SINGOLO2
        """
        logger.debug(
            f"[UpdateNextPlayer2] Start. Alfa2: {self.current_player_alfa2 is not None}, "
            f"Bravo2: {self.current_player_bravo2 is not None}"
        )
        
        next_id = None
        next_name = None
        locked = False
        
        # Case 1: Entrambe le piste sono libere
        if self.current_player_alfa2 is None and self.current_player_bravo2 is None:
            logger.debug("[UpdateNextPlayer2] Case 1: Both Free - Priority COUPLES2")
            # Priorità assoluta alle coppie
            if self.queue_couples2:
                next_id = self.queue_couples2[0]['id']
                locked = True
                logger.debug(f"[UpdateNextPlayer2] Next: COUPLE2 {next_id}")
            elif self.queue_singles2:
                # Solo se non ci sono coppie, prendi singolo
                next_id = self.queue_singles2[0]['id']
                locked = True
                logger.debug(f"[UpdateNextPlayer2] Next: SINGLE2 {next_id}")

        # Case 2: Solo Alfa2 è libera (Bravo2 occupata da una coppia)
        elif self.current_player_alfa2 is None and self.current_player_bravo2 is not None:
            logger.debug("[UpdateNextPlayer2] Case 2: Alfa2 Free, Bravo2 Occupied - SINGLES2 ONLY")
            # Solo i singoli possono entrare (le coppie hanno bisogno di entrambe le piste)
            if self.queue_singles2:
                next_id = self.queue_singles2[0]['id']
                locked = True
                logger.debug(f"[UpdateNextPlayer2] Next: SINGLE2 {next_id}")
            # NON mostrare coppie qui perché non possono entrare
            else:
                logger.debug("[UpdateNextPlayer2] No singles2 available, waiting for Bravo2 to free")

        # Case 3 & 4: Alfa2 è occupata (e Bravo2 può essere libera o occupata)
        elif self.current_player_alfa2 is not None:
            logger.debug("[UpdateNextPlayer2] Case 3/4: Alfa2 Occupied - Show next in queue")
            # Mostra il prossimo in coda, con priorità alle coppie
            if self.queue_couples2:
                next_id = self.queue_couples2[0]['id']
                locked = True
                logger.debug(f"[UpdateNextPlayer2] Next in queue: COUPLE2 {next_id}")
            elif self.queue_singles2:
                next_id = self.queue_singles2[0]['id']
                locked = True
                logger.debug(f"[UpdateNextPlayer2] Next in queue: SINGLE2 {next_id}")

        # Update state
        if next_id:
            next_name = self.get_player_name(next_id)
            logger.debug(f"[UpdateNextPlayer2] Result: {next_id} ({next_name}), Locked={locked}")
        else:
            logger.debug("[UpdateNextPlayer2] Result: No next player")
            next_name = None
            locked = False
        
        self.next_player_alfa_bravo_id2 = next_id
        self.next_player_alfa_bravo_name2 = next_name
        self.next_player_alfa_bravo_locked2 = locked
    
    def update_next_charlie_player(self):
        """Update next Charlie player."""
        if self.queue_charlie:
            self.next_player_charlie_id = self.queue_charlie[0]['id']
            self.next_player_charlie_name = self.get_player_name(self.next_player_charlie_id)
            self.next_player_charlie_locked = True
        else:
            self.next_player_charlie_id = None
            self.next_player_charlie_name = None
            self.next_player_charlie_locked = False
    
    # ============================================================================
    # TIMING & AVERAGES
    # ============================================================================
    
    def update_averages(self) -> None:
        """Update all timing averages. Delegates to timing_manager."""
        self.timing_manager.update_averages()
    
    # ============================================================================
    # LEADERBOARD
    # ============================================================================
    
    def get_leaderboard(self) -> Dict[str, List[Tuple[str, str]]]:
        """Get leaderboards for all player types."""
        def get_real_leaderboard(player_type: str, limit: int = 10) -> List[Tuple[str, str]]:
            board = []
            sqlite_lock = Lock()
            try:
                with sqlite_lock:
                    conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
                    cursor = conn.cursor()
                    cursor.execute(f"""
                        SELECT s.player_name, s.player_id, s.score FROM scoring s
                        {"JOIN qualified_players q on q.player_id = s.player_id" if os.environ.get("TREASURE_HUNT_ACTIVE") and (player_type == 'couple' or player_type == 'single') else ""}
                        WHERE s.player_type = ?
                        {"AND q.treasure_hunt_updated is not null AND q.qualification_reason is not 'Non qualificato'" if os.environ.get("TREASURE_HUNT_ACTIVE") and (player_type == 'couple' or player_type == 'single') else ""}
                        ORDER BY s.score ASC
                        LIMIT ?
                    """, (player_type, limit))
                    rows = cursor.fetchall()
                    conn.close()
                for row in rows:
                    player_name, player_id, score_minutes = row
                    display_name = player_id if player_id else player_name
                    board.append((display_name, date.format_time_into_mmss(score_minutes)))
            except Exception as e:
                logger.error(f"Error fetching leaderboard for {player_type}: {e}")
            return board
        
        return {
            'couples': get_real_leaderboard('couple'),
            'singles': get_real_leaderboard('single'),
            'charlie': get_real_leaderboard('charlie'),
            'statico': get_real_leaderboard('statico')
        }
    
    # ============================================================================
    # QUALIFICATION CHECK
    # ============================================================================
    
    def check_qualification(self, score_minutes: float, player_type: str) -> Tuple[bool, Optional[str]]:
        """Check if a score qualifies for leaderboard."""
        sqlite_lock = Lock()
        is_qualified = False
        reason = None
        db_path = os.environ.get('SQLITE_DB_PATH')
        
        logger.debug(f"[QUAL CHECK] Checking score {score_minutes} for type {player_type}")
        
        try:
            with sqlite_lock:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get top 3 qualified scores
                cursor.execute("""
                    SELECT score_minutes FROM qualified_players
                    WHERE player_type = ?
                    ORDER BY score_minutes ASC
                    LIMIT 3
                """, (player_type,))
                top_qualified_scores_result = cursor.fetchall()
                
                # Get top player today
                cursor.execute("""
                    SELECT score FROM scoring
                    WHERE player_type = ?
                    ORDER BY score ASC
                    LIMIT 1
                """, (player_type,))
                top_player_today_result = cursor.fetchall()
                
                conn.close()
            
            top_qualified_scores = [float(row[0]) for row in top_qualified_scores_result if row[0] is not None]
            top_player_today = [float(row[0]) for row in top_player_today_result if row[0] is not None]
            
            logger.debug(f"[QUAL CHECK] Top 3 qualified: {top_qualified_scores}")
            logger.debug(f"[QUAL CHECK] Top today: {top_player_today}")
            
            # Check qualification
            if len(top_qualified_scores) < 3:
                is_qualified = True
                reason = 'fills_top_3'
                logger.debug(f"[QUAL CHECK] Qualifies - fills top 3")
            elif score_minutes <= top_qualified_scores[-1]:
                if top_player_today and score_minutes <= top_player_today[0]:
                    is_qualified = True
                    reason = 'beats_current_top_3 & top_today'
                else:
                    is_qualified = True
                    reason = 'beats_current_top_3'
                logger.debug(f"[QUAL CHECK] Qualifies - beats top 3")
            elif top_player_today and score_minutes <= top_player_today[0]:
                is_qualified = True
                reason = 'top_today'
                logger.debug(f"[QUAL CHECK] Qualifies - top today")
            else:
                logger.debug(f"[QUAL CHECK] Does not qualify")
        
        except sqlite3.Error as e:
            logger.error(f"[QUAL CHECK] Database error: {e}", exc_info=True)
            return False, None
        except Exception as e:
            logger.error(f"[QUAL CHECK] General error: {e}", exc_info=True)
            return False, None
        
        logger.debug(f"[QUAL CHECK] Result: Qualified={is_qualified}, Reason={reason}")
        return is_qualified, reason
    
    # ============================================================================
    # SCHEDULING & SIMULATION
    # ============================================================================
    
    def localize_time(self, dt):
        """Ensure datetime has Rome timezone."""
        if dt.tzinfo is None:
            return self.rome_tz.localize(dt)
        return dt
    
    def calculate_blue_waiting_time(self, current_blu: int, len_giallo: int) -> float:
        """Calculate waiting time for a blue (single) player."""
        if current_blu <= len_giallo:
            N_giallo = current_blu
        else:
            N_giallo = len_giallo
        
        min_att = self.T_mid * N_giallo + self.T_single * (current_blu - 1)
        return min_att
    
    def calculate_yellow_waiting_time(
        self,
        current_giallo: int,
        len_blu: int,
        dt_total: float,
        dt_mid: float,
        dt_single: float
    ) -> float:
        """Calculate waiting time for a yellow (couple) player."""
        if dt_total <= (dt_single + dt_mid) and (current_giallo <= len_blu):
            min_att = dt_single * (current_giallo - 1) + dt_mid * (current_giallo - 1)
        elif dt_total <= (dt_single + dt_mid):
            min_att = dt_single * len_blu + dt_mid * len_blu + dt_total * (current_giallo - len_blu)
        else:
            min_att = dt_total * (current_giallo - 1)
        
        return min_att
    
    def simulate_schedule(self) -> Dict[str, datetime.datetime]:
        """Simulate schedule for track set 1."""
        now = date.get_current_time()
        estimated_times = {}
        
        len_giallo = len(self.queue_couples)
        len_blu = len(self.queue_singles)
        
        # Singles
        for current_blu, player in enumerate(self.queue_singles, 1):
            min_att = self.calculate_blue_waiting_time(current_blu, len_giallo)
            estimated_times[player['id']] = now + datetime.timedelta(minutes=min_att)
        
        # Couples
        for current_giallo, player in enumerate(self.queue_couples, 1):
            min_att = self.calculate_yellow_waiting_time(
                current_giallo, len_blu, self.T_total, self.T_mid, self.T_single
            )
            estimated_times[player['id']] = now + datetime.timedelta(minutes=min_att)
        
        return estimated_times
    
    def simulate_schedule2(self) -> Dict[str, datetime.datetime]:
        """Simulate schedule for track set 2."""
        now = date.get_current_time()
        sim_time = max(now, self.ALFA_next_available2)
        
        self.ALFA_next_available2 = self.localize_time(self.ALFA_next_available2)
        BRAVO_avail2 = self.BRAVO_next_available2 if self.BRAVO_next_available2 > sim_time else sim_time
        
        dt_mid2 = datetime.timedelta(minutes=self.T_mid2)
        dt_total2 = datetime.timedelta(minutes=self.T_total)
        dt_single2 = datetime.timedelta(minutes=self.T_single2)
        
        couples = deepcopy(self.queue_couples2)
        singles = deepcopy(self.queue_singles2)
        
        estimated_times2 = {}
        
        while couples or singles:
            if not couples and singles:
                item = singles.pop(0)
                start_time = sim_time
                estimated_times2[item['id']] = start_time
                sim_time = start_time + dt_single2
                continue
            
            if BRAVO_avail2 <= sim_time:
                if couples:
                    item = couples.pop(0)
                    start_time = sim_time
                    estimated_times2[item['id']] = start_time
                    sim_time = start_time + dt_mid2
                    BRAVO_avail2 = start_time + dt_total2
                    continue
                else:
                    if singles:
                        item = singles.pop(0)
                        start_time = sim_time
                        estimated_times2[item['id']] = start_time
                        sim_time = start_time + dt_single2
                        continue
                    else:
                        break
            else:
                if singles:
                    item = singles.pop(0)
                    start_time = sim_time
                    estimated_times2[item['id']] = start_time
                    sim_time = start_time + dt_single2
                    continue
                else:
                    sim_time = BRAVO_avail2
                    continue
        
        return estimated_times2
    
    def get_waiting_board(self) -> Tuple[
        List[Tuple[int, str, Union[datetime.datetime, str]]],
        List[Tuple[int, str, Union[datetime.datetime, str]]],
        List[Tuple[int, str, Union[datetime.datetime, str]]],
        List[Tuple[int, str, Union[datetime.datetime, str]]],
        List[Tuple[int, str, Union[datetime.datetime, str]]],
        List[Tuple[int, str, Union[datetime.datetime, str]]]
    ]:
        """Get waiting boards for all queues."""
        now = date.get_current_time()
        est1 = self.simulate_schedule()
        est2 = self.simulate_schedule2()
        
        # Update next players if not locked
        if not self.next_player_alfa_bravo_locked:
            if self.couple_in_bravo and self.single_in_alfa and self.queue_couples:
                self.next_player_alfa_bravo_id = self.queue_couples[0]['id']
                self.next_player_alfa_bravo_locked = True
            else:
                next_player_found = False
                for queue_item in self.queue_couples + self.queue_singles:
                    estimated_time = est1.get(queue_item['id'])
                    if estimated_time:
                        minutes_to_entry = (estimated_time - now).total_seconds() / 60
                        if minutes_to_entry <= 2 or not next_player_found:
                            self.next_player_alfa_bravo_id = queue_item['id']
                            self.next_player_alfa_bravo_name = self.get_player_name(self.next_player_alfa_bravo_id)
                            self.next_player_alfa_bravo_locked = True
                            next_player_found = True
                            if minutes_to_entry <= 2:
                                break
        
        if not self.next_player_alfa_bravo_locked2:
            if self.couple_in_bravo2 and self.single_in_alfa2 and self.queue_couples2:
                self.next_player_alfa_bravo_id2 = self.queue_couples2[0]['id']
                self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2)
                self.next_player_alfa_bravo_locked2 = True
            else:
                next_player_found2 = False
                for queue_item in self.queue_couples2 + self.queue_singles2:
                    estimated_time2 = est2.get(queue_item['id'])
                    if estimated_time2:
                        minutes_to_entry2 = (estimated_time2 - now).total_seconds() / 60
                        if minutes_to_entry2 <= 2 or not next_player_found2:
                            self.next_player_alfa_bravo_id2 = queue_item['id']
                            self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2)
                            self.next_player_alfa_bravo_locked2 = True
                            next_player_found2 = True
                            if minutes_to_entry2 <= 2:
                                break
        
        # Build boards
        couples_board = []
        for idx, item in enumerate(self.queue_couples):
            estimated = est1.get(item['id'], "N/D")
            display_time = "PROSSIMO INGRESSO" if item['id'] == self.next_player_alfa_bravo_id else estimated
            couples_board.append((idx + 1, item['id'], display_time))
        
        singles_board = []
        for idx, item in enumerate(self.queue_singles):
            estimated = est1.get(item['id'], "N/D")
            display_time = "PROSSIMO INGRESSO" if item['id'] == self.next_player_alfa_bravo_id else estimated
            singles_board.append((idx + 1, item['id'], display_time))
        
        couples_board2 = []
        for idx, item in enumerate(self.queue_couples2):
            estimated2 = est2.get(item['id'], "N/D")
            display_time = "PROSSIMO INGRESSO" if item['id'] == self.next_player_alfa_bravo_id2 else estimated2
            couples_board2.append((idx + 1, item['id'], display_time))
        
        singles_board2 = []
        for idx, item in enumerate(self.queue_singles2):
            estimated2 = est2.get(item['id'], "N/D")
            display_time = "PROSSIMO INGRESSO" if item['id'] == self.next_player_alfa_bravo_id2 else estimated2
            singles_board2.append((idx + 1, item['id'], display_time))
        
        # Charlie board
        charlie_board = []
        charlie_sim_time = max(now, self.localize_time(self.CHARLIE_next_available))
        for idx, item in enumerate(self.queue_charlie):
            start_time = charlie_sim_time
            display_time = "PROSSIMO INGRESSO" if item['id'] == self.next_player_charlie_id else start_time
            charlie_board.append((idx + 1, item['id'], display_time))
            charlie_sim_time = start_time + datetime.timedelta(minutes=self.T_charlie)
        
        # Statico board
        statico_board = []
        delta_avail = self.localize_time(self.DELTA_next_available)
        echo_avail = self.localize_time(self.ECHO_next_available)
        for idx, item in enumerate(self.queue_statico):
            next_avail_time = min(max(now, delta_avail), max(now, echo_avail))
            start_time = next_avail_time
            display_time = "PROSSIMO INGRESSO" if item['id'] == self.next_player_statico_id else start_time
            statico_board.append((idx + 1, item['id'], display_time))
            
            if max(now, delta_avail) <= max(now, echo_avail):
                delta_avail = start_time + datetime.timedelta(minutes=self.T_statico)
            else:
                echo_avail = start_time + datetime.timedelta(minutes=self.T_statico)
        
        return couples_board, singles_board, couples_board2, singles_board2, charlie_board, statico_board
    
    # ============================================================================
    # DURATION TRACKING
    # ============================================================================
    
    def get_durations(self) -> Dict[str, str]:
        """Get current durations for all active players formatted as MM:SS."""
        durations = {}
        now = date.get_current_time()
        
        tracks = {
            'alfa': self.current_player_alfa,
            'bravo': self.current_player_bravo,
            'alfa2': self.current_player_alfa2,
            'bravo2': self.current_player_bravo2,
            'charlie': self.current_player_charlie,
            'delta': self.current_player_delta,
            'echo': self.current_player_echo
        }
        
        for track_name, player in tracks.items():
            if player:
                player_id = player['id']
                start_time = self.player_start_times.get(player_id)
                if start_time:
                    duration_seconds = (now - start_time).total_seconds()
                    minutes = int(duration_seconds // 60)
                    seconds = int(duration_seconds % 60)
                    durations[track_name] = f"{minutes:02}:{seconds:02}"
        
        return durations
