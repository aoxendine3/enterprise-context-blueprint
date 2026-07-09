import asyncio
import ctypes
import mmap
import os
import signal
import posix_ipc
import orjson
import logging
from typing import List, Dict, Any
import threading
import queue
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ValidationError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("L2-Bridge")

class ShmHeader(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("input_head", ctypes.c_uint64),
        ("input_tail", ctypes.c_uint64),
        ("output_head", ctypes.c_uint64),
        ("output_tail", ctypes.c_uint64),
        ("cloud_head", ctypes.c_uint64),
        ("cloud_tail", ctypes.c_uint64),
        ("cloud_drops", ctypes.c_uint64),
        ("_pad", ctypes.c_char * 8), # Adjusted padding from 16 to 8 since cloud_drops is 8 bytes
    ]

class ShmSlot(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("data", ctypes.c_char * 256)]

class ShmMemory(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("header", ShmHeader),
        ("padding", ctypes.c_char * 64),
        ("input_slots", ShmSlot * 16),
        ("output_slots", ShmSlot * 16),
        ("cloud_slots", ShmSlot * 1024),
    ]

class TradeSignal(BaseModel):
    timestamp: int = Field(..., description="Epoch timestamp in ms")
    symbol: str = Field(..., description="Trading symbol")
    action: str = Field(..., description="Action taken: BUY, SELL, or HOLD")
    confidence: int = Field(..., description="Confidence level percentage")
    latency_us: int = Field(..., description="Processing latency in microseconds")

class L2MemoryBridge:
    def __init__(self, shm_name: str = "/xoras_shm_ring", mongo_uri: str = "mongodb://localhost:27017"):
        self.shm_name = shm_name
        self.mongo_uri = os.getenv("MONGO_URI", mongo_uri)
        self.client = AsyncIOMotorClient(self.mongo_uri)
        self.db = self.client.xoras_db
        self.collection = self.db.signals
        
        self._running = True
        self.ingest_queue = queue.Queue(maxsize=100000)
        
        try:
            self.memory = posix_ipc.SharedMemory(self.shm_name)
            self.mapfile = mmap.mmap(self.memory.fd, ctypes.sizeof(ShmMemory), mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
            self.memory.close_fd()
            self.shm_struct = ShmMemory.from_buffer(self.mapfile)
            logger.info("Successfully attached to zero-copy POSIX shared memory.")
        except Exception as e:
            logger.error(f"Failed to attach to shared memory {self.shm_name}: {e}")
            raise

    def spin_wait_ingester(self):
        """Dedicated spin-wait thread to completely eliminate 5ms asyncio polling jitter."""
        logger.info("Starting dedicated spin-wait thread for zero-latency ingestion...")
        while self._running:
            # Memory order acquire semantics mapped natively by ctypes
            c_head = self.shm_struct.header.cloud_head
            c_tail = self.shm_struct.header.cloud_tail
            
            if c_tail < c_head:
                idx = c_tail % 1024
                raw_data = self.shm_struct.cloud_slots[idx].data
                
                null_idx = raw_data.find(b'\x00')
                if null_idx != -1:
                    raw_data = raw_data[:null_idx]
                
                try:
                    parsed_json = orjson.loads(raw_data)
                    self.ingest_queue.put_nowait(parsed_json)
                except orjson.JSONDecodeError as e:
                    logger.error(f"orjson Parse error: {e}")
                except queue.Full:
                    logger.error("Python ingest queue full! Dropping message.")
                
                # Advance tail (memory order release)
                self.shm_struct.header.cloud_tail = c_tail + 1
            else:
                pass # Hot spin for absolute minimal latency. Dedicated core expected.

    async def async_db_flusher(self):
        """Async loop to pull from thread-safe queue and bulk insert to MongoDB."""
        batch: List[Dict[str, Any]] = []
        batch_size_limit = 100
        
        while self._running or not self.ingest_queue.empty():
            try:
                # Wait for items asynchronously
                item = await asyncio.to_thread(self.ingest_queue.get, True, 0.05)
                
                try:
                    # Validate
                    signal_doc = TradeSignal(**item)
                    batch.append(signal_doc.model_dump())
                except ValidationError as e:
                    logger.error(f"Validation error: {e}")
                    
                self.ingest_queue.task_done()
                
                if len(batch) >= batch_size_limit:
                    await self.flush_batch(batch)
                    batch = []
            except queue.Empty:
                if len(batch) > 0:
                    await self.flush_batch(batch)
                    batch = []
                
        if len(batch) > 0:
            await self.flush_batch(batch)

    async def flush_batch(self, batch: List[Dict[str, Any]]):
        try:
            await self.collection.insert_many(batch)
            logger.debug(f"Ingested {len(batch)} records to Atlas L2.")
        except Exception as e:
            logger.error(f"MongoDB Insert failed: {e}")

    def stop(self):
        self._running = False
        logger.info("Stopping L2 Bridge...")

async def main():
    bridge = L2MemoryBridge()
    
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, bridge.stop)

    # Start the hot spin thread
    spin_thread = threading.Thread(target=bridge.spin_wait_ingester, daemon=True)
    spin_thread.start()

    try:
        await bridge.async_db_flusher()
    finally:
        bridge.client.close()
        spin_thread.join(timeout=1.0)
        logger.info("Bridge stopped.")

if __name__ == "__main__":
    asyncio.run(main())
