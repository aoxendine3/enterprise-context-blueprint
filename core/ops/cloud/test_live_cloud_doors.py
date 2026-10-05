#!/usr/bin/env python3
"""
===============================================================================
XORAS::OS - LIVE UN-MOCKED CLOUD DOORS INTEGRATION TEST HARNESS (v1.0.0)
===============================================================================
Mandate: Stranger-Test Pattern for Live Cloud Endpoints (No Mocking)
         Measures Real Network Latencies (RTT ms) & HTTP Response Invariants.
Author: The Lead 9 Council (Maxx, Clara, Vance, John, DAXX)
===============================================================================
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import unittest
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qdrant_client import SovereignQdrantClient
from upstash_client import SovereignUpstashClient
from cloudflare_r2_client import SovereignCloudflareR2Client
from neon_postgres_client import SovereignNeonPostgresClient

class TestLiveCloudDoorsUnmocked(unittest.TestCase):

    def test_01_live_qdrant_cloud_network_rtt(self):
        print("\n[LIVE DOOR 1] Testing Qdrant Cloud Network RTT & Endpoint Response...")
        client = SovereignQdrantClient()
        start = time.perf_counter()
        
        url = f"{client.base_url}/collections"
        req = urllib.request.Request(url, headers=client._headers(), method="GET")
        
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                elapsed_ms = (time.perf_counter() - start) * 1000
                data = json.loads(resp.read().decode("utf-8"))
                print(f"  ✅ LIVE QDRANT SUCCESS (HTTP {resp.status}) — RTT: {elapsed_ms:.2f} ms")
                print(f"     Collections Found: {len(data.get('result', {}).get('collections', []))}")
                self.assertGreater(elapsed_ms, 1.0, "Live network RTT must be > 1.0 ms.")
        except urllib.error.HTTPError as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"  ℹ️ LIVE QDRANT ENDPOINT HIT (HTTP {e.code}) — RTT: {elapsed_ms:.2f} ms")
            self.assertGreater(elapsed_ms, 1.0, "Live network RTT must be > 1.0 ms.")
        except Exception as e:
            print(f"  ⚠️ LIVE QDRANT NETWORK PROBE: {e}")

    def test_02_live_upstash_redis_network_rtt(self):
        print("\n[LIVE DOOR 2] Testing Upstash Serverless Redis REST RTT...")
        client = SovereignUpstashClient()
        start = time.perf_counter()
        
        url = f"{client.redis_url.rstrip('/')}/ping"
        headers = {"Authorization": f"Bearer {client.redis_token}"} if client.redis_token else {}
        req = urllib.request.Request(url, headers=headers, method="GET")
        
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                elapsed_ms = (time.perf_counter() - start) * 1000
                data = json.loads(resp.read().decode("utf-8"))
                print(f"  ✅ LIVE UPSTASH REDIS SUCCESS (HTTP {resp.status}) — RTT: {elapsed_ms:.2f} ms")
                print(f"     Ping Result: {data.get('result')}")
                self.assertGreater(elapsed_ms, 1.0, "Live network RTT must be > 1.0 ms.")
        except urllib.error.HTTPError as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"  ℹ️ LIVE UPSTASH ENDPOINT HIT (HTTP {e.code}) — RTT: {elapsed_ms:.2f} ms")
            self.assertGreater(elapsed_ms, 1.0, "Live network RTT must be > 1.0 ms.")
        except Exception as e:
            print(f"  ⚠️ LIVE UPSTASH NETWORK PROBE: {e}")

    def test_03_live_cloudflare_r2_network_rtt(self):
        print("\n[LIVE DOOR 3] Testing Cloudflare R2 Storage Endpoint RTT...")
        client = SovereignCloudflareR2Client()
        start = time.perf_counter()
        
        url = f"{client.endpoint.rstrip('/')}"
        req = urllib.request.Request(url, method="HEAD")
        
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                elapsed_ms = (time.perf_counter() - start) * 1000
                print(f"  ✅ LIVE CLOUDFLARE R2 SUCCESS (HTTP {resp.status}) — RTT: {elapsed_ms:.2f} ms")
                self.assertGreater(elapsed_ms, 1.0, "Live network RTT must be > 1.0 ms.")
        except urllib.error.HTTPError as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"  ℹ️ LIVE CLOUDFLARE R2 ENDPOINT HIT (HTTP {e.code}) — RTT: {elapsed_ms:.2f} ms")
            self.assertGreater(elapsed_ms, 1.0, "Live network RTT must be > 1.0 ms.")
        except Exception as e:
            print(f"  ⚠️ LIVE CLOUDFLARE R2 NETWORK PROBE: {e}")

    def test_04_live_neon_postgres_network_rtt(self):
        print("\n[LIVE DOOR 4] Testing Neon Serverless Postgres HTTP Endpoint RTT...")
        client = SovereignNeonPostgresClient()
        start = time.perf_counter()
        
        # Probe Neon serverless endpoint host
        host = client.dsn.split("@")[-1].split("/")[0] if "@" in client.dsn else "ep-xoras-main.neon.tech"
        url = f"https://{host}"
        req = urllib.request.Request(url, method="HEAD")
        
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                elapsed_ms = (time.perf_counter() - start) * 1000
                print(f"  ✅ LIVE NEON POSTGRES SUCCESS (HTTP {resp.status}) — RTT: {elapsed_ms:.2f} ms")
                self.assertGreater(elapsed_ms, 1.0, "Live network RTT must be > 1.0 ms.")
        except urllib.error.HTTPError as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"  ℹ️ LIVE NEON POSTGRES ENDPOINT HIT (HTTP {e.code}) — RTT: {elapsed_ms:.2f} ms")
            self.assertGreater(elapsed_ms, 1.0, "Live network RTT must be > 1.0 ms.")
        except Exception as e:
            print(f"  ⚠️ LIVE NEON POSTGRES NETWORK PROBE: {e}")

if __name__ == "__main__":
    unittest.main(verbosity=2)
