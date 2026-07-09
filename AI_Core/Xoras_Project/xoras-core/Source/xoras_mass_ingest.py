import os
import asyncio
from xoras_memory_core import MemoryCore


async def ingest_directory(directory_path, memory_core):
    print(f"[MASS-INGEST] Scanning {directory_path} for base data...")
    count = 0
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith((".py", ".md", ".html")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Slice content to avoid token limits (approx 1000 chars per memory block)
                    chunk_size = 1000
                    chunks = [content[i:i+chunk_size]
                              for i in range(0, len(content), chunk_size)]

                    for i, chunk in enumerate(chunks):
                        meta_text = f"File: {file} (Part {i+1}):\n{chunk}"
                        await memory_core.memorize(meta_text)
                        count += 1
                except Exception as e:
                    print(f"[MASS-INGEST] Failed to read {file}: {e}")

    print(f"\n[MASS-INGEST] Total Memory Blocks Ingested: {count}")
    print("[MASS-INGEST] Omni-System now has absolute context of its own architecture.")

if __name__ == "__main__":
    memory = MemoryCore()
    source_dir = "/Users/ajoxendine68/Desktop/Xoras_Project/Source"
    asyncio.run(ingest_directory(source_dir, memory))
