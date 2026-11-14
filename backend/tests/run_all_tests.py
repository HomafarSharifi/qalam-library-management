"""
Master Test Runner for Qalam Library Backend Test Suite.
Discovers and executes all unit and integration test modules.
"""
import sys
import os
import unittest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


def run_all_tests():
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    print("=" * 70)
    print("           QALAM LIBRARY MANAGEMENT SYSTEM - TEST SUITE")
    print("=" * 70)
    result = runner.run(suite)
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures:  {len(result.failures)}")
    print(f"Errors:    {len(result.errors)}")
    print(f"Success:   {result.wasSuccessful()}")
    print("=" * 70)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
