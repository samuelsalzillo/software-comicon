"""
Quick integration test to identify issues.
"""
import os
import sys
import tempfile
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_basic_imports():
    """Test basic imports work."""
    print("TEST 1: Basic imports...")
    try:
        from src.model.GameBackend import GameBackend
        from src.service.service_player import PlayerService
        from src.repository import get_scoring_repository
        print("  ✅ All imports successful")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_gamebackend_init():
    """Test GameBackend initialization."""
    print("\nTEST 2: GameBackend initialization...")
    try:
        # Setup temp database
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        os.environ['SQLITE_DB_PATH'] = db_path
        
        # Initialize database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mid_times (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                couple_type TEXT,
                mid_duration_minutes REAL
            )
        """)
        conn.commit()
        conn.close()
        
        from src.model.GameBackend import GameBackend
        backend = GameBackend()
        
        print(f"  ✅ GameBackend initialized")
        print(f"     - QueueManager: {type(backend.queue_manager).__name__}")
        print(f"     - TrackManager: {type(backend.track_manager).__name__}")
        print(f"     - TimingManager: {type(backend.timing_manager).__name__}")
        
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
        
        return True
    except Exception as e:
        print(f"  ❌ GameBackend init failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_repository():
    """Test repository operations."""
    print("\nTEST 3: Repository operations...")
    try:
        # Setup temp database
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        os.environ['SQLITE_DB_PATH'] = db_path
        
        # Initialize database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scoring (
                player_id TEXT PRIMARY KEY,
                player_name TEXT,
                player_type TEXT,
                score REAL,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()
        
        from src.repository import get_scoring_repository
        scoring_repo = get_scoring_repository()
        
        # Test save
        scoring_repo.save_score(
            player_id='TEST-001',
            player_name='Test Player',
            player_type='couple',
            score=4.5
        )
        
        # Test retrieve
        player = scoring_repo.find_by_player_id('TEST-001')
        
        if player and player['score'] == 4.5:
            print("  ✅ Repository operations successful")
            success = True
        else:
            print("  ❌ Repository operations failed")
            success = False
        
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
        
        return success
    except Exception as e:
        print(f"  ❌ Repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_queue_operations():
    """Test queue operations."""
    print("\nTEST 4: Queue operations...")
    try:
        # Setup temp database
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        os.environ['SQLITE_DB_PATH'] = db_path
        
        # Initialize database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mid_times (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                couple_type TEXT,
                mid_duration_minutes REAL
            )
        """)
        conn.commit()
        conn.close()
        
        from src.model.GameBackend import GameBackend
        backend = GameBackend()
        
        # Test add to queue
        backend.add_couple('GIALLO-001', 'Team Alpha')
        backend.add_single('BLU-001', 'Player Beta')
        
        if len(backend.queue_couples) == 1 and len(backend.queue_singles) == 1:
            print("  ✅ Queue operations successful")
            success = True
        else:
            print(f"  ❌ Queue operations failed: couples={len(backend.queue_couples)}, singles={len(backend.queue_singles)}")
            success = False
        
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
        
        return success
    except Exception as e:
        print(f"  ❌ Queue operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run quick tests."""
    print("="*70)
    print("QUICK INTEGRATION TEST")
    print("="*70)
    
    results = []
    
    results.append(("Basic Imports", test_basic_imports()))
    results.append(("GameBackend Init", test_gamebackend_init()))
    results.append(("Repository Operations", test_repository()))
    results.append(("Queue Operations", test_queue_operations()))
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    exit(main())
