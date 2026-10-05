import asyncio
import json
import os
import time

FIFO_PATH = "/tmp/xoras_audio_queue.fifo"

class AudioQueueDaemon:
    def __init__(self):
        self.queue = asyncio.PriorityQueue()
        self.manifest_path = "identity/sovereign_citizens_manifest.json"
        self.engine_script = "core/ops/scripts/fullscreen_ui/sync_stage_engine_kokoro.py"
        
        if not os.path.exists(FIFO_PATH):
            os.mkfifo(FIFO_PATH)
            
    def validate_citizen(self, agent_id):
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
        for c in manifest.get('citizens', []):
            if c['agent_id'] == agent_id:
                return True
        return False
        
    async def worker(self):
        while True:
            priority, timestamp, agent_id, text = await self.queue.get()
            if not self.validate_citizen(agent_id):
                print(f"[AudioQueue] FAULT: Unverified '{agent_id}'. Dropped.")
                self.queue.task_done()
                continue
                
            # Block the worker while playing to avoid overlapping audio
            os.system(f"python3 {self.engine_script} '{agent_id}' '{text}'")
            self.queue.task_done()

    async def listener(self):
        while True:
            # Read from FIFO
            with open(FIFO_PATH, 'r') as f:
                data = f.read().strip()
                if not data:
                    await asyncio.sleep(0.1)
                    continue
                try:
                    payload = json.loads(data)
                    agent_id = payload['agent']
                    text = payload['text']
                    priority = 1 if agent_id == 'jarvis' else 2
                    await self.queue.put((priority, time.time(), agent_id, text))
                except Exception as e:
                    pass

    async def run(self):
        asyncio.create_task(self.worker())
        await self.listener()

if __name__ == "__main__":
    daemon = AudioQueueDaemon()
    asyncio.run(daemon.run())
