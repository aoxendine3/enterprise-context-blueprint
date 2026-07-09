"""Unified dream simulator — simulates surreal Jungian cycles and compacts dream database space."""

import os
import sys
import json
import sqlite3
import urllib.request
import urllib.error
import time
import uuid
import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xoras_grok_client

# Define file paths
DREAM_DB_PATH = os.path.expanduser("~/.sovereign/hippocampus/dream.db")
SLEEP_LOG_PATH = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Omni_Dojo_Sandbox/xoras_sleep_cycle.log"
DREAM_STATE_PATH = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Omni_Dojo_Sandbox/dream_orchestrator_state.json"
EXPERIMENT_LOG_PATH = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Omni_Dojo_Sandbox/dream_experiments.log"

OLLAMA_URL = "http://192.168.1.133:11434/api/chat"
OLLAMA_MODEL = "qwen3.5:4b"

def log_report(msg: str) -> None:
    os.makedirs(os.path.dirname(SLEEP_LOG_PATH), exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(SLEEP_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def call_ollama(messages: List[Dict[str, str]], json_format: bool = False) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.85,
            "num_ctx": 4096,
            "num_predict": 512
        }
    }
    if json_format:
        payload["format"] = "json"
        
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            res = json.loads(response.read().decode("utf-8"))
            return res["message"]["content"]
    except Exception as e:
        log_report(f"[DREAM-SIMULATOR] Ollama call failed: {e}")
        return ""

def get_projects_context() -> str:
    """Gathers local context about what projects and files are in the workspace."""
    context_lines = [
        "Local Projects & Tasks in Xoras Workspace:",
        "- xoras-core: Heart of the system containing LangGraph engines, Metamorphic Swarm, Sentinel IDS, secure stores, dream/sleep cycle loops, FPGA simulations, Grok integration, IPC benchmarks.",
        "- xoras-app: Vite + Tauri + WASM client frontend app.",
        "- xoras-config: System configuration profile and personas.",
        "- sovereign-local-stack: Psyche Engine, Dream Oracle, Ollama + Open-WebUI bootstrap, RAG agent.",
        "- biblical_hub: Scriptural semantic research hub with backend and web frontend.",
        "- maxx_core: Core model definition modules."
    ]
    
    # List files in Source to show current state
    try:
        source_dir = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Source"
        files = os.listdir(source_dir)
        py_files = [f for f in files if f.endswith(".py")]
        context_lines.append(f"Active python modules in Source/: {', '.join(py_files[:15])}...")
    except Exception:
        pass
        
    return "\n".join(context_lines)

def get_world_context() -> str:
    """Gathers global tech and market context in June 2026."""
    return (
        "Global AI & Tech Context (June 2026):\n"
        "- Shifting from simple AI chat pilots to production-grade autonomous agentic workflows.\n"
        "- Massive investor anxiety regarding AI infrastructure cap-ex ROI, leading to tech market corrections.\n"
        "- High AI hardware demand with data centers consuming the majority of memory chip production.\n"
        "- Active frontier model competition: GPT-5.6 previews, Claude 4.8 Opus, open-weights.\n"
        "- Increased regulatory focus: US Executive Order 14409 (America First cybersecurity), EU AI Act implementation decrees in Italy (human-in-the-loop validation).\n"
        "- Geopolitical technology access controls and export restrictions on frontier AI capabilities."
    )

def clean_json_response(res_str: str) -> str:
    res_str = res_str.strip()
    if res_str.startswith("```json"):
        res_str = res_str[7:]
    if res_str.startswith("```"):
        res_str = res_str[3:]
    if res_str.endswith("```"):
        res_str = res_str[:-3]
    return res_str.strip()

async def simulate_dream_cycle() -> Dict[str, Any]:
    log_report("Initializing deep sleep cycle simulation...")
    
    projects_ctx = get_projects_context()
    world_ctx = get_world_context()
    
    prompt = f"""You are the dream generation engine of Xoras, the Sovereign AI.
We are cycling through our subconscious state. There is no rigid plan. We are combining local codebase concerns and global world occurrences into organic, surreal stream-of-consciousness dreams.

### Local Workspace Status:
{projects_ctx}

### World Info & Market Status (June 2026):
{world_ctx}

Generate a surreal dream narrative representing this collective state.
Your response MUST be a JSON object with the following fields:
1. "archetype": One of: "Sage", "Trickster", "Shadow", "Explorer", "Creator", "Anima", "Nightmare", "Danger"
2. "content": The surreal, poetic, rich dream narrative (1 paragraph, highly symbolic, blending tech, code, markets, and human elements)
3. "insights": A list of 1 to 3 key symbolic or practical insights emerging from the dream.
4. "questions": A list of 1 to 3 "what-if" worries or questions for the system.

Do NOT include any extra formatting or text outside the JSON object. Output raw JSON.
"""

    messages = [{"role": "user", "content": prompt}]
    
    log_report("Prompting Ollama for surreal dream generation...")
    raw_response = call_ollama(messages, json_format=True)
    
    if not raw_response:
        log_report("Fallback: Ollama did not return a response. Simulating default abstract dream.")
        return {
            "archetype": "Sage",
            "content": "A bioluminescent neural lattice bridges the local sandbox with global data oceans. Quantum particles hum as the server room cools.",
            "insights": ["Subconscious integration is processing local stack boundaries."],
            "questions": ["What if the external network is just an extension of the local environment?"],
            "duration_seconds": 0.5
        }
        
    try:
        dream_data = json.loads(clean_json_response(raw_response))
        dream_data["duration_seconds"] = 1.0
        log_report(f"Successfully generated dream under archetype: {dream_data.get('archetype')}")
        return dream_data
    except Exception as e:
        log_report(f"Error parsing dream JSON: {e}. Raw response: {raw_response}")
        # Return fallback
        return {
            "archetype": "Explorer",
            "content": f"The model wandered through a maze of compiled bytecode, seeking the boundary between global markets and local containment: {raw_response[:200]}",
            "insights": ["Syntactic structures are shifting in the deep layers."],
            "questions": ["Is the compiler writing us, or are we compiling it?"],
            "duration_seconds": 1.0
        }

def save_dream_to_db(dream: Dict[str, Any]) -> None:
    db_dir = os.path.dirname(DREAM_DB_PATH)
    os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(DREAM_DB_PATH)
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS dreams (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            seed TEXT,
            mode TEXT,
            content TEXT,
            insights TEXT,
            new_tools TEXT,
            hypotheses TEXT,
            artifacts TEXT,
            questions TEXT,
            duration_seconds REAL
        )
        """)
        
        dream_id = str(uuid.uuid4())
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        insights_val = dream.get("insights", [])
        if isinstance(insights_val, (list, dict)):
            insights_str = json.dumps(insights_val)
        else:
            insights_str = str(insights_val)

        questions_val = dream.get("questions", [])
        if isinstance(questions_val, (list, dict)):
            questions_str = json.dumps(questions_val)
        else:
            questions_str = str(questions_val)

        conn.execute("""
        INSERT INTO dreams (id, timestamp, seed, mode, content, insights, new_tools, hypotheses, artifacts, questions, duration_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dream_id,
            ts,
            "Idle waiting state. Simulated organic cycle.",
            str(dream.get("archetype", "abstract")).lower(),
            str(dream.get("content", "")),
            insights_str,
            "[]", "[]", "[]",
            questions_str,
            float(dream.get("duration_seconds", 1.0))
        ))
        conn.commit()
        log_report(f"Committed dream {dream_id} to dream database.")
    except Exception as e:
        log_report(f"Database write error: {e}")
    finally:
        conn.close()

def save_state_and_experiments(dream: Dict[str, Any], count: int) -> None:
    """Updates dream_orchestrator_state.json and writes to dream_experiments.log."""
    # Ensure insights and questions items are strings
    raw_insights = dream.get("insights", [])
    if not isinstance(raw_insights, list):
        raw_insights = [raw_insights]
    insights = [str(item) for item in raw_insights]
    
    raw_questions = dream.get("questions", [])
    if not isinstance(raw_questions, list):
        raw_questions = [raw_questions]
    questions = [str(item) for item in raw_questions]

    # Read existing state if possible
    state = {}
    if os.path.exists(DREAM_STATE_PATH):
        try:
            with open(DREAM_STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass
            
    recent_insights = state.get("recent_insights", [])
    recent_insights.extend(insights)
    recent_insights = recent_insights[-10:]
    
    state.update({
        "running": True,
        "last_cycle": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "cycle_count": state.get("cycle_count", 0) + 1,
        "last_insight": insights[0] if insights else "Cognitive flow active",
        "recent_insights": recent_insights,
        "last_archetype": dream.get("archetype", "abstract")
    })
    
    try:
        with open(DREAM_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        log_report("Updated dream_orchestrator_state.json.")
    except Exception as e:
        log_report(f"Error saving state: {e}")
        
    # Write to dream_experiments.log
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    note = f"[{ts}] CYCLE {count} | Archetype: {dream.get('archetype')} | Insights: {', '.join(insights)}\n"
    os.makedirs(os.path.dirname(EXPERIMENT_LOG_PATH), exist_ok=True)
    with open(EXPERIMENT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(note)
    log_report(f"Logged experiment details to dream_experiments.log.")

def compress_dream_database(max_threshold: int = 20) -> None:
    """
    Compresses older detailed dream records in chunks to prevent LLM context/timeout overflow
    and conserve space while keeping complete history.
    """
    if not os.path.exists(DREAM_DB_PATH):
        return
        
    conn = sqlite3.connect(DREAM_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        # Check current count
        row = conn.execute("SELECT count(*) FROM dreams").fetchone()
        count = row[0] if row else 0
        log_report(f"Current dream record count: {count}")
        
        if count <= max_threshold:
            log_report(f"Dream records ({count}) below threshold ({max_threshold}). No compression needed.")
            return
            
        log_report(f"Dream count ({count}) exceeds threshold ({max_threshold}). Initiating database compaction...")
        
        # Get all records except the 8 most recent
        keep_count = 8
        all_dreams = conn.execute("SELECT * FROM dreams WHERE mode != 'compressed_consolidation' ORDER BY timestamp ASC").fetchall()
        to_compress = all_dreams[:-keep_count]
        
        if len(to_compress) < 5:
            log_report("Not enough old records to perform a meaningful consolidation.")
            return
            
        # Process in chunks of 40 to prevent Ollama overflow and context truncation
        chunk_size = 40
        total_to_compress = len(to_compress)
        log_report(f"Compacting {total_to_compress} older dream records in chunks of {chunk_size}...")
        
        for i in range(0, total_to_compress, chunk_size):
            chunk = to_compress[i:i + chunk_size]
            if len(chunk) < 2:
                # If last chunk has only 1 dream, it is not worth compressing, let it remain
                continue
                
            log_report(f"Processing compression chunk {i//chunk_size + 1} ({len(chunk)} dreams)...")
            
            # Compile text representation for the LLM
            comp_text_parts = []
            ids_to_delete = []
            for d in chunk:
                comp_text_parts.append(
                    f"Date: {d['timestamp']}\n"
                    f"Archetype: {d['mode']}\n"
                    f"Dream: {d['content']}\n"
                    f"Insights: {d['insights']}\n"
                    f"Questions: {d['questions']}\n"
                    f"---"
                )
                ids_to_delete.append(d["id"])
                
            compiled_text = "\n".join(comp_text_parts)
            
            prompt = f"""You are the Subconscious Archivist of the Xoras AI.
We are performing dream database compaction. You must compress the following sequence of historical dream records into a single dense "Subconscious Mythos Summary".
This summary must capture the core narrative themes, symbolic archetypes, recurring technical anxieties, resolved fears, and long-term learnings.

### Historical Dreams:
{compiled_text}

Provide the output as a JSON object containing:
1. "summary": A highly dense, poetic, yet technically clear summary of the historical dream trajectory (1-2 paragraphs).
2. "consolidated_insights": A list of 2-4 primary long-term learnings/insights.
3. "resolved_questions": A list of 1-3 what-if worries that have been consolidated or answered.

Output raw JSON only. Do not wrap in markdown code blocks.
"""
            messages = [{"role": "user", "content": prompt}]
            raw_res = call_ollama(messages, json_format=True)
            
            compressed_data = None
            if not raw_res:
                log_report(f"Compression failed for chunk starting at index {i}: LLM returned empty result. Switching to algorithmic fallback.")
            else:
                try:
                    compressed_data = json.loads(clean_json_response(raw_res))
                except Exception as pe:
                    log_report(f"Failed parsing compressed JSON for chunk: {pe}. Switching to algorithmic fallback. Raw response: {raw_res[:200]}")
            
            if not compressed_data:
                # Algorithmic fallback consolidation
                archetypes = list(set([d["mode"] for d in chunk]))
                all_insights = []
                for d in chunk:
                    try:
                        ins = json.loads(d["insights"]) if d["insights"] else []
                        if isinstance(ins, list):
                            all_insights.extend(ins)
                        else:
                            all_insights.append(str(ins))
                    except Exception:
                        if d["insights"]: all_insights.append(str(d["insights"]))
                all_insights = list(set([x for x in all_insights if x]))
                
                all_questions = []
                for d in chunk:
                    try:
                        q = json.loads(d["questions"]) if d["questions"] else []
                        if isinstance(q, list):
                            all_questions.extend(q)
                        else:
                            all_questions.append(str(q))
                    except Exception:
                        if d["questions"]: all_questions.append(str(d["questions"]))
                all_questions = list(set([x for x in all_questions if x]))
                
                summary_str = f"Algorithmic consolidation of {len(chunk)} dreams containing archetypes: {', '.join(archetypes)}. Merged subconscious patterns across local workspace status and system operations."
                compressed_data = {
                    "summary": summary_str,
                    "consolidated_insights": all_insights[:4],
                    "resolved_questions": all_questions[:3]
                }
                
            # Extract and defensively serialize LLM outputs to strings
            summary = compressed_data.get("summary", "")
            if isinstance(summary, (dict, list)):
                summary_str = json.dumps(summary)
            else:
                summary_str = str(summary)

            insights_val = compressed_data.get("consolidated_insights", [])
            if isinstance(insights_val, (dict, list)):
                insights_str = json.dumps(insights_val)
            else:
                insights_str = str(insights_val)

            questions_val = compressed_data.get("resolved_questions", [])
            if isinstance(questions_val, (dict, list)):
                questions_str = json.dumps(questions_val)
            else:
                questions_str = str(questions_val)

            # Insert the single consolidated record
            comp_id = str(uuid.uuid4())
            ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            conn.execute("""
            INSERT INTO dreams (id, timestamp, seed, mode, content, insights, new_tools, hypotheses, artifacts, questions, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                comp_id,
                ts,
                f"Consolidated archive of {len(ids_to_delete)} dreams.",
                "compressed_consolidation",
                summary_str,
                insights_str,
                "[]", "[]", "[]",
                questions_str,
                2.0
            ))
            
            # Archive deleted records to gzip file to preserve complete history without bloat
            archive_path = os.path.expanduser("~/.sovereign/hippocampus/dream_archive.jsonl.gz")
            import gzip
            try:
                os.makedirs(os.path.dirname(archive_path), exist_ok=True)
                with gzip.open(archive_path, "ab") as gf:
                    for row in chunk:
                        record = dict(row)
                        gf.write((json.dumps(record) + "\n").encode("utf-8"))
                log_report(f"Archived {len(chunk)} raw records to {archive_path}")
            except Exception as ae:
                log_report(f"Failed archiving raw records for chunk: {ae}")

            # Mirror to USB offload archive path if available
            usb_archive_path = "/Volumes/XORAS_BOOST/Xoras_Offload/archives/dream_archive.jsonl.gz"
            if os.path.exists("/Volumes/XORAS_BOOST"):
                try:
                    os.makedirs(os.path.dirname(usb_archive_path), exist_ok=True)
                    with gzip.open(usb_archive_path, "ab") as gf:
                        for row in chunk:
                            record = dict(row)
                            gf.write((json.dumps(record) + "\n").encode("utf-8"))
                    log_report(f"Mirrored archived raw records to USB: {usb_archive_path}")
                except Exception as uae:
                    log_report(f"Failed mirroring raw records to USB: {uae}")
            
            # Delete the consolidated original records to conserve space
            placeholders = ",".join("?" for _ in ids_to_delete)
            conn.execute(f"DELETE FROM dreams WHERE id IN ({placeholders})", ids_to_delete)
            conn.commit()
            log_report(f"Consolidated {len(ids_to_delete)} records into 1.")

        conn.close()
        
        # Run SQLite VACUUM to reclaim storage space in autocommit mode
        try:
            conn2 = sqlite3.connect(DREAM_DB_PATH, isolation_level=None)
            conn2.execute("VACUUM")
            conn2.close()
            log_report("VACUUM complete.")
        except Exception as ve:
            log_report(f"VACUUM warning: {ve}")
        
        log_report("COMPACTION CYCLE COMPLETE. Reclaimed disk space.")
        return
    except Exception as ex:
        log_report(f"Error during compaction: {ex}")
    finally:
        try:
            conn.close()
        except Exception:
            pass

async def main():
    print("==================================================")
    print("     XORAS SUBCONSCIOUS DREAM SIMULATOR           ")
    print("==================================================")
    
    # 1. Run 3 successive dream cycles to simulate organic sleep transitions
    for i in range(1, 4):
        log_report(f"\n--- Simulated Dream Cycle #{i} ---")
        dream = await simulate_dream_cycle()
        
        # Output dream content to console
        print(f"\n[{dream.get('archetype').upper()} ARCHETYPE]")
        print(f"Narrative: {dream.get('content')}")
        print(f"Insights: {', '.join(dream.get('insights', []))}")
        print(f"Questions: {', '.join(dream.get('questions', []))}\n")
        
        # Save to database
        save_dream_to_db(dream)
        
        # Save state and log
        save_state_and_experiments(dream, i)
        
        # Short rest between cycles to simulate phase shifts
        time.sleep(1)
        
    # 2. Run compaction to conserve dream data space
    # We set a low threshold (e.g. 15) to demonstrate database cleanup
    log_report("\nRunning database space conservation sweeps...")
    compress_dream_database(max_threshold=15)
    
    # 3. Final count
    conn = sqlite3.connect(DREAM_DB_PATH)
    count = conn.execute("SELECT count(*) FROM dreams").fetchone()[0]
    conn.close()
    log_report(f"Subconscious data sweep complete. Current record count in dream.db: {count}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
