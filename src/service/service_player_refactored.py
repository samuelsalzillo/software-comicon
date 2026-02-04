"""
Player Service - Refactored with OOP Pattern.

This module provides a service class for all player-related operations,
including contact management, game simulation, button handling, and player actions.
"""
import logging
import os
import sqlite3
from typing import Dict, Optional, Tuple, Any

from flask import request, jsonify, url_for

from ..utils.database import get_lock, execute_with_retry
from ..utils import date
from ..utils.model import get_game_backend, set_game_backend
from ..service import service_game_backend
from ..model.GameBackend import GameBackend
from ..exceptions import ValidationError, PlayerNotFoundError, QueueError
from ..config import PlayerType

logger = logging.getLogger(__name__)


class PlayerService:
    """
    Service for handling player-related operations.

    This class encapsulates all business logic related to players,
    including contact management, simulation, button handling, and actions.
    """

    def __init__(self, backend: Optional[GameBackend] = None):
        """
        Initialize PlayerService.

        Args:
            backend: GameBackend instance. If None, will get from utils.
        """
        self.backend = backend or get_game_backend()
        logger.info("PlayerService initialized")

    # ============================================================================
    # CONTACT MANAGEMENT
    # ============================================================================

    def save_contact_info(self, data: Dict[str, Any]) -> Tuple[Dict, int]:
        """
        Save player contact information to qualified_players table.

        Args:
            data: Dictionary with contact information

        Returns:
            Tuple of (response dict, status code)
        """
        logger.debug(f"Saving contact info: {data}")

        # Extract and validate data
        try:
            contact_data = self._extract_contact_data(data)
        except ValidationError as e:
            logger.warning(f"Contact validation failed: {e}")
            return {'success': False, 'message': str(e)}, 400

        # Save to database
        try:
            self._save_contact_to_db(contact_data)
            logger.info(f"[CONTACT SAVE] Success for {contact_data['player_id']}")
            return {'success': True, 'message': 'Dati di contatto salvati con successo!'}, 200
        except Exception as e:
            logger.error(f"[CONTACT SAVE] Failed: {e}", exc_info=True)
            return {'success': False, 'message': f'Errore DB: {e}'}, 500

    def _extract_contact_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and validate contact data from request.

        Args:
            data: Raw request data

        Returns:
            Validated contact data dictionary

        Raises:
            ValidationError: If data is invalid or incomplete
        """
        required_fields = [
            'player_id', 'player_name', 'first_name', 'last_name',
            'phone_number', 'score_minutes', 'player_type', 'qualification_reason'
        ]

        # Check all required fields
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            raise ValidationError(
                'contact_data',
                f"Campi mancanti: {', '.join(missing)}"
            )

        # Validate and normalize score
        try:
            score_float = float(data['score_minutes'])
        except (ValueError, TypeError):
            raise ValidationError('score_minutes', 'Formato punteggio non valido')

        # Normalize player type
        player_type = data['player_type'].lower()
        if player_type in ('couple2', 'single2'):
            player_type = player_type[:-1]

        if player_type not in ('couple', 'single', 'charlie'):
            raise ValidationError('player_type', f'Tipo giocatore non valido: {player_type}')

        return {
            'player_id': data['player_id'],
            'player_name': data['player_name'],
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'phone_number': data['phone_number'],
            'score_float': score_float,
            'score_formatted': date.format_time_into_mmss(score_float),
            'player_type': player_type,
            'qualification_reason': data['qualification_reason'],
            'qualification_date': date.get_current_time().strftime('%Y-%m-%d'),
            'timestamp': date.get_current_time()
        }

    def _save_contact_to_db(self, contact_data: Dict[str, Any]) -> None:
        """
        Save contact data to database.

        Args:
            contact_data: Validated contact data

        Raises:
            Exception: If database operation fails
        """
        sqlite_lock = get_lock()

        with sqlite_lock:
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
            cursor = conn.cursor()

            logger.info(
                f"[CONTACT SAVE] ID={contact_data['player_id']}, "
                f"Contact={contact_data['first_name']} {contact_data['last_name']}, "
                f"Score={contact_data['score_formatted']}"
            )

            execute_with_retry(
                cursor,
                """
                INSERT INTO qualified_players
                (player_id, player_name, first_name, last_name, phone_number, 
                 score_minutes, score_formatted, player_type, qualification_reason, 
                 qualification_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    contact_data['player_id'],
                    contact_data['player_name'],
                    contact_data['first_name'],
                    contact_data['last_name'],
                    contact_data['phone_number'],
                    contact_data['score_float'],
                    contact_data['score_formatted'],
                    contact_data['player_type'],
                    contact_data['qualification_reason'],
                    contact_data['qualification_date'],
                    contact_data['timestamp']
                )
            )
            conn.commit()
            conn.close()

    # ============================================================================
    # GAME SIMULATION & STATUS
    # ============================================================================

    def simulate_player_status(self) -> Dict:
        """
        Get complete player and game status for frontend.

        Returns:
            Dictionary with all game status information
        """
        # Get waiting boards
        boards = self.backend.get_waiting_board()
        couples_board, singles_board, couples2_board, singles2_board, charlie_board, statico_board = boards

        # Get durations
        durations = self.backend.get_durations()

        # Format boards with player names
        formatted_boards = {
            'couples': service_game_backend.format_list(couples_board, self.backend.player_names),
            'singles': service_game_backend.format_list(singles_board, self.backend.player_names),
            'couples2': service_game_backend.format_list(couples2_board, self.backend.player_names),
            'singles2': service_game_backend.format_list(singles2_board, self.backend.player_names),
            'charlie': service_game_backend.format_list(charlie_board, self.backend.player_names),
            'statico': service_game_backend.format_list(statico_board, self.backend.player_names)
        }

        # Get next players
        next_players = self._get_next_players_info()

        # Get current players
        current_players = self._get_current_players_info()

        # Calculate remaining times
        remaining_times = self._calculate_remaining_times()

        # Get track statuses
        track_statuses = self._get_track_statuses()

        # Check stop capabilities
        stop_capabilities = self._get_stop_capabilities()

        # Persist backend state
        set_game_backend(self.backend)

        # Combine all information
        return {
            **formatted_boards,
            **next_players,
            **current_players,
            **remaining_times,
            **track_statuses,
            **durations,
            **stop_capabilities,
            'player_icon_url': url_for('static', filename='icons/Vector.svg')
        }

    def _get_next_players_info(self) -> Dict:
        """Get information about next players for all tracks."""
        return {
            'next_player_alfa_bravo_id': self.backend.next_player_alfa_bravo_id,
            'next_player_alfa_bravo_name': self.backend.get_player_name(
                self.backend.next_player_alfa_bravo_id
            ) if self.backend.next_player_alfa_bravo_id else None,
            'next_player_alfa_bravo_id2': self.backend.next_player_alfa_bravo_id2,
            'next_player_alfa_bravo_name2': self.backend.get_player_name(
                self.backend.next_player_alfa_bravo_id2
            ) if self.backend.next_player_alfa_bravo_id2 else None,
            'next_player_charlie_id': self.backend.next_player_charlie_id,
            'next_player_charlie_name': self.backend.next_player_charlie_name,
            'next_player_statico_id': self.backend.next_player_statico_id,
            'next_player_statico_name': self.backend.next_player_statico_name
        }

    def _get_current_players_info(self) -> Dict:
        """Get information about current players on all tracks."""
        return {
            'current_player_alfa': self.backend.current_player_alfa,
            'current_player_bravo': self.backend.current_player_bravo,
            'current_player_alfa2': self.backend.current_player_alfa2,
            'current_player_bravo2': self.backend.current_player_bravo2,
            'current_player_charlie': self.backend.current_player_charlie,
            'current_player_delta': self.backend.current_player_delta,
            'current_player_echo': self.backend.current_player_echo
        }

    def _calculate_remaining_times(self) -> Dict:
        """Calculate remaining times for all tracks."""
        now = date.get_current_time()

        # Localize all times
        times_to_localize = [
            'ALFA_next_available', 'BRAVO_next_available',
            'ALFA_next_available2', 'BRAVO_next_available2',
            'CHARLIE_next_available', 'DELTA_next_available', 'ECHO_next_available'
        ]

        for attr in times_to_localize:
            current_time = getattr(self.backend, attr)
            setattr(self.backend, attr, self.backend.localize_time(current_time))

        # Calculate remaining minutes
        def calc_remaining(next_available):
            return max(0, (next_available - now).total_seconds() / 60)

        return {
            'alfa_remaining': f"{int(calc_remaining(self.backend.ALFA_next_available))}min",
            'bravo_remaining': f"{int(calc_remaining(self.backend.BRAVO_next_available))}min",
            'alfa2_remaining': f"{int(calc_remaining(self.backend.ALFA_next_available2))}min",
            'bravo2_remaining': f"{int(calc_remaining(self.backend.BRAVO_next_available2))}min",
            'charlie_remaining': f"{int(calc_remaining(self.backend.CHARLIE_next_available))}min",
            'delta_remaining': f"{int(calc_remaining(self.backend.DELTA_next_available))}min",
            'echo_remaining': f"{int(calc_remaining(self.backend.ECHO_next_available))}min"
        }

    def _get_track_statuses(self) -> Dict:
        """Get status (Occupata/Libera) for all tracks."""
        tracks = [
            ('alfa', self.backend.current_player_alfa),
            ('bravo', self.backend.current_player_bravo),
            ('alfa2', self.backend.current_player_alfa2),
            ('bravo2', self.backend.current_player_bravo2),
            ('charlie', self.backend.current_player_charlie),
            ('delta', self.backend.current_player_delta),
            ('echo', self.backend.current_player_echo)
        ]

        return {
            f'{track}_status': 'Occupata' if player else 'Libera'
            for track, player in tracks
        }

    def _get_stop_capabilities(self) -> Dict:
        """Check which tracks can be stopped."""
        return {
            'can_stop_couple1': self.backend.can_stop_couple(),
            'can_stop_couple2': self.backend.can_stop_couple2(),
            'can_stop_single1': (
                self.backend.current_player_alfa is not None and
                self.backend.current_player_alfa.get('id', '').startswith("BLU")
            ),
            'can_stop_single2': (
                self.backend.current_player_alfa2 is not None and
                self.backend.current_player_alfa2.get('id', '').startswith("BIANCO")
            )
        }

    # ============================================================================
    # BUTTON HANDLING
    # ============================================================================

    def handle_button_press(self, button: str, data: Optional[Dict] = None) -> Tuple[Dict, int]:
        """
        Handle button press actions.

        Args:
            button: Button identifier
            data: Additional data from request

        Returns:
            Tuple of (response dict, status code)
        """
        logger.info(f"Button press: {button}")

        try:
            if button in self._get_start_buttons():
                return self._handle_start_button(button)
            elif button in self._get_stop_buttons():
                return self._handle_stop_button(button, data or {})
            elif button in ['third', 'third2']:
                return self._handle_third_button(button)
            else:
                logger.warning(f"Unknown button: {button}")
                return {'success': False, 'error': 'Pulsante non riconosciuto'}, 400
        except Exception as e:
            logger.error(f"Button press error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}, 500

    def _get_start_buttons(self) -> list:
        """Get list of start button identifiers."""
        return [
            'first_start', 'second_start', 'first_start2', 'second_start2',
            'charlie_start', 'statico_start_delta', 'statico_start_echo'
        ]

    def _get_stop_buttons(self) -> list:
        """Get list of stop button identifiers."""
        return [
            'first_stop', 'second_stop', 'first_stop2', 'second_stop2',
            'charlie_stop', 'statico_stop_delta', 'statico_stop_echo'
        ]

    def _handle_start_button(self, button: str) -> Tuple[Dict, int]:
        """Handle start button press."""
        handlers = {
            'first_start': lambda: self._start_couple_game(1),
            'second_start': lambda: self._start_single_game(1),
            'first_start2': lambda: self._start_couple_game(2),
            'second_start2': lambda: self._start_single_game(2),
            'charlie_start': self._start_charlie_game,
            'statico_start_delta': lambda: self._start_statico_game('delta'),
            'statico_start_echo': lambda: self._start_statico_game('echo')
        }

        handler = handlers.get(button)
        if handler:
            return handler()

        return {'success': False, 'error': 'Handler non trovato'}, 400

    def _start_couple_game(self, track_set: int) -> Tuple[Dict, int]:
        """Start couple game on specified track set."""
        queue_attr = 'queue_couples' if track_set == 1 else 'queue_couples2'
        queue = getattr(self.backend, queue_attr)

        if not queue:
            return {
                'success': False,
                'error': f'La coda coppie {track_set} è vuota'
            }, 400

        try:
            if track_set == 1:
                self.backend.start_game(is_couple=True)
            else:
                self.backend.start_game2(is_couple=True)

            set_game_backend(self.backend)

            player_attr = 'current_player_couple' if track_set == 1 else 'current_player_couple2'

            return {
                'success': True,
                'start_time': date.get_current_time().isoformat(),
                f'current_player_alfa{"" if track_set == 1 else "2"}': getattr(self.backend, f'current_player_alfa{"" if track_set == 1 else "2"}'),
                f'current_player_bravo{"" if track_set == 1 else "2"}': getattr(self.backend, f'current_player_bravo{"" if track_set == 1 else "2"}')
            }, 200
        except Exception as e:
            logger.error(f"Error starting couple game {track_set}: {e}")
            return {'success': False, 'error': str(e)}, 500

    def _start_single_game(self, track_set: int) -> Tuple[Dict, int]:
        """Start single game on specified track set."""
        queue_attr = 'queue_singles' if track_set == 1 else 'queue_singles2'
        queue = getattr(self.backend, queue_attr)

        if not queue:
            return {
                'success': False,
                'error': f'La coda singoli {track_set} è vuota'
            }, 400

        try:
            if track_set == 1:
                self.backend.start_game(is_couple=False)
            else:
                self.backend.start_game2(is_couple=False)

            set_game_backend(self.backend)

            suffix = "" if track_set == 1 else "2"
            return {
                'success': True,
                'start_time': date.get_current_time().isoformat(),
                f'current_player_alfa{suffix}': getattr(self.backend, f'current_player_alfa{suffix}')
            }, 200
        except Exception as e:
            logger.error(f"Error starting single game {track_set}: {e}")
            return {'success': False, 'error': str(e)}, 500

    def _start_charlie_game(self) -> Tuple[Dict, int]:
        """Start Charlie game."""
        if not self.backend.queue_charlie:
            return {'success': False, 'error': 'La coda Charlie è vuota'}, 400

        try:
            self.backend.start_charlie_game()
            set_game_backend(self.backend)
            return {
                'success': True,
                'current_player_charlie': self.backend.current_player_charlie
            }, 200
        except Exception as e:
            logger.error(f"Error starting charlie game: {e}")
            return {'success': False, 'error': str(e)}, 500

    def _start_statico_game(self, pista: str) -> Tuple[Dict, int]:
        """Start Statico game on specified track."""
        if not self.backend.queue_statico:
            return {'success': False, 'error': 'La coda Statico è vuota'}, 400

        player_attr = f'current_player_{pista}'
        if getattr(self.backend, player_attr):
            return {'success': False, 'error': f'La pista {pista.upper()} è già occupata'}, 400

        try:
            self.backend.start_statico_game(pista=pista)
            set_game_backend(self.backend)
            return {
                'success': True,
                player_attr: getattr(self.backend, player_attr)
            }, 200
        except Exception as e:
            logger.error(f"Error starting statico game on {pista}: {e}")
            return {'success': False, 'error': str(e)}, 500

    def _handle_stop_button(self, button: str, data: Dict) -> Tuple[Dict, int]:
        """Handle stop button press - returns data for penalty modal."""
        now = date.get_current_time()

        try:
            if button == 'first_stop':
                result = self._prepare_couple_stop(1, data.get('control'))
            elif button == 'second_stop':
                result = self._prepare_single_stop(1)
            elif button == 'first_stop2':
                result = self._prepare_couple_stop(2, data.get('control'))
            elif button == 'second_stop2':
                result = self._prepare_single_stop(2)
            elif button == 'charlie_stop':
                return self._handle_charlie_stop()
            elif button == 'statico_stop_delta':
                return self._handle_statico_stop('delta')
            elif button == 'statico_stop_echo':
                return self._handle_statico_stop('echo')
            else:
                return {'success': False, 'error': 'Pulsante stop non riconosciuto'}, 400

            if 'error' in result:
                return {'success': False, 'error': result['error']}, 400

            # Calculate timer duration
            start_time = self.backend.player_start_times.get(result['player_id'])
            if not start_time:
                return {
                    'success': False,
                    'error': f"Orario inizio non trovato per {result['player_id']}"
                }, 400

            timer_duration_minutes = (now - start_time).total_seconds() / 60.0

            set_game_backend(self.backend)

            return {
                'success': True,
                'action': 'penalty_input_required',
                'player_id': result['player_id'],
                'player_name': self.backend.get_player_name(result['player_id']),
                'timer_duration_minutes': timer_duration_minutes,
                'player_type': result['player_type']
            }, 200

        except Exception as e:
            logger.error(f"Error in stop button {button}: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}, 500

    def _prepare_couple_stop(self, track_set: int, control: bool) -> Dict:
        """Prepare data for couple stop."""
        suffix = "" if track_set == 1 else "2"
        can_stop_method = 'can_stop_couple' if track_set == 1 else 'can_stop_couple2'

        if control and not getattr(self.backend, can_stop_method)():
            return {'error': f'Stop coppia {track_set} non possibile (metà percorso?)'}

        couple_attr = f'current_player_couple{suffix}'
        current_couple = getattr(self.backend, couple_attr)

        if not current_couple:
            return {'error': f'Nessuna coppia {track_set} attiva'}

        return {
            'player_id': current_couple['id'],
            'player_type': f'couple{suffix}' if track_set == 2 else 'couple'
        }

    def _prepare_single_stop(self, track_set: int) -> Dict:
        """Prepare data for single stop."""
        suffix = "" if track_set == 1 else "2"
        prefix = "BLU" if track_set == 1 else "BIANCO"

        current_player = getattr(self.backend, f'current_player_alfa{suffix}')

        if not (current_player and current_player.get('id', '').startswith(prefix)):
            return {'error': f'Nessun singolo ({prefix}) in pista ALFA{suffix}'}

        return {
            'player_id': current_player['id'],
            'player_type': f'single{suffix}' if track_set == 2 else 'single'
        }

    def _handle_charlie_stop(self) -> Tuple[Dict, int]:
        """Handle Charlie stop button."""
        if not self.backend.current_player_charlie:
            return {'success': False, 'error': 'Nessun giocatore Charlie attivo'}, 400

        player_id = self.backend.current_player_charlie['id']
        start_time = self.backend.player_start_times.get(player_id)

        if not start_time:
            return {
                'success': False,
                'error': f'Orario inizio non trovato per {player_id}'
            }, 400

        now = date.get_current_time()
        timer_duration_minutes = (now - start_time).total_seconds() / 60.0

        try:
            self.backend.record_charlie_game(timer_duration_minutes)
            set_game_backend(self.backend)

            return {
                'success': True,
                'player_id': player_id,
                'player_name': self.backend.get_player_name(player_id)
            }, 200
        except Exception as e:
            logger.error(f"Error recording charlie game: {e}")
            return {'success': False, 'error': str(e)}, 500

    def _handle_statico_stop(self, pista: str) -> Tuple[Dict, int]:
        """Handle Statico stop button."""
        player_attr = f'current_player_{pista}'
        current_player = getattr(self.backend, player_attr)

        if not current_player:
            return {
                'success': False,
                'error': f'Nessun giocatore in pista {pista.upper()}'
            }, 400

        player_id = current_player['id']
        start_time = self.backend.player_start_times.get(player_id)

        if not start_time:
            return {
                'success': False,
                'error': f'Orario inizio non trovato per {player_id}'
            }, 400

        now = date.get_current_time()
        duration = (now - start_time).total_seconds() / 60

        try:
            self.backend.record_statico_game(duration, pista=pista)
            set_game_backend(self.backend)
            return {'success': True}, 200
        except Exception as e:
            logger.error(f"Error recording statico game on {pista}: {e}")
            return {'success': False, 'error': str(e)}, 500

    def _handle_third_button(self, button: str) -> Tuple[Dict, int]:
        """Handle third button (metà percorso) press."""
        try:
            if button == 'third':
                self.backend.button_third_pressed()
            else:  # third2
                self.backend.button_third_pressed2()

            set_game_backend(self.backend)
            return {'success': True}, 200
        except ValueError as e:
            logger.warning(f"Third button {button} failed: {e}")
            return {'success': False, 'error': str(e)}, 400
        except Exception as e:
            logger.error(f"Error in third button {button}: {e}")
            return {'success': False, 'error': 'Errore interno del server'}, 500

    # ============================================================================
    # PLAYER ACTIONS
    # ============================================================================

    def get_skipped_players(self) -> Dict:
        """
        Get all skipped players.

        Returns:
            Dictionary with skipped players for each queue
        """
        return {
            'couples': [{'id': c['id']} for c in self.backend.skipped_couples],
            'singles': [{'id': s['id']} for s in self.backend.skipped_singles],
            'couples2': [{'id': c2['id']} for c2 in self.backend.skipped_couples2],
            'singles2': [{'id': s2['id']} for s2 in self.backend.skipped_singles2],
            'charlie': [{'id': p['id']} for p in self.backend.skipped_charlie],
            'statico': [{'id': p['id']} for p in self.backend.skipped_statico]
        }

    def add_statico_player(self, player_id: int, name: str) -> Tuple[Dict, int]:
        """
        Add a player to Statico queue.

        Args:
            player_id: Player numeric ID
            name: Player name/color

        Returns:
            Tuple of (response dict, status code)
        """
        if not player_id or not name:
            return {'success': False, 'error': 'ID e nome obbligatori'}, 400

        if player_id > 100:
            return {'success': False, 'error': 'ID deve essere minore di 100'}, 400

        statico_id = f"{name.upper()} {int(player_id):03d}"

        try:
            self.backend.add_statico_player(statico_id, name)
            set_game_backend(self.backend)
            return {'success': True}, 200
        except Exception as e:
            logger.error(f"Error adding statico player: {e}")
            return {'success': False, 'error': str(e)}, 500

    def skip_statico_player(self, player_id: str) -> Tuple[Dict, int]:
        """
        Skip a Statico player.

        Args:
            player_id: Player ID to skip

        Returns:
            Tuple of (response dict, status code)
        """
        if not player_id:
            return {'success': False, 'error': 'Player ID obbligatorio'}, 400

        try:
            self.backend.skip_statico_player(player_id)
            set_game_backend(self.backend)

            return {
                'success': True,
                'next_player_statico_id': self.backend.next_player_statico_id,
                'next_player_statico_name': self.backend.next_player_statico_name
            }, 200
        except Exception as e:
            logger.error(f"Error skipping statico player: {e}")
            return {'success': False, 'error': str(e)}, 500

    def delete_player(self, player_id: str) -> Tuple[Dict, int]:
        """
        Delete a player from all queues.

        Args:
            player_id: Player ID to delete

        Returns:
            Tuple of (response dict, status code)
        """
        if not player_id:
            return {'success': False, 'error': 'Player ID obbligatorio'}, 400

        try:
            self.backend.delete_player(player_id)
            set_game_backend(self.backend)
            return {'success': True}, 200
        except Exception as e:
            logger.error(f"Error deleting player: {e}")
            return {'success': False, 'error': str(e)}, 500


# ============================================================================
# LEGACY FUNCTIONS FOR BACKWARD COMPATIBILITY
# ============================================================================

_player_service: Optional[PlayerService] = None


def get_player_service() -> PlayerService:
    """Get or create PlayerService instance."""
    global _player_service
    if _player_service is None:
        _player_service = PlayerService()
    return _player_service


def service_save_contact():
    """Legacy function - delegates to PlayerService."""
    service = get_player_service()
    response, status = service.save_contact_info(request.json)
    return jsonify(response), status


def simulate_player():
    """Legacy function - delegates to PlayerService."""
    service = get_player_service()
    return jsonify(service.simulate_player_status())


def get_skipped():
    """Legacy function - delegates to PlayerService."""
    service = get_player_service()
    return jsonify(service.get_skipped_players())


def service_button_press():
    """Legacy function - delegates to PlayerService."""
    service = get_player_service()
    button = request.json.get('button')
    response, status = service.handle_button_press(button, request.json)
    return jsonify(response), status


def service_add_statico():
    """Legacy function - delegates to PlayerService."""
    service = get_player_service()
    player_id = request.json.get('id')
    name = request.json.get('name')
    response, status = service.add_statico_player(player_id, name)
    return jsonify(response), status


def service_skip_statico_player():
    """Legacy function - delegates to PlayerService."""
    service = get_player_service()
    player_id = request.json.get('id')
    response, status = service.skip_statico_player(player_id)
    return jsonify(response), status


def service_delete_player():
    """Legacy function - delegates to PlayerService."""
    service = get_player_service()
    player_id = request.json.get('id')
    response, status = service.delete_player(player_id)
    return jsonify(response), status
