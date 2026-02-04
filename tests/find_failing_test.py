"""
Script to identify the failing test.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.test_integration import IntegrationTestSuite

def main():
    suite = IntegrationTestSuite()
    suite.setup()

    print("\n" + "="*70)
    print("TESTING INDIVIDUAL TESTS TO FIND FAILURE")
    print("="*70)

    tests = [
        ("GameBackend Initialization", suite.test_gamebackend_initialization),
        ("Queue Operations", suite.test_queue_operations),
        ("Track Operations", suite.test_track_operations),
        ("Timing Operations", suite.test_timing_operations),
        ("Repository Scoring", suite.test_repository_scoring),
        ("Repository Qualified Players", suite.test_repository_qualified_players),
        ("PlayerService Integration", suite.test_player_service),
        ("SchedulingService Integration", suite.test_scheduling_service),
        ("Backward Compatibility", suite.test_backward_compatibility),
        ("End-to-End Flow", suite.test_end_to_end_flow),
    ]

    for name, test_func in tests:
        print(f"\n{'='*70}")
        print(f"Running: {name}")
        print('='*70)

        passed_before = suite.results['passed']
        failed_before = suite.results['failed']

        test_func()

        passed_after = suite.results['passed']
        failed_after = suite.results['failed']

        tests_in_this = (passed_after - passed_before) + (failed_after - failed_before)
        failed_in_this = failed_after - failed_before

        if failed_in_this > 0:
            print(f"\n⚠️  {name}: {failed_in_this} test(s) FAILED")
            print(f"   Errors: {suite.results['errors'][-failed_in_this:]}")
        else:
            print(f"\n✅ {name}: All tests passed")

    suite.teardown()

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total Passed: {suite.results['passed']}")
    print(f"Total Failed: {suite.results['failed']}")

    if suite.results['errors']:
        print("\n❌ All Errors:")
        for error in suite.results['errors']:
            print(f"  - {error}")

if __name__ == '__main__':
    main()
