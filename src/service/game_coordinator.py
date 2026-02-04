"""
Game Coordinator Service.

Coordina la logica complessa di gioco tra QueueManager, TrackManager e TimingManager.
Sposta fuori da GameBackend tutta la logica di coordinamento complessa.
"""
import logging
import datetime
from typing import Optional, Tuple

from .queue_manager import QueueManager
from .track_manager import TrackManager
from .timing_manager import TimingManager
from ..utils import date
from ..exceptions import QueueError

logger = logging.getLogger(__name__)


class GameCoordinator:
    """
    Coordina operazioni complesse di gioco tra i manager.

    Questa classe gestisce:
    - Avvio giochi con logica di next player
    - Pressione pulsanti e transizioni di stato
    - Logiche di qualificazione
    - Update next player complessi
    """

    def __init__(
        self,
        queue_manager: QueueManager,
        track_manager: TrackManager,
        timing_manager: TimingManager
    ):
        """
        Inizializza GameCoordinator.

        Args:
            queue_manager: Gestore code
            track_manager: Gestore piste
            timing_manager: Gestore timing
        """
        self.queue_manager = queue_manager
        self.track_manager = track_manager
        self.timing_manager = timing_manager

        # Next player tracking
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

        logger.info("GameCoordinator initialized")

    # ============================================================================
    # START GAME LOGIC
    # ============================================================================

    def start_game(self, is_couple: bool, track_set: int = 1) -> None:
        """
        Avvia un gioco su un track set.

        Args:
            is_couple: True per coppia, False per singolo
            track_set: 1 o 2
        """
        now = date.get_current_time()

        if is_couple:
            self._start_couple_game(track_set, now)
        else:
            self._start_single_game(track_set, now)

        # Update next player
        self._update_next_player(track_set)

    def _start_couple_game(self, track_set: int, now: datetime.datetime) -> None:
        """Avvia gioco coppia."""
        queue_attr = 'queue_couples' if track_set == 1 else 'queue_couples2'
        queue = getattr(self.queue_manager, queue_attr)

        if not queue:
            raise QueueError(f"No couples in queue for track set {track_set}")

        # Remove from queue
        player = queue.pop(0)

        # Assign to tracks
        suffix = "" if track_set == 1 else "2"
        self.track_manager.assign_couple_to_tracks(player, track_set)

        # Set timing
        t_mid = self.timing_manager.t_mid if track_set == 1 else self.timing_manager.t_mid2
        t_total = self.timing_manager.t_total if track_set == 1 else self.timing_manager.t_total

        setattr(self.track_manager, f'ALFA_next_available{suffix}',
                now + datetime.timedelta(minutes=t_mid))
        setattr(self.track_manager, f'BRAVO_next_available{suffix}',
                now + datetime.timedelta(minutes=t_total))

        logger.info(f"Started couple game for {player['id']} on track set {track_set}")

    def _start_single_game(self, track_set: int, now: datetime.datetime) -> None:
        """Avvia gioco singolo."""
        queue_attr = 'queue_singles' if track_set == 1 else 'queue_singles2'
        queue = getattr(self.queue_manager, queue_attr)

        if not queue:
            raise QueueError(f"No singles in queue for track set {track_set}")

        # Remove from queue
        player = queue.pop(0)

        # Assign to Alfa only
        self.track_manager.assign_single_to_alfa(player, track_set)

        # Set timing
        t_single = self.timing_manager.t_single if track_set == 1 else self.timing_manager.t_single2
        suffix = "" if track_set == 1 else "2"

        setattr(self.track_manager, f'ALFA_next_available{suffix}',
                now + datetime.timedelta(minutes=t_single))

        logger.info(f"Started single game for {player['id']} on track set {track_set}")

    def start_charlie_game(self) -> None:
        """Avvia gioco Charlie."""
        if not self.next_player_charlie_id:
            raise QueueError("No charlie player available to start")

        player = {'id': self.next_player_charlie_id, 'arrival': date.get_current_time()}
        self.track_manager.assign_charlie(player)

        # Remove from queue
        self.queue_manager.remove_from_queue('charlie', self.next_player_charlie_id)

        # Set timing
        self.track_manager.CHARLIE_next_available = date.get_current_time() + datetime.timedelta(
            minutes=self.timing_manager.t_charlie
        )

        # Update next player
        self._update_next_charlie_player()

        logger.info(f"Started charlie game for {player['id']}")

    def start_statico_game(self, pista: str) -> None:
        """Avvia gioco Statico."""
        if not self.queue_manager.queue_statico:
            raise QueueError("No statico players in queue")

        first_player = self.queue_manager.queue_statico[0]
        player_id = first_player['id']

        player = {'id': player_id, 'arrival': date.get_current_time()}
        self.track_manager.assign_statico(player, pista)

        # Remove from queue
        self.queue_manager.remove_from_queue('statico', player_id)

        # Set timing
        t_statico = self.timing_manager.t_statico
        if pista == 'delta':
            self.track_manager.DELTA_next_available = date.get_current_time() + datetime.timedelta(
                minutes=t_statico
            )
        else:
            self.track_manager.ECHO_next_available = date.get_current_time() + datetime.timedelta(
                minutes=t_statico
            )

        # Update next player
        self._update_next_statico_player()

        logger.info(f"Started statico game on {pista} for {player_id}")

    # ============================================================================
    # BUTTON PRESS LOGIC
    # ============================================================================

    def button_third_pressed(self, track_set: int = 1) -> None:
        """
        Gestisce pressione terzo pulsante (mid-point coppia).

        Args:
            track_set: 1 o 2
        """
        now = date.get_current_time()
        suffix = "" if track_set == 1 else "2"
        prefix = "GIALLO" if track_set == 1 else "ROSA"

        current_player_alfa = getattr(self.track_manager, f'current_player_alfa{suffix}')

        if current_player_alfa and current_player_alfa.get("id", "").startswith(prefix):
            player_id = current_player_alfa['id']

            # Record mid time
            start_time = self.track_manager.player_start_times.get(player_id)
            if start_time:
                mid_duration = (now - start_time).total_seconds() / 60.0
                self.timing_manager.record_mid_time(mid_duration, track_set)
                logger.info(f"[Button Third {track_set}] Mid time: {mid_duration:.2f}m for {player_id}")

            # Free Alfa track
            setattr(self.track_manager, f'current_player_alfa{suffix}', None)
            setattr(self.track_manager, f'couple_in_alfa{suffix}', False)
            setattr(self.track_manager, f'third_button_pressed{suffix}', True)

            # Update next player
            self._update_next_player(track_set)

            logger.info(f"[Button Third {track_set}] Alfa track freed for {player_id}")
        else:
            logger.warning(f"[Button Third {track_set}] No {prefix} couple in ALFA")

    def can_stop_couple(self, track_set: int = 1) -> bool:
        """
        Verifica se la coppia può fermarsi.

        Args:
            track_set: 1 o 2

        Returns:
            True se può fermarsi, False altrimenti
        """
        suffix = "" if track_set == 1 else "2"
        third_pressed = getattr(self.track_manager, f'third_button_pressed{suffix}', False)
        current_bravo = getattr(self.track_manager, f'current_player_bravo{suffix}')

        return third_pressed and current_bravo is not None

    # ============================================================================
    # UPDATE NEXT PLAYER LOGIC
    # ============================================================================

    def _update_next_player(self, track_set: int = 1) -> None:
        """
        Aggiorna il prossimo giocatore per un track set.

        Logica corretta:
        1. Entrambe libere → Priorità COPPIE, poi SINGOLI
        2. Solo Alfa libera (Bravo occupata) → Solo SINGOLI
        3. Alfa occupata → Mostra prossimo in coda
        """
        suffix = "" if track_set == 1 else "2"

        current_alfa = getattr(self.track_manager, f'current_player_alfa{suffix}')
        current_bravo = getattr(self.track_manager, f'current_player_bravo{suffix}')

        queue_couples = self.queue_manager.queue_couples if track_set == 1 else self.queue_manager.queue_couples2
        queue_singles = self.queue_manager.queue_singles if track_set == 1 else self.queue_manager.queue_singles2

        next_id = None
        next_name = None
        locked = False

        if current_alfa is None and current_bravo is None:
            # Entrambe libere: priorità coppie
            if queue_couples:
                next_id = queue_couples[0]['id']
                locked = True
            elif queue_singles:
                next_id = queue_singles[0]['id']
                locked = True

        elif current_alfa is None and current_bravo is not None:
            # Solo Alfa libera: solo singoli possono entrare
            if queue_singles:
                next_id = queue_singles[0]['id']
                locked = True

        elif current_alfa is not None:
            # Alfa occupata: mostra prossimo in coda
            if queue_couples:
                next_id = queue_couples[0]['id']
                locked = True
            elif queue_singles:
                next_id = queue_singles[0]['id']
                locked = True

        # Update state
        if next_id:
            next_name = self.queue_manager.player_names.get(next_id, next_id)

        if track_set == 1:
            self.next_player_alfa_bravo_id = next_id
            self.next_player_alfa_bravo_name = next_name
            self.next_player_alfa_bravo_locked = locked
        else:
            self.next_player_alfa_bravo_id2 = next_id
            self.next_player_alfa_bravo_name2 = next_name
            self.next_player_alfa_bravo_locked2 = locked

        logger.debug(f"[UpdateNextPlayer{track_set}] Next: {next_id}, Locked: {locked}")

    def _update_next_charlie_player(self) -> None:
        """Aggiorna prossimo giocatore Charlie."""
        if self.queue_manager.queue_charlie:
            self.next_player_charlie_id = self.queue_manager.queue_charlie[0]['id']
            self.next_player_charlie_name = self.queue_manager.player_names.get(
                self.next_player_charlie_id,
                self.next_player_charlie_id
            )
            self.next_player_charlie_locked = True
        else:
            self.next_player_charlie_id = None
            self.next_player_charlie_name = None
            self.next_player_charlie_locked = False

    def _update_next_statico_player(self) -> None:
        """Aggiorna prossimo giocatore Statico."""
        if self.queue_manager.queue_statico:
            self.next_player_statico_id = self.queue_manager.queue_statico[0]['id']
            self.next_player_statico_name = self.queue_manager.player_names.get(
                self.next_player_statico_id,
                self.next_player_statico_id
            )
            self.next_player_statico_locked = True
        else:
            self.next_player_statico_id = None
            self.next_player_statico_name = None
            self.next_player_statico_locked = False

    # ============================================================================
    # QUALIFICATION LOGIC
    # ============================================================================

    def check_qualification(self, score: float, player_type: str) -> Tuple[bool, Optional[str]]:
        """
        Verifica se un giocatore si qualifica.

        Args:
            score: Punteggio del giocatore (in minuti)
            player_type: Tipo giocatore ('couple', 'single', 'charlie')

        Returns:
            Tuple (is_qualified, reason)
        """
        # Ottieni tempo di riferimento
        if player_type == 'couple':
            reference_time = self.timing_manager.t_total
        elif player_type == 'single':
            reference_time = self.timing_manager.t_single
        elif player_type == 'charlie':
            reference_time = self.timing_manager.t_charlie
        else:
            return False, None

        # Verifica qualificazione
        if score <= reference_time:
            reason = f"Completato in {score:.2f}m (limite: {reference_time:.2f}m)"
            return True, reason
        else:
            return False, None
