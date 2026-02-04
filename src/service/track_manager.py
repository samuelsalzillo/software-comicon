"""
Track Manager Service.

This module manages the state of game tracks (Alfa, Bravo, Charlie, Delta, Echo)
and handles player assignments to tracks.
"""
import datetime
import logging
from typing import Optional, Dict
from ..utils import date

logger = logging.getLogger(__name__)


class TrackManager:
    """
    Manages game tracks and their availability.

    This class handles the state of all game tracks, tracking which players
    are currently on each track and when tracks become available.
    """

    def __init__(self):
        """Initialize track manager with all tracks available."""
        # Current players on tracks
        self.current_player_alfa: Optional[Dict] = None
        self.current_player_bravo: Optional[Dict] = None
        self.current_player_alfa2: Optional[Dict] = None
        self.current_player_bravo2: Optional[Dict] = None
        self.current_player_charlie: Optional[Dict] = None
        self.current_player_delta: Optional[Dict] = None
        self.current_player_echo: Optional[Dict] = None

        # Track availability times
        now = date.get_current_time()
        self.ALFA_next_available = now
        self.BRAVO_next_available = now
        self.ALFA_next_available2 = now
        self.BRAVO_next_available2 = now
        self.CHARLIE_next_available = now
        self.DELTA_next_available = now
        self.ECHO_next_available = now

        # Track state flags
        self.couple_in_alfa: bool = False
        self.couple_in_bravo: bool = False
        self.single_in_alfa: bool = False
        self.couple_in_alfa2: bool = False
        self.couple_in_bravo2: bool = False
        self.single_in_alfa2: bool = False
        self.player_in_charlie: bool = False
        self.player_in_delta: bool = False
        self.player_in_echo: bool = False

        # Couple tracking
        self.current_player_couple: Optional[Dict] = None
        self.current_player_couple2: Optional[Dict] = None

        # Third button pressed flags
        self.third_button_pressed: bool = False
        self.third_button_pressed2: bool = False

        # Player start times and durations
        self.player_start_times: Dict[str, datetime.datetime] = {}
        self.player_durations: Dict[str, float] = {}

        logger.info("TrackManager initialized")

    def assign_player_to_track(
        self,
        track_name: str,
        player: Dict,
        duration_minutes: float
    ) -> bool:
        """
        Assign a player to a track.

        Args:
            track_name: Name of the track ('alfa', 'bravo', etc.)
            player: Player dictionary with 'id' and 'arrival'
            duration_minutes: Expected duration on track

        Returns:
            True if assignment successful, False if track occupied
        """
        track_attr = f"current_player_{track_name}"
        avail_attr = f"{track_name}_next_available"

        if not hasattr(self, track_attr):
            logger.error(f"Invalid track name: {track_name}")
            return False

        current_player = getattr(self, track_attr)
        if current_player is not None:
            logger.warning(f"Track {track_name} is already occupied by {current_player.get('id')}")
            return False

        # Assign player
        setattr(self, track_attr, player)

        # Update availability
        now = date.get_current_time()
        next_available = now + datetime.timedelta(minutes=duration_minutes)
        setattr(self, avail_attr, next_available)

        # Record start time
        self.player_start_times[player['id']] = now

        logger.info(
            f"Assigned player {player['id']} to track {track_name}, "
            f"available at {next_available.strftime('%H:%M:%S')}"
        )
        return True

    def release_track(self, track_name: str) -> Optional[Dict]:
        """
        Release a player from a track.

        Args:
            track_name: Name of the track to release

        Returns:
            The player that was on the track, or None
        """
        track_attr = f"current_player_{track_name}"

        if not hasattr(self, track_attr):
            logger.error(f"Invalid track name: {track_name}")
            return None

        player = getattr(self, track_attr)
        if player is None:
            logger.warning(f"Track {track_name} is already free")
            return None

        # Release track
        setattr(self, track_attr, None)

        logger.info(f"Released player {player['id']} from track {track_name}")
        return player

    def is_track_available(self, track_name: str) -> bool:
        """
        Check if a track is currently available.

        Args:
            track_name: Name of the track

        Returns:
            True if track is free and available
        """
        track_attr = f"current_player_{track_name}"
        avail_attr = f"{track_name}_next_available"

        if not hasattr(self, track_attr):
            return False

        current_player = getattr(self, track_attr)
        if current_player is not None:
            return False

        # Check if enough time has passed
        now = date.get_current_time()
        next_available = getattr(self, avail_attr)
        return now >= next_available

    def get_track_status(self, track_name: str) -> Dict:
        """
        Get detailed status of a track.

        Args:
            track_name: Name of the track

        Returns:
            Dictionary with track status information
        """
        track_attr = f"current_player_{track_name}"
        avail_attr = f"{track_name}_next_available"

        if not hasattr(self, track_attr):
            return {'error': f'Invalid track: {track_name}'}

        current_player = getattr(self, track_attr)
        next_available = getattr(self, avail_attr)
        now = date.get_current_time()

        status = {
            'track': track_name,
            'occupied': current_player is not None,
            'available': self.is_track_available(track_name),
            'next_available': next_available.isoformat(),
        }

        if current_player:
            status['current_player'] = current_player['id']
            start_time = self.player_start_times.get(current_player['id'])
            if start_time:
                elapsed = (now - start_time).total_seconds()
                status['elapsed_seconds'] = elapsed
                status['elapsed_formatted'] = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"

        return status

    def get_all_tracks_status(self) -> Dict[str, Dict]:
        """
        Get status of all tracks.

        Returns:
            Dictionary mapping track names to their status
        """
        tracks = ['alfa', 'bravo', 'alfa2', 'bravo2', 'charlie', 'delta', 'echo']
        return {track: self.get_track_status(track) for track in tracks}

    def get_player_duration(self, player_id: str) -> Optional[float]:
        """
        Get the elapsed time for a player currently on track.

        Args:
            player_id: Player identifier

        Returns:
            Duration in minutes, or None if player not found
        """
        start_time = self.player_start_times.get(player_id)
        if start_time is None:
            return None

        now = date.get_current_time()
        duration_seconds = (now - start_time).total_seconds()
        return duration_seconds / 60.0

    def record_player_duration(self, player_id: str, duration: float) -> None:
        """
        Record the final duration for a player.

        Args:
            player_id: Player identifier
            duration: Final duration in minutes
        """
        self.player_durations[player_id] = duration

        # Clean up start time
        if player_id in self.player_start_times:
            del self.player_start_times[player_id]

        logger.info(f"Recorded duration {duration:.2f} min for player {player_id}")

    def handle_third_button(self, track_set: int = 1) -> bool:
        """
        Handle the third button press for couples.

        Args:
            track_set: 1 for Alfa/Bravo, 2 for Alfa2/Bravo2

        Returns:
            True if button press was valid
        """
        if track_set == 1:
            if self.couple_in_alfa:
                self.third_button_pressed = True
                self.couple_in_alfa = False
                logger.info("Third button pressed for track set 1")
                return True
        elif track_set == 2:
            if self.couple_in_alfa2:
                self.third_button_pressed2 = True
                self.couple_in_alfa2 = False
                logger.info("Third button pressed for track set 2")
                return True

        logger.warning(f"Invalid third button press for track set {track_set}")
        return False

    def can_stop_couple(self, track_set: int = 1) -> bool:
        """
        Check if a couple can stop their game.

        Args:
            track_set: 1 for Alfa/Bravo, 2 for Alfa2/Bravo2

        Returns:
            True if couple can stop
        """
        if track_set == 1:
            return (
                self.third_button_pressed and
                self.current_player_bravo is not None and
                self.current_player_couple is not None and
                self.current_player_couple.get('id') == self.current_player_bravo.get('id')
            )
        elif track_set == 2:
            return (
                self.third_button_pressed2 and
                self.current_player_bravo2 is not None and
                self.current_player_couple2 is not None and
                self.current_player_couple2.get('id') == self.current_player_bravo2.get('id')
            )
        return False

    def assign_couple_to_tracks(self, player: Dict, track_set: int = 1) -> None:
        """
        Assegna una coppia ad entrambe le piste (Alfa e Bravo).

        Args:
            player: Dizionario giocatore con 'id' e 'arrival'
            track_set: 1 per Alfa/Bravo, 2 per Alfa2/Bravo2
        """
        now = date.get_current_time()

        if track_set == 1:
            self.current_player_couple = player
            self.current_player_alfa = player
            self.current_player_bravo = player
            self.couple_in_alfa = True
            self.couple_in_bravo = True
            self.third_button_pressed = False
        else:
            self.current_player_couple2 = player
            self.current_player_alfa2 = player
            self.current_player_bravo2 = player
            self.couple_in_alfa2 = True
            self.couple_in_bravo2 = True
            self.third_button_pressed2 = False

        self.player_start_times[player['id']] = now
        logger.info(f"Assigned couple {player['id']} to track set {track_set}")

    def assign_single_to_alfa(self, player: Dict, track_set: int = 1) -> None:
        """
        Assegna un singolo alla pista Alfa.

        Args:
            player: Dizionario giocatore con 'id' e 'arrival'
            track_set: 1 per Alfa, 2 per Alfa2
        """
        now = date.get_current_time()

        if track_set == 1:
            self.current_player_alfa = player
            self.single_in_alfa = True
        else:
            self.current_player_alfa2 = player
            self.single_in_alfa2 = True

        self.player_start_times[player['id']] = now
        logger.info(f"Assigned single {player['id']} to Alfa{track_set if track_set > 1 else ''}")

    def assign_charlie(self, player: Dict) -> None:
        """
        Assegna un giocatore alla pista Charlie.

        Args:
            player: Dizionario giocatore con 'id' e 'arrival'
        """
        now = date.get_current_time()
        self.current_player_charlie = player
        self.player_in_charlie = True
        self.player_start_times[player['id']] = now
        logger.info(f"Assigned {player['id']} to Charlie track")

    def assign_statico(self, player: Dict, pista: str) -> None:
        """
        Assegna un giocatore alla pista Statico (Delta o Echo).

        Args:
            player: Dizionario giocatore con 'id' e 'arrival'
            pista: 'delta' o 'echo'
        """
        now = date.get_current_time()

        if pista == 'delta':
            self.current_player_delta = player
            self.player_in_delta = True
        else:
            self.current_player_echo = player
            self.player_in_echo = True

        self.player_start_times[player['id']] = now
        logger.info(f"Assigned {player['id']} to {pista.upper()} track")
