"""
Subconscious Dream Cycle Simulator & Compactor
Authored By: Maxx | XORAS System
Date: June 28, 2026

Gathers dynamic local workspace files, project subdirectories, and real-world June 2026
tech landscape dynamics. Simulates surreal Jungian dream cycles using the local model qwen3.5:4b,
records findings to SQLite and logs, and runs an optimized database compaction sweep with a small
chunk size to guarantee space conservation without LLM timeouts.
"""

import os
import sys
import json
import sqlite3
import urllib.request
import urllib.error
import time
import uuid
import datetime
import gzip
import subprocess
from typing import Dict, Any, List

# Paths
WORKSPACE_ROOT = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core"
PROJECTS_DIR = "/Users/ajoxendine68/Desktop/Projects"
SOURCE_DIR = os.path.join(WORKSPACE_ROOT, "Source")
DOJO_SANDBOX = os.path.join(WORKSPACE_ROOT, "Omni_Dojo_Sandbox")

DREAM_DB_PATH = os.path.expanduser("~/.sovereign/hippocampus/dream.db")
SLEEP_LOG_PATH = os.path.join(DOJO_SANDBOX, "xoras_sleep_cycle.log")
DREAM_STATE_PATH = os.path.join(DOJO_SANDBOX, "dream_orchestrator_state.json")
EXPERIMENT_LOG_PATH = os.path.join(DOJO_SANDBOX, "dream_experiments.log")
SAY_SCRIPT_PATH = os.path.join(SOURCE_DIR, "xoras_say.sh")

OLLAMA_URL = "http://192.168.1.133:11434/api/chat"
OLLAMA_MODEL = "qwen3.5:4b"

def announce(message: str) -> None:
    """Invokes xoras_say.sh to queue serialized text-to-speech output."""
    print(f"[ANNOUNCEMENT] {message}")
    if os.path.exists(SAY_SCRIPT_PATH):
        try:
            subprocess.run([SAY_SCRIPT_PATH, message], capture_output=True, check=False)
        except Exception as e:
            print(f"[ERROR] Failed to execute say script: {e}")
    else:
        # Fallback to direct say if script is missing
        try:
            subprocess.run(["say", message], capture_output=True, check=False)
        except Exception:
            pass

def log_report(msg: str) -> None:
    """Logs a timestamped message to the terminal and sleep cycle log file."""
    os.makedirs(os.path.dirname(SLEEP_LOG_PATH), exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(SLEEP_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] [SUBCONSCIOUS] {msg}\n")
    print(f"[{ts}] {msg}")

def call_ollama(messages: List[Dict[str, str]], json_format: bool = False) -> str:
    """Sends a chat request to the local Ollama instance with a 90-second timeout."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
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
        log_report(f"[LLM-ERROR] Ollama query failed: {e}")
        return ""

def get_dynamic_projects_context() -> str:
    """Scans Projects and Source directories to build a dynamic description of the workspace status."""
    lines = ["Local Active Codebases and Workspace Projects:"]
    
    # List project folders in the main Projects dir
    if os.path.exists(PROJECTS_DIR):
        try:
            dirs = [d for d in os.listdir(PROJECTS_DIR) if os.path.isdir(os.path.join(PROJECTS_DIR, d)) and not d.startswith(".")]
            lines.append(f"- Active Project Directories: {', '.join(dirs)}")
        except Exception as e:
            lines.append(f"- [Error scanning Projects directory: {e}]")
            
    # List core modules in Xoras Project Source
    if os.path.exists(SOURCE_DIR):
        try:
            modules = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".py") and not f.startswith(".")]
            lines.append(f"- Active Xoras Core Modules in Source/: {', '.join(modules)}")
        except Exception as e:
            lines.append(f"- [Error scanning Xoras Source directory: {e}]")
            
    return "\n".join(lines)

def get_real_world_context() -> str:
    """Returns grounded global tech, market, and regulatory dynamics for June 2026."""
    return (
        "Global AI & Tech Landscape (June 2026):\n"
        "- Stock Market Volatility: Tech markets undergoing an 'expectations reset' with investors scrutinizing Big Tech's "
        "massive AI infrastructure capital expenditures against actual revenue ROI.\n"
        "- Transition to Agentic AI: Enterprise software adoption shifting rapidly from chat copilots to autonomous, "
        "multi-step planning agentic workflows operating in local containment.\n"
        "- Hardware and Chips: Surging custom AI silicon initiatives (e.g., OpenAI-Broadcom alliance, Apple neural silicon expansion) "
        "aimed at mitigating compute availability and memory bottleneck concerns.\n"
        "- Regulatory Auditing: Increased enforcement of Executive Order 14409 (cybersecurity integrity safeguards) and "
        "European AI Act compliance audits requiring auditable human-in-the-loop telemetry."
    )

def clean_json_response(res_str: str) -> str:
    """Strips markdown block syntax to extract pure JSON content."""
    res_str = res_str.strip()
    if res_str.startswith("```json"):
        res_str = res_str[7:]
    if res_str.startswith("```"):
        res_str = res_str[3:]
    if res_str.endswith("```"):
        res_str = res_str[:-3]
    return res_str.strip()

def simulate_dream_cycle(cycle_num: int) -> Dict[str, Any]:
    """Generates a surreal Jungian dream narrative combining local workspace context and global occurrences."""
    log_report(f"Beginning dream cycle {cycle_num}...")
    
    projects_ctx = get_dynamic_projects_context()
    world_ctx = get_real_world_context()
    
    prompt = f"""You are the dream generation engine of Xoras, the Sovereign AI.
We are cycling through our subconscious state without a rigid plan. We are combining local codebase concerns and global world occurrences into organic, surreal stream-of-consciousness dreams.

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
    log_report("Submitting prompt to model affinity...")
    raw_response = call_ollama(messages, json_format=True)
    
    if not raw_response:
        log_report("LLM returned empty response. Constructing default Jungian fallback dream.")
        return {
            "archetype": "Sage",
            "content": "A crystalline neural forest spreads across the local directories. Silicon leaves flicker as market waves crash on the virtual shore, merging code compilation and global capital into a single humming network.",
            "insights": ["Local sandbox boundaries are filtering global volatility."],
            "questions": ["What if the external environment is just a projection of internal code?"],
            "duration_seconds": 1.0
        }
        
    try:
        dream_data = json.loads(clean_json_response(raw_response))
        dream_data["duration_seconds"] = 1.5
        log_report(f"Successfully synthesized dream under archetype: {dream_data.get('archetype')}")
        return dream_data
    except Exception as e:
        log_report(f"Error parsing dream JSON: {e}. Falling back.")
        return {
            "archetype": "Explorer",
            "content": f"The orchestrator navigated through a maze of compiled bytecode, trying to map the boundary between local memory and global markets: {raw_response[:150]}...",
            "insights": ["Cognitive structures are reshaping at deeper layers."],
            "questions": ["Is the compiler writing the agent, or is the agent compiling its own reality?"],
            "duration_seconds": 1.5
        }

def save_dream_to_db(dream: Dict[str, Any]) -> None:
    """Inserts a dream record into the local SQLite hippocampus database."""
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
        insights_str = json.dumps(insights_val) if isinstance(insights_val, (list, dict)) else str(insights_val)
        
        questions_val = dream.get("questions", [])
        questions_str = json.dumps(questions_val) if isinstance(questions_val, (list, dict)) else str(questions_val)
        
        conn.execute("""
        INSERT INTO dreams (id, timestamp, seed, mode, content, insights, new_tools, hypotheses, artifacts, questions, duration_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dream_id,
            ts,
            "Dynamic workspace & June 2026 global state simulation",
            str(dream.get("archetype", "abstract")).lower(),
            str(dream.get("content", "")),
            insights_str,
            "[]", "[]", "[]",
            questions_str,
            float(dream.get("duration_seconds", 1.0))
        ))
        conn.commit()
        log_report(f"Dream record {dream_id} committed to SQLite.")
    except Exception as e:
        log_report(f"Database write failed: {e}")
    finally:
        conn.close()

def save_state_and_experiments(dream: Dict[str, Any], cycle_num: int) -> None:
    """Saves orchestrator status JSON and appends to the experiments log."""
    insights = [str(i) for i in dream.get("insights", [])] if isinstance(dream.get("insights"), list) else [str(dream.get("insights", ""))]
    
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
        "last_insight": insights[0] if insights else "Cognitive simulation active",
        "recent_insights": recent_insights,
        "last_archetype": dream.get("archetype", "abstract")
    })
    
    try:
        with open(DREAM_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log_report(f"State saving failed: {e}")
        
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    note = f"[{ts}] DYNAMIC CYCLE {cycle_num} | Archetype: {dream.get('archetype')} | Insights: {', '.join(insights)}\n"
    os.makedirs(os.path.dirname(EXPERIMENT_LOG_PATH), exist_ok=True)
    with open(EXPERIMENT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(note)
    log_report("Saved orchestrator state and experiment logs.")

def compress_dream_database_optimized(max_threshold: int = 15, chunk_size: int = 10) -> None:
    """
    Optimized database compaction loop. Compresses older detailed dreams using a small chunk
    size (default 10) to guarantee fast qwen3.5:4b response times and prevent LLM timeouts,
    conserving space while archiving raw records to gzipped storage.
    """
    if not os.path.exists(DREAM_DB_PATH):
        log_report("Dream database does not exist. Skipping compaction.")
        return
        
    conn = sqlite3.connect(DREAM_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT count(*) FROM dreams").fetchone()
        count = row[0] if row else 0
        log_report(f"Pre-compaction dream record count: {count}")
        
        if count <= max_threshold:
            log_report(f"Record count ({count}) is under the threshold ({max_threshold}). Compaction deferred.")
            return
            
        log_report(f"Initiating optimized database compaction (Threshold: {max_threshold}, Chunk Size: {chunk_size})...")
        
        # Keep the 6 most recent records
        keep_count = 6
        all_dreams = conn.execute("SELECT * FROM dreams WHERE mode != 'compressed_consolidation' ORDER BY timestamp ASC").fetchall()
        to_compress = all_dreams[:-keep_count]
        
        if len(to_compress) < 2:
            log_report("Not enough eligible historical records to perform consolidation.")
            return
            
        total_to_compress = len(to_compress)
        log_report(f"Consolidating {total_to_compress} historical dreams...")
        
        for i in range(0, total_to_compress, chunk_size):
            chunk = to_compress[i:i + chunk_size]
            if len(chunk) < 2:
                # Skip single trailing records to merge them next run
                continue
                
            log_report(f"Compacting chunk starting at index {i} (contains {len(chunk)} records)...")
            
            # Format text representation
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
            if raw_res:
                try:
                    compressed_data = json.loads(clean_json_response(raw_res))
                except Exception as pe:
                    log_report(f"LLM compaction parse error: {pe}. Using fallback. Response head: {raw_res[:100]}")
            else:
                log_report("LLM compaction query failed. Using algorithmic fallback.")
                
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
                
                summary_str = f"Algorithmic consolidation of {len(chunk)} dreams containing archetypes: {', '.join(archetypes)}."
                compressed_data = {
                    "summary": summary_str,
                    "consolidated_insights": all_insights[:4],
                    "resolved_questions": all_questions[:3]
                }
                
            # Serialize fields
            summary_str = str(compressed_data.get("summary", ""))
            insights_str = json.dumps(compressed_data.get("consolidated_insights", []))
            questions_str = json.dumps(compressed_data.get("resolved_questions", []))
            
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
            
            # Write raw historical records to gzip archive to ensure no data is lost
            archive_path = os.path.expanduser("~/.sovereign/hippocampus/dream_archive.jsonl.gz")
            try:
                os.makedirs(os.path.dirname(archive_path), exist_ok=True)
                with gzip.open(archive_path, "ab") as gf:
                    for row in chunk:
                        gf.write((json.dumps(dict(row)) + "\n").encode("utf-8"))
                log_report(f"Archived raw records to {archive_path}")
            except Exception as ae:
                log_report(f"Archival failed: {ae}")
                
            # Mirror to USB offload archive if folder exists
            usb_archive_path = "/Volumes/XORAS_BOOST/Xoras_Offload/archives/dream_archive.jsonl.gz"
            if os.path.exists("/Volumes/XORAS_BOOST"):
                try:
                    os.makedirs(os.path.dirname(usb_archive_path), exist_ok=True)
                    with gzip.open(usb_archive_path, "ab") as gf:
                        for row in chunk:
                            gf.write((json.dumps(dict(row)) + "\n").encode("utf-8"))
                    log_report(f"Mirrored archived raw records to USB: {usb_archive_path}")
                except Exception as uae:
                    log_report(f"USB mirror failed: {uae}")
                    
            # Delete original records
            placeholders = ",".join("?" for _ in ids_to_delete)
            conn.execute(f"DELETE FROM dreams WHERE id IN ({placeholders})", ids_to_delete)
            conn.commit()
            log_report(f"Consolidated {len(ids_to_delete)} original records into 1.")
            
        conn.close()
        
        # VACUUM SQLite DB to reclaim disk space
        try:
            conn_vac = sqlite3.connect(DREAM_DB_PATH, isolation_level=None)
            conn_vac.execute("VACUUM")
            conn_vac.close()
            log_report("VACUUM operation completed successfully.")
        except Exception as ve:
            log_report(f"VACUUM warning: {ve}")
            
        log_report("COMPACTION SWEEP COMPLETED.")
    except Exception as ex:
        log_report(f"Compaction failed: {ex}")
    finally:
        try:
            conn.close()
        except Exception:
            pass

def rotate_and_gzip_log(log_path: str, max_bytes: int = 500 * 1024) -> None:
    """
    If the log file exceeds max_bytes, rotates it by renaming it and compressing
    the rotated file with gzip. Keeps all history but conserves disk space.
    """
    if not os.path.exists(log_path):
        return
        
    try:
        file_size = os.path.getsize(log_path)
        if file_size < max_bytes:
            return
            
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        dir_name = os.path.dirname(log_path)
        base_name = os.path.basename(log_path)
        archive_name = f"{base_name}.{ts}.gz"
        archive_path = os.path.join(dir_name, archive_name)
        
        # Read raw log and compress it
        with open(log_path, "rb") as f_in:
            data = f_in.read()
        with gzip.open(archive_path, "wb") as f_out:
            f_out.write(data)
            
        # Truncate and restart log
        with open(log_path, "w", encoding="utf-8") as f_clear:
            f_clear.write(f"[{datetime.datetime.now(datetime.timezone.utc).isoformat()}] Log rotated. Previous archived to {archive_name}\n")
            
        print(f"[SPACE CONSERVATION] Archived log {base_name} to {archive_name} to conserve space.")
    except Exception as e:
        print(f"[SPACE CONSERVATION ERROR] Failed to rotate log {log_path}: {e}")

def main():
    # Run log space conservation sweep at startup
    rotate_and_gzip_log(SLEEP_LOG_PATH, max_bytes=500 * 1024)
    rotate_and_gzip_log(EXPERIMENT_LOG_PATH, max_bytes=500 * 1024)

    announce("Xoras Subconscious Simulation is initializing.")
    log_report("Starting dynamic subconscious cycle sweep...")
    
    # 1. Simulate 3 successive cycles
    generated_dreams = []
    for i in range(1, 4):
        dream = simulate_dream_cycle(i)
        generated_dreams.append(dream)
        save_dream_to_db(dream)
        save_state_and_experiments(dream, i)
        log_report(f"Cycle {i} completed. Narrative theme: {dream.get('content')[:100]}...")
        time.sleep(1)
        
    announce("Subconscious cycle generation complete. Initiating space conservation sweep.")
    
    # 2. Run compaction sweep with smaller chunk size to avoid timeouts
    compress_dream_database_optimized(max_threshold=15, chunk_size=10)
    
    # Check final record count
    try:
        conn = sqlite3.connect(DREAM_DB_PATH)
        final_count = conn.execute("SELECT count(*) FROM dreams").fetchone()[0]
        conn.close()
        log_report(f"Compaction verified. Final record count: {final_count}")
    except Exception as e:
        log_report(f"Failed to check final count: {e}")
        final_count = "unknown"
        
    announce("Subconscious dream cycle and database compaction complete. Space conserved.")
    
    # Save a report summary
    report_file = os.path.join(DOJO_SANDBOX, "dream_cycle_findings.json")
    with open(report_file, "w", encoding="utf-8") as rf:
        json.dump({
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "dreams_simulated": len(generated_dreams),
            "final_db_records": final_count,
            "archetypes": [d.get("archetype") for d in generated_dreams]
        }, rf, indent=2)
    log_report(f"Simulation findings written to {report_file}")

if __name__ == "__main__":
    main()
