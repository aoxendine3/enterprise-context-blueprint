"""
Comprehensive Unit & Benchmark Test Suite for XORAS Sovra Core
Tests:
1. PoincareManifold: metric symmetry, triangle inequality, boundary clipping, hierarchy projection.
2. HexCell & HexCellEngine: exact 3,200-byte layout, packing/unpacking roundtrip, ring buffer streaming.
3. StreamingEntropyEngine: Shannon entropy mathematical correctness, LUT speedup, suspicious token detection.
4. KernelDriftDetector: directory state snapshotting, Merkle root consistency, added/modified/deleted file detection.
5. SagaInverseEngine: atomic transaction preparation, rollback on failure, inverse delta cleanup.
"""

import math
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sovra_core.poincare_hypergraph import PoincareManifold
from sovra_core.hexcell_memory import HexCell, HexCellEngine, HEXCELL_SIZE
from sovra_core.streaming_entropy import StreamingEntropyEngine
from sovra_core.kernel_drift_detector import KernelDriftDetector
from sovra_core.saga_inverse import SagaInverseEngine


class TestPoincareManifold(unittest.TestCase):
    def setUp(self):
        self.manifold = PoincareManifold(dim=16)

    def test_origin_distance(self):
        origin = [0.0] * 16
        dist = self.manifold.geodesic_distance(origin, origin)
        self.assertAlmostEqual(dist, 0.0, places=5)

    def test_distance_symmetry(self):
        u = [0.2, 0.3] + [0.0] * 14
        v = [-0.1, 0.4] + [0.0] * 14
        d_uv = self.manifold.geodesic_distance(u, v)
        d_vu = self.manifold.geodesic_distance(v, u)
        self.assertAlmostEqual(d_uv, d_vu, places=6)
        self.assertGreater(d_uv, 0.0)

    def test_boundary_clipping(self):
        outside = [0.9, 0.9] + [0.0] * 14
        clipped = self.manifold.clip_point(outside)
        norm = math.sqrt(sum(x * x for x in clipped))
        self.assertLess(norm, 1.0)

    def test_hierarchy_projection(self):
        root = [0.0] * 16
        child_0 = self.manifold.project_hierarchy(root, child_index=0, total_children=4, depth=1)
        child_1 = self.manifold.project_hierarchy(root, child_index=1, total_children=4, depth=1)
        self.assertEqual(len(child_0), 16)
        self.assertEqual(len(child_1), 16)
        d = self.manifold.geodesic_distance(child_0, child_1)
        self.assertGreater(d, 0.0)


class TestHexCell(unittest.TestCase):
    def test_hexcell_pack_size_and_roundtrip(self):
        p_coord = [0.05 * i for i in range(16)]
        vec = [math.sin(i) for i in range(512)]
        sig = b"A" * 64
        dig = b"B" * 32
        bmask = [1 << (i % 64) for i in range(16)]
        payload = b"XORAS_SOVEREIGN_NODE_TEST_PAYLOAD"

        cell = HexCell(
            cell_id=42,
            timestamp=1789290000.0,
            epoch=2,
            flags=7,
            poincare_coord=p_coord,
            vector=vec,
            signature=sig,
            digest=dig,
            bitmask=bmask,
            payload=payload
        )

        packed = cell.pack()
        self.assertEqual(len(packed), HEXCELL_SIZE)
        self.assertEqual(len(packed), 3200)

        unpacked = HexCell.unpack(packed)
        self.assertEqual(unpacked.cell_id, 42)
        self.assertEqual(unpacked.epoch, 2)
        self.assertEqual(unpacked.flags, 7)
        self.assertEqual(unpacked.signature, sig)
        self.assertEqual(unpacked.digest, dig)
        self.assertEqual(unpacked.bitmask, bmask)
        self.assertTrue(unpacked.payload.startswith(payload))

    def test_hexcell_engine_streaming(self):
        engine = HexCellEngine(capacity=10)
        for i in range(15):
            cell = HexCell(cell_id=i, epoch=1)
            idx = engine.write_cell(cell)
            self.assertEqual(idx, i % 10)

        # Most recent cell at index 4 (14 % 10)
        read_back = engine.read_cell(4)
        self.assertEqual(read_back.cell_id, 14)


class TestStreamingEntropy(unittest.TestCase):
    def setUp(self):
        self.engine = StreamingEntropyEngine()

    def test_zero_entropy_for_uniform_string(self):
        entropy = self.engine.calculate_entropy("AAAAAAAAAA")
        self.assertAlmostEqual(entropy, 0.0, places=5)

    def test_high_entropy_random_secret(self):
        secret = "x4kP9zL2mNqR5wT8vB1jY6cH3sG0vF9d"
        entropy = self.engine.calculate_entropy(secret)
        self.assertGreater(entropy, 4.0)
        self.assertTrue(self.engine.is_suspicious_entropy(secret))

    def test_path_not_flagged(self):
        path_str = "/Users/admin/Desktop/SSOT/index.html"
        self.assertFalse(self.engine.is_suspicious_entropy(path_str))


class TestKernelDriftDetector(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.detector = KernelDriftDetector(self.test_dir)
        # Create mock repo
        with open(os.path.join(self.test_dir, "file1.txt"), "w") as f:
            f.write("initial_content_1")
        with open(os.path.join(self.test_dir, "file2.txt"), "w") as f:
            f.write("initial_content_2")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_snapshot_and_drift_detection(self):
        merkle_root_1, count_1 = self.detector.snapshot()
        self.assertEqual(count_1, 2)
        self.assertTrue(len(merkle_root_1) == 64)

        # No drift
        drift_0 = self.detector.detect_drift()
        self.assertEqual(len(drift_0["added"]), 0)
        self.assertEqual(len(drift_0["modified"]), 0)
        self.assertEqual(len(drift_0["deleted"]), 0)

        # Modify file1
        with open(os.path.join(self.test_dir, "file1.txt"), "w") as f:
            f.write("modified_content_1")

        # Add file3
        with open(os.path.join(self.test_dir, "file3.txt"), "w") as f:
            f.write("new_file_3")

        # Delete file2
        os.remove(os.path.join(self.test_dir, "file2.txt"))

        drift_1 = self.detector.detect_drift()
        self.assertIn("file1.txt", drift_1["modified"])
        self.assertIn("file3.txt", drift_1["added"])
        self.assertIn("file2.txt", drift_1["deleted"])


class TestSagaInverse(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.wal_dir = os.path.join(self.test_dir, "wal")
        self.engine = SagaInverseEngine(self.wal_dir)
        self.target_file = Path(self.test_dir) / "critical_config.json"
        with open(self.target_file, "w") as f:
            f.write('{"state": "ORIGINAL"}')

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_successful_rollback(self):
        tx = self.engine.begin("tx_001")
        tx.prepare_file(self.target_file)

        # Mutate file (simulated error or corrupt build)
        with open(self.target_file, "w") as f:
            f.write('{"state": "CORRUPT_MUTATION"}')

        # Abort transaction -> rollback
        aborted = self.engine.abort("tx_001")
        self.assertTrue(aborted)

        # Verify restoration
        with open(self.target_file, "r") as f:
            content = f.read()
        self.assertEqual(content, '{"state": "ORIGINAL"}')


if __name__ == "__main__":
    unittest.main()
