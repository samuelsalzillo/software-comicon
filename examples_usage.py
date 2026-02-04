"""
Usage Examples for Refactored Classes.

This module demonstrates how to use the new service classes
and refactored components.
"""

# Example 1: Using QueueManager
from src.service.queue_manager import QueueManager

def example_queue_manager():
    """Example of using QueueManager."""
    # Initialize queue manager
    queue_mgr = QueueManager()

    # Add players to queues
    queue_mgr.add_to_queue('couples', 'GIALLO-001', 'Team Alpha')
    queue_mgr.add_to_queue('singles', 'BLU-001', 'Player Beta')
    queue_mgr.add_to_queue('charlie', 'VERDE-001', 'Player Gamma')

    # Get queue statistics
    stats = queue_mgr.get_all_queue_stats()
    print(f"Queue stats: {stats}")

    # Skip a player
    queue_mgr.skip_player('GIALLO-001')

    # Restore skipped player as next
    queue_mgr.restore_skipped('GIALLO-001', as_next=True)

    # Get player position
    position = queue_mgr.get_player_position('couples', 'GIALLO-001')
    print(f"Player position: {position}")


# Example 2: Using TrackManager
from src.service.track_manager import TrackManager

def example_track_manager():
    """Example of using TrackManager."""
    # Initialize track manager
    track_mgr = TrackManager()

    # Assign player to track
    player = {'id': 'GIALLO-001', 'arrival': None}
    success = track_mgr.assign_player_to_track('alfa', player, duration_minutes=5.0)
    print(f"Player assigned: {success}")

    # Check track availability
    is_available = track_mgr.is_track_available('alfa')
    print(f"Track Alfa available: {is_available}")

    # Get track status
    status = track_mgr.get_track_status('alfa')
    print(f"Track Alfa status: {status}")

    # Get all tracks status
    all_status = track_mgr.get_all_tracks_status()
    print(f"All tracks: {all_status}")

    # Release track
    released_player = track_mgr.release_track('alfa')
    print(f"Released player: {released_player}")

    # Handle third button for couples
    track_mgr.couple_in_alfa = True
    success = track_mgr.handle_third_button(track_set=1)
    print(f"Third button handled: {success}")


# Example 3: Using TimingManager
from src.service.timing_manager import TimingManager

def example_timing_manager():
    """Example of using TimingManager."""
    # Initialize timing manager
    timing_mgr = TimingManager()

    # Record couple game
    timing_mgr.record_couple_game(
        player_id='GIALLO-001',
        timer_duration=4.5,
        official_score=5.0,
        track_set=1
    )

    # Record single game
    timing_mgr.record_single_game(
        player_id='BLU-001',
        timer_duration=2.0,
        official_score=2.5,
        track_set=1
    )

    # Record mid time
    timing_mgr.record_mid_time(mid_duration=1.8, track_set=1)

    # Update averages
    timing_mgr.update_averages()

    # Get timing statistics
    stats = timing_mgr.get_timing_stats()
    print(f"Timing stats: {stats}")

    # Access current values
    print(f"Current T_total: {timing_mgr.t_total}")
    print(f"Current T_single: {timing_mgr.t_single}")
    print(f"Current T_charlie: {timing_mgr.t_charlie}")


# Example 4: Using BackupService
from src.service.backup import BackupService, initialize_backup_service

def example_backup_service():
    """Example of using BackupService."""
    # Initialize backup service
    backup_service = initialize_backup_service(
        db_path='stand.db',
        backup_dir='backup',
        max_backups=10,
        backup_interval=3600
    )

    # Create a backup
    backup_path = backup_service.create_backup()
    print(f"Backup created at: {backup_path}")

    # Get all backups
    all_backups = backup_service.get_all_backups()
    print(f"Total backups: {len(all_backups)}")
    for backup in all_backups:
        print(f"  - {backup['filename']} ({backup['size_bytes']} bytes)")

    # Restore from backup (use with caution!)
    # success = backup_service.restore_backup('stand_db_backup_20260203_120000.db')
    # print(f"Restore successful: {success}")


# Example 5: Using Configuration Constants
from src.config import (
    PlayerType, TrackName, ColorCode,
    DefaultTimings, GameConfig
)

def example_configuration():
    """Example of using configuration constants."""
    # Using enums
    player_type = PlayerType.COUPLE
    print(f"Player type: {player_type.value}")

    track_name = TrackName.ALFA
    print(f"Track name: {track_name.value}")

    color = ColorCode.GIALLO
    print(f"Color code: {color.value}")

    # Using configuration classes
    print(f"Default T_mid: {DefaultTimings.T_MID}")
    print(f"Default T_total: {DefaultTimings.T_TOTAL}")
    print(f"Min games for average: {GameConfig.MIN_GAMES_FOR_AVERAGE}")
    print(f"Penalty hours: {GameConfig.PENALTY_HOURS}")


# Example 6: Using Custom Exceptions
from src.exceptions import (
    PlayerNotFoundError,
    TrackOccupiedError,
    ValidationError
)

def example_exceptions():
    """Example of using custom exceptions."""
    # Player not found
    try:
        player_id = 'GIALLO-999'
        # Simulating player lookup
        raise PlayerNotFoundError(player_id, context='queue_couples')
    except PlayerNotFoundError as e:
        print(f"Error: {e}")
        print(f"Details: {e.details}")

    # Track occupied
    try:
        raise TrackOccupiedError('alfa', 'GIALLO-001')
    except TrackOccupiedError as e:
        print(f"Error: {e}")
        print(f"Track: {e.track_name}, Player: {e.current_player_id}")

    # Validation error
    try:
        raise ValidationError('player_name', 'Name cannot be empty', value='')
    except ValidationError as e:
        print(f"Error: {e}")
        print(f"Field: {e.field}, Value: {e.value}")


# Example 7: Using GameBackendService
from src.service.service_game_backend import GameBackendService

def example_game_backend_service():
    """Example of using GameBackendService."""
    service = GameBackendService()

    # Format player list
    player_list = [
        (1, 'GIALLO-001', '14:30:00'),
        (2, 'GIALLO-002', '14:35:00'),
        (3, 'GIALLO-003', '14:40:00')
    ]
    player_names = {
        'GIALLO-001': 'Team Alpha',
        'GIALLO-002': 'Team Beta',
        'GIALLO-003': 'Team Gamma'
    }

    formatted = service.format_player_list(player_list, player_names)
    print(f"Formatted list: {formatted}")

    # Format time display
    time_str = service.format_time_display(125.5)  # 125.5 seconds
    print(f"Formatted time: {time_str}")  # Output: 02:05

    # Calculate score with penalty
    final_score = service.calculate_score_with_penalty(
        base_time=5.0,  # 5 minutes
        penalty_seconds=30  # 30 seconds penalty
    )
    print(f"Final score: {final_score} minutes")  # 5.5 minutes


# Example 8: Using TreasureHunt Model
from src.model.TreasureHunt import TreasureHunt
from datetime import datetime, timedelta

def example_treasure_hunt_model():
    """Example of using enhanced TreasureHunt model."""
    # Create a treasure hunt entry (normally done through SQLAlchemy session)
    # This is just for demonstration
    hunt = TreasureHunt()
    hunt.id_player = 'GIALLO-001'
    hunt.chiave_esterna = '12345'
    hunt.nome = 'Mario'
    hunt.cognome = 'Rossi'
    hunt.qr_code = 'QR123'
    hunt.qr_code_founded = 'QR123'
    hunt.telefono = '+39 123 456 7890'
    hunt.timestamp_inizio = datetime.now()
    hunt.timestamp_fine = datetime.now() + timedelta(minutes=10)

    # Use properties
    print(f"Full name: {hunt.full_name}")
    print(f"Duration: {hunt.duration_seconds} seconds")
    print(f"QR correct: {hunt.is_qr_code_correct}")

    # Convert to dictionary
    data = hunt.to_dict()
    print(f"Dictionary: {data}")


# Example 9: Complete Workflow
def example_complete_workflow():
    """Example of a complete game workflow using new classes."""
    # Initialize managers
    queue_mgr = QueueManager()
    track_mgr = TrackManager()
    timing_mgr = TimingManager()

    print("=== Game Workflow Example ===\n")

    # Step 1: Add players to queue
    print("1. Adding players to queue...")
    queue_mgr.add_to_queue('couples', 'GIALLO-001', 'Team Alpha')
    queue_mgr.add_to_queue('couples', 'GIALLO-002', 'Team Beta')
    queue_mgr.add_to_queue('singles', 'BLU-001', 'Player Gamma')

    stats = queue_mgr.get_all_queue_stats()
    print(f"   Queue stats: {stats}\n")

    # Step 2: Assign player to track
    print("2. Assigning player to track...")
    player = {'id': 'GIALLO-001', 'arrival': None}
    track_mgr.assign_player_to_track('alfa', player, duration_minutes=5.0)
    track_mgr.couple_in_alfa = True

    status = track_mgr.get_track_status('alfa')
    print(f"   Track Alfa status: {status}\n")

    # Step 3: Handle third button
    print("3. Handling third button press...")
    track_mgr.handle_third_button(track_set=1)
    timing_mgr.record_mid_time(1.8, track_set=1)
    print(f"   Third button pressed, mid time recorded\n")

    # Step 4: Complete game and record times
    print("4. Completing game...")
    timing_mgr.record_couple_game(
        player_id='GIALLO-001',
        timer_duration=4.5,
        official_score=5.0,
        track_set=1
    )
    track_mgr.release_track('alfa')
    print(f"   Game completed, track released\n")

    # Step 5: Update averages
    print("5. Updating timing averages...")
    timing_mgr.update_averages()
    print(f"   T_total: {timing_mgr.t_total:.2f} min")
    print(f"   T_mid: {timing_mgr.t_mid:.2f} min\n")

    # Step 6: Remove player from queue (already played)
    print("6. Cleaning up...")
    queue_mgr.remove_from_queue('couples', 'GIALLO-001')

    final_stats = queue_mgr.get_all_queue_stats()
    print(f"   Final queue stats: {final_stats}\n")

    print("=== Workflow Complete ===")


if __name__ == '__main__':
    """Run all examples."""
    print("=" * 60)
    print("REFACTORED CLASSES USAGE EXAMPLES")
    print("=" * 60)
    print()

    examples = [
        ("QueueManager", example_queue_manager),
        ("TrackManager", example_track_manager),
        ("TimingManager", example_timing_manager),
        ("BackupService", example_backup_service),
        ("Configuration", example_configuration),
        ("Custom Exceptions", example_exceptions),
        ("GameBackendService", example_game_backend_service),
        ("TreasureHunt Model", example_treasure_hunt_model),
        ("Complete Workflow", example_complete_workflow),
    ]

    for title, example_func in examples:
        print(f"\n{'=' * 60}")
        print(f"Example: {title}")
        print('=' * 60)
        try:
            example_func()
        except Exception as e:
            print(f"Error running example: {e}")
        print()
