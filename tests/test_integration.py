"""
Integration Tests Suite.

Test completo di integrazione per verificare che tutti i componenti refactorizzati
funzionino correttamente insieme.
"""
import os
import sys
import tempfile
import sqlite3
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model.GameBackend import GameBackend
from src.service.service_player import PlayerService, get_player_service
from src.service.scheduling_service import get_scheduling_service
from src.repository import (
    get_scoring_repository,
    get_qualified_players_repository,
    get_queue_repository,
    get_average_times_repository
)


class IntegrationTestSuite:
    """Suite completa di test di integrazione."""

    def __init__(self):
        self.test_db_path = None
        self.backend = None
        self.player_service = None
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }

    def setup(self):
        """Setup test environment."""
        print("🔧 Setup test environment...")

        # Create temporary database
        fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        os.environ['SQLITE_DB_PATH'] = self.test_db_path

        # Initialize database tables
        self._init_test_database()

        # Initialize components
        self.backend = GameBackend()
        self.player_service = PlayerService(self.backend)

        print(f"✅ Test database created: {self.test_db_path}")
        print(f"✅ GameBackend initialized with managers")
        print(f"✅ PlayerService initialized\n")

    def teardown(self):
        """Cleanup test environment."""
        print("\n🧹 Cleanup test environment...")

        # Clear backend references to close any open connections
        self.backend = None
        self.player_service = None

        # Force garbage collection to close connections
        import gc
        gc.collect()

        # Wait a bit for connections to close
        import time
        time.sleep(0.1)

        if self.test_db_path and os.path.exists(self.test_db_path):
            try:
                os.unlink(self.test_db_path)
                print(f"✅ Test database deleted")
            except PermissionError:
                print(f"⚠️  Could not delete test database (still in use)")
                print(f"   File will be cleaned up on next run: {self.test_db_path}")

    def _init_test_database(self):
        """Initialize test database with required tables."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Create all required tables
        tables = [
            """
            CREATE TABLE IF NOT EXISTS scoring (
                player_id TEXT PRIMARY KEY,
                player_name TEXT,
                player_type TEXT,
                score REAL,
                created_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS qualified_players (
                player_id TEXT PRIMARY KEY,
                player_name TEXT,
                first_name TEXT,
                last_name TEXT,
                phone_number TEXT,
                score_minutes REAL,
                score_formatted TEXT,
                player_type TEXT,
                qualification_reason TEXT,
                qualification_date TEXT,
                created_at TEXT,
                treasure_hunt_updated TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS average_times (
                player_type TEXT PRIMARY KEY,
                timer_duration_minutes REAL,
                official_score_minutes REAL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS queue (
                player_id TEXT PRIMARY KEY,
                player_name TEXT,
                queue_type TEXT,
                position INTEGER,
                arrival_time TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS mid_times (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                couple_type TEXT,
                mid_duration_minutes REAL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS charlie_timer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT,
                timer_duration_minutes REAL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS skipped (
                player_id TEXT PRIMARY KEY,
                player_name TEXT,
                queue_type TEXT,
                skipped_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS couple_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT,
                timer_duration_minutes REAL,
                official_score_minutes REAL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS single_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT,
                timer_duration_minutes REAL,
                official_score_minutes REAL
            )
            """
        ]

        for table_sql in tables:
            cursor.execute(table_sql)

        conn.commit()
        conn.close()
        logger.debug("Test database initialized with all required tables")

    def assert_test(self, condition, test_name, error_msg=""):
        """Assert a test condition."""
        if condition:
            self.results['passed'] += 1
            print(f"  ✅ {test_name}")
            return True
        else:
            self.results['failed'] += 1
            self.results['errors'].append(f"{test_name}: {error_msg}")
            print(f"  ❌ {test_name}: {error_msg}")
            return False

    # ========================================================================
    # TEST 1: GameBackend Initialization
    # ========================================================================

    def test_gamebackend_initialization(self):
        """Test GameBackend initialization with managers."""
        print("\n📋 TEST 1: GameBackend Initialization")

        # Test managers exist
        self.assert_test(
            self.backend.queue_manager is not None,
            "QueueManager initialized"
        )

        self.assert_test(
            self.backend.track_manager is not None,
            "TrackManager initialized"
        )

        self.assert_test(
            self.backend.timing_manager is not None,
            "TimingManager initialized"
        )

        # Test manager types
        self.assert_test(
            type(self.backend.queue_manager).__name__ == 'QueueManager',
            "QueueManager correct type"
        )

        self.assert_test(
            type(self.backend.track_manager).__name__ == 'TrackManager',
            "TrackManager correct type"
        )

        self.assert_test(
            type(self.backend.timing_manager).__name__ == 'TimingManager',
            "TimingManager correct type"
        )

    # ========================================================================
    # TEST 2: Queue Operations
    # ========================================================================

    def test_queue_operations(self):
        """Test queue operations through GameBackend."""
        print("\n📋 TEST 2: Queue Operations")

        # Test add couple
        self.backend.add_couple('GIALLO-001', 'Team Alpha')
        self.assert_test(
            len(self.backend.queue_couples) == 1,
            "Add couple to queue"
        )

        self.assert_test(
            self.backend.queue_couples[0]['id'] == 'GIALLO-001',
            "Couple ID correct"
        )

        # Test add single
        self.backend.add_single('BLU-001', 'Player Beta')
        self.assert_test(
            len(self.backend.queue_singles) == 1,
            "Add single to queue"
        )

        # Test add charlie
        self.backend.add_charlie_player('VERDE-001', 'Player Gamma')
        self.assert_test(
            len(self.backend.queue_charlie) == 1,
            "Add charlie to queue"
        )

        # Test player names
        self.assert_test(
            self.backend.get_player_name('GIALLO-001') == 'Team Alpha',
            "Get player name"
        )

        # Test skip player
        self.backend.skip_player('GIALLO-001')
        self.assert_test(
            len(self.backend.skipped_couples) == 1,
            "Skip player"
        )

        self.assert_test(
            len(self.backend.queue_couples) == 0,
            "Player removed from queue after skip"
        )

    # ========================================================================
    # TEST 3: Track Operations
    # ========================================================================

    def test_track_operations(self):
        """Test track operations through GameBackend."""
        print("\n📋 TEST 3: Track Operations")

        # Add players to queue
        self.backend.add_couple('GIALLO-002', 'Team Beta')
        self.backend.add_single('BLU-002', 'Player Delta')

        # Test start game for couple
        self.backend.start_game(is_couple=True)

        self.assert_test(
            self.backend.current_player_alfa is not None,
            "Couple assigned to Alfa"
        )

        self.assert_test(
            self.backend.current_player_bravo is not None,
            "Couple assigned to Bravo"
        )

        self.assert_test(
            self.backend.current_player_alfa['id'] == 'GIALLO-002',
            "Correct couple in Alfa"
        )

        # Test track availability
        self.assert_test(
            self.backend.current_player_couple is not None,
            "Current couple tracked"
        )

        # Test can_stop_couple
        self.assert_test(
            self.backend.can_stop_couple() == False,
            "Cannot stop couple before mid point"
        )

        # Simulate mid point
        self.backend.button_third_pressed()

        self.assert_test(
            self.backend.can_stop_couple() == True,
            "Can stop couple after mid point"
        )

    # ========================================================================
    # TEST 4: Timing Operations
    # ========================================================================

    def test_timing_operations(self):
        """Test timing operations through GameBackend."""
        print("\n📋 TEST 4: Timing Operations")

        # Test default timing values
        self.assert_test(
            self.backend.T_mid > 0,
            "T_mid initialized"
        )

        self.assert_test(
            self.backend.T_total > 0,
            "T_total initialized"
        )

        self.assert_test(
            self.backend.T_single > 0,
            "T_single initialized"
        )

        # Test set timing values
        original_t_mid = self.backend.T_mid
        self.backend.T_mid = 2.5

        self.assert_test(
            self.backend.T_mid == 2.5,
            "Set T_mid value"
        )

        # Test record game
        try:
            self.backend.record_couple_game(4.5, 5.0)
            self.assert_test(True, "Record couple game")
        except Exception as e:
            self.assert_test(False, "Record couple game", str(e))

        # Test timing history
        self.assert_test(
            len(self.backend.couple_history_total) > 0,
            "Couple history recorded"
        )

    # ========================================================================
    # TEST 5: Repository Pattern - Scoring
    # ========================================================================

    def test_repository_scoring(self):
        """Test ScoringRepository integration."""
        print("\n📋 TEST 5: Repository Pattern - Scoring")

        scoring_repo = get_scoring_repository()

        # Test save score
        try:
            scoring_repo.save_score(
                player_id='TEST-001',
                player_name='Test Player',
                player_type='couple',
                score=4.5
            )
            self.assert_test(True, "Save score via repository")
        except Exception as e:
            self.assert_test(False, "Save score via repository", str(e))

        # Test find by ID
        player = scoring_repo.find_by_player_id('TEST-001')
        self.assert_test(
            player is not None,
            "Find score by player ID"
        )

        self.assert_test(
            player['score'] == 4.5,
            "Score value correct"
        )

        # Test get leaderboard
        leaderboard = scoring_repo.get_leaderboard('couple', limit=10)
        self.assert_test(
            len(leaderboard) >= 1,
            "Get leaderboard"
        )

        self.assert_test(
            leaderboard[0]['player_id'] == 'TEST-001',
            "Leaderboard ordered correctly"
        )

    # ========================================================================
    # TEST 6: Repository Pattern - Qualified Players
    # ========================================================================

    def test_repository_qualified_players(self):
        """Test QualifiedPlayersRepository integration."""
        print("\n📋 TEST 6: Repository Pattern - Qualified Players")

        qualified_repo = get_qualified_players_repository()

        # Test save qualified player
        try:
            qualified_repo.save_qualified_player(
                player_id='QUAL-001',
                player_name='Qualified Player',
                first_name='Mario',
                last_name='Rossi',
                phone_number='+39123456789',
                score_minutes=4.5,
                score_formatted='04:30',
                player_type='couple',
                qualification_reason='top_3',
                qualification_date='2026-02-03',
                created_at='2026-02-03T14:30:00'
            )
            self.assert_test(True, "Save qualified player via repository")
        except Exception as e:
            self.assert_test(False, "Save qualified player via repository", str(e))

        # Test find qualified by type
        qualified = qualified_repo.find_qualified_by_type('couple', limit=3)
        self.assert_test(
            len(qualified) >= 1,
            "Find qualified by type"
        )

        # Test is qualified
        is_qualified = qualified_repo.is_player_qualified('QUAL-001')
        self.assert_test(
            is_qualified == True,
            "Check if player is qualified"
        )

    # ========================================================================
    # TEST 7: PlayerService Integration
    # ========================================================================

    def test_player_service(self):
        """Test PlayerService integration."""
        print("\n📋 TEST 7: PlayerService Integration")

        # Test save contact
        contact_data = {
            'player_id': 'PS-001',
            'player_name': 'Service Test',
            'first_name': 'Luigi',
            'last_name': 'Verdi',
            'phone_number': '+39987654321',
            'score_minutes': 3.5,
            'player_type': 'couple',
            'qualification_reason': 'best_today'
        }

        try:
            response, status = self.player_service.save_contact_info(contact_data)
            self.assert_test(
                status == 200,
                "PlayerService save contact"
            )

            self.assert_test(
                response['success'] == True,
                "Save contact successful"
            )
        except Exception as e:
            self.assert_test(False, "PlayerService save contact", str(e))

        # Test get skipped players
        skipped = self.player_service.get_skipped_players()
        self.assert_test(
            isinstance(skipped, dict),
            "Get skipped players"
        )

        self.assert_test(
            'couples' in skipped,
            "Skipped players has couples key"
        )

    # ========================================================================
    # TEST 8: SchedulingService Integration
    # ========================================================================

    def test_scheduling_service(self):
        """Test SchedulingService integration."""
        print("\n📋 TEST 8: SchedulingService Integration")

        scheduling_service = get_scheduling_service()

        # Test calculate waiting time
        try:
            wait_time = scheduling_service.calculate_waiting_time(
                player_type='couple',
                position=2,
                queue_lengths={'couples': 5, 'singles': 3},
                timing_params={'t_mid': 2.0, 't_total': 5.0, 't_single': 2.0}
            )
            self.assert_test(
                wait_time >= 0,
                "Calculate waiting time"
            )
        except Exception as e:
            self.assert_test(False, "Calculate waiting time", str(e))

        # Test calculate throughput
        try:
            throughput = scheduling_service.calculate_throughput(
                timing_params={'t_mid': 2.0, 't_total': 5.0, 't_single': 2.0},
                track_set=1
            )
            self.assert_test(
                'couples_per_hour' in throughput,
                "Calculate throughput"
            )

            self.assert_test(
                throughput['couples_per_hour'] > 0,
                "Throughput value correct"
            )
        except Exception as e:
            self.assert_test(False, "Calculate throughput", str(e))

        # Test suggest optimization
        try:
            suggestions = scheduling_service.suggest_queue_optimization(
                queue_lengths={'couples': 10, 'couples2': 2, 'singles': 5, 'singles2': 5},
                timing_params={'t_total': 5.0, 't_charlie': 3.0},
                track_availability={'alfa': True, 'bravo': False}
            )
            self.assert_test(
                isinstance(suggestions, dict),
                "Suggest queue optimization"
            )
        except Exception as e:
            self.assert_test(False, "Suggest queue optimization", str(e))

    # ========================================================================
    # TEST 9: Backward Compatibility
    # ========================================================================

    def test_backward_compatibility(self):
        """Test backward compatibility with legacy functions."""
        print("\n📋 TEST 9: Backward Compatibility")

        # Test legacy get_player_service
        legacy_service = get_player_service()
        self.assert_test(
            legacy_service is not None,
            "Legacy get_player_service works"
        )

        self.assert_test(
            isinstance(legacy_service, PlayerService),
            "Legacy service returns PlayerService"
        )

        # Test GameBackend properties delegation
        self.assert_test(
            hasattr(self.backend, 'queue_couples'),
            "GameBackend has queue_couples property"
        )

        self.assert_test(
            hasattr(self.backend, 'current_player_alfa'),
            "GameBackend has current_player_alfa property"
        )

        self.assert_test(
            hasattr(self.backend, 'T_mid'),
            "GameBackend has T_mid property"
        )

        # Test property delegation works
        couples = self.backend.queue_couples
        self.assert_test(
            isinstance(couples, list),
            "Property delegation returns correct type"
        )

    # ========================================================================
    # TEST 10: End-to-End Flow
    # ========================================================================

    def test_end_to_end_flow(self):
        """Test complete end-to-end flow."""
        print("\n📋 TEST 10: End-to-End Flow")

        # 1. Add players to queue
        self.backend.add_couple('GIALLO-E2E', 'E2E Team Alpha')
        self.backend.add_single('BLU-E2E', 'E2E Player Beta')

        self.assert_test(
            len(self.backend.queue_couples) >= 1,
            "E2E: Players added to queue"
        )

        # 2. Start game
        self.backend.start_game(is_couple=True)

        self.assert_test(
            self.backend.current_player_alfa is not None,
            "E2E: Game started"
        )

        # 3. Mark mid point
        self.backend.button_third_pressed()

        self.assert_test(
            self.backend.can_stop_couple() == True,
            "E2E: Mid point marked"
        )

        # 4. Record game
        self.backend.record_couple_game(4.5, 5.0)

        self.assert_test(
            len(self.backend.couple_history_total) > 0,
            "E2E: Game recorded"
        )

        # 5. Save score via repository
        scoring_repo = get_scoring_repository()
        scoring_repo.save_score(
            player_id='GIALLO-E2E',
            player_name='E2E Team Alpha',
            player_type='couple',
            score=5.0
        )

        # 6. Check if score was saved
        saved_score = scoring_repo.find_by_player_id('GIALLO-E2E')

        self.assert_test(
            saved_score is not None,
            "E2E: Score saved to database"
        )

        self.assert_test(
            saved_score['score'] == 5.0,
            "E2E: Score value correct"
        )

        # 7. Save qualified player
        qualified_repo = get_qualified_players_repository()
        qualified_repo.save_qualified_player(
            player_id='GIALLO-E2E',
            player_name='E2E Team Alpha',
            first_name='E2E',
            last_name='Test',
            phone_number='+39000000000',
            score_minutes=5.0,
            score_formatted='05:00',
            player_type='couple',
            qualification_reason='test',
            qualification_date='2026-02-03',
            created_at='2026-02-03T15:00:00'
        )

        # 8. Verify qualification
        is_qualified = qualified_repo.is_player_qualified('GIALLO-E2E')

        self.assert_test(
            is_qualified == True,
            "E2E: Player qualified"
        )

        print("\n  🎉 End-to-End flow completed successfully!")

    # ========================================================================
    # Run All Tests
    # ========================================================================

    def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "="*70)
        print("🚀 INTEGRATION TESTS SUITE")
        print("="*70)

        self.setup()

        try:
            self.test_gamebackend_initialization()
            self.test_queue_operations()
            self.test_track_operations()
            self.test_timing_operations()
            self.test_repository_scoring()
            self.test_repository_qualified_players()
            self.test_player_service()
            self.test_scheduling_service()
            self.test_backward_compatibility()
            self.test_end_to_end_flow()
        finally:
            self.teardown()

        # Print results
        print("\n" + "="*70)
        print("📊 TEST RESULTS")
        print("="*70)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📈 Success Rate: {self.results['passed']/(self.results['passed']+self.results['failed'])*100:.1f}%")

        if self.results['errors']:
            print("\n❌ Errors:")
            for error in self.results['errors']:
                print(f"  - {error}")

        print("\n" + "="*70)

        if self.results['failed'] == 0:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Integration is working correctly!")
            print("✅ Ready for production!")
        else:
            print("⚠️  SOME TESTS FAILED")
            print("Please review the errors above")

        print("="*70 + "\n")

        return self.results['failed'] == 0


def main():
    """Main test runner."""
    suite = IntegrationTestSuite()
    success = suite.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
