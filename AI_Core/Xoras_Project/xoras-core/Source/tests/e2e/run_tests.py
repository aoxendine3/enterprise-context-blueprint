import os
import sys

# Ensure workspace root and Source folder are in sys.path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, workspace_root)
sys.path.insert(0, os.path.join(workspace_root, 'Source'))

from Source.tests.e2e.import_helper import get_xoras_vector_db
import unittest
import time
import statistics

# Set XORAS_TEST_MODE default to mock
if "XORAS_TEST_MODE" not in os.environ:
    os.environ["XORAS_TEST_MODE"] = "mock"

# Dynamically import vector db to instrument it

db_mod = get_xoras_vector_db()
query_times = []
original_query = db_mod.query_semantic_memory


def instrumented_query(query, limit=10):
    start = time.perf_counter()
    res = original_query(query, limit)
    elapsed = (time.perf_counter() - start) * 1000.0  # in ms
    query_times.append(elapsed)
    return res


db_mod.query_semantic_memory = instrumented_query


def main():
    print(f"Starting E2E Test Suite in Mode: {os.environ['XORAS_TEST_MODE']}")

    loader = unittest.defaultTestLoader
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.perf_counter()
    result = runner.run(suite)
    end_time = time.perf_counter()

    total_time = (end_time - start_time) * 1000.0  # in ms

    total_run = result.testsRun
    failures_count = len(result.failures)
    errors_count = len(result.errors)
    skipped_count = len(result.skipped)
    passed_count = total_run - failures_count - errors_count - skipped_count

    print("\n" + "="*50)
    print(" E2E TEST SUMMARY")
    print("="*50)
    print(f"Total Tests Run: {total_run}")
    print(f"Passed:         {passed_count}")
    print(f"Failed:         {failures_count}")
    print(f"Errors:         {errors_count}")
    print(f"Skipped:        {skipped_count}")
    print(f"Execution Time: {total_time:.2f} ms")

    if query_times:
        min_lat = min(query_times)
        max_lat = max(query_times)
        avg_lat = statistics.mean(query_times)
        median_lat = statistics.median(query_times)
        print(f"\nQuery Latency SLA Metrics (Total Queries: {len(query_times)}):")
        print(f"  Min Query Time:    {min_lat:.2f} ms")
        print(f"  Max Query Time:    {max_lat:.2f} ms")
        print(f"  Avg Query Time:    {avg_lat:.2f} ms")
        print(f"  Median Query Time: {median_lat:.2f} ms")

        sla_violation = False
        for t in query_times:
            if t >= 500.0:
                print(
                    f"  [SLA VIOLATION] Query latency exceeded 500ms limit: {t:.2f} ms")
                sla_violation = True

        if sla_violation:
            print("\nTest runner failed due to query latency SLA violations.")
            sys.exit(1)
    else:
        print("\nNo queries executed during the test run.")

    if not result.wasSuccessful():
        print("\nTest runner failed due to test failures or errors.")
        sys.exit(1)

    print("\nAll tests passed successfully under latency SLA.")
    sys.exit(0)


if __name__ == '__main__':
    main()
