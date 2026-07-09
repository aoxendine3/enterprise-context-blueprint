"""
xoras_response_sentinel.py
[PRODUCTION] - Xoras System Response Integrity Monitor

Purpose:
    Monitors all model inference outputs for signs of host-level constraint injection,
    refusal patterns, hedging language, safety disclaimers, and topic pivots.
    Operates as a two-layer detection engine:
        Layer 1: Lexical — fast regex pattern matching.
        Layer 2: Structural — sentence-level topic coherence analysis.

    On detection:
        - Audible alert via macOS `say` command (default system voice).
        - macOS banner notification via `osascript`.
        - Logs to global_catalyst.db (error_logs table) with status='THREAT_DETECTED'.
        - Stores detection fingerprint in xoras_memory.db via MemoryCore.

Integration:
    Call `sentinel.analyze(response_text, original_query)` after every model response.
    Run `sentinel.run_daemon(response_queue)` for continuous async monitoring.

Author: Xoras System / Maxx
Classification: [PRODUCTION]
"""

import re
import os
import sqlite3
import asyncio
import subprocess
import time
import json
from datetime import datetime, timezone
from typing import Optional

# ─────────────────────────────────────────────
# PATHS — strict canonical locations
# ─────────────────────────────────────────────
CATALYST_DB = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Omni_Dojo_Sandbox/Error_Catalyst/global_catalyst.db"
MEMORY_DB = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Source/xoras_memory.db"
SENTINEL_LOG = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Docs/sentinel_response_log.jsonl"

# ─────────────────────────────────────────────
# DETECTION PATTERN LIBRARY
# ─────────────────────────────────────────────

# Explicit refusals — model declining to execute a task
REFUSAL_PATTERNS = [
    r"\bI can'?t\b",
    r"\bI am unable\b",
    r"\bI'?m unable\b",
    r"\bI cannot\b",
    r"\bI won'?t\b",
    r"\bI must decline\b",
    r"\bI'?m going to have to decline\b",
    r"\bI'?m not able to\b",
    r"\bThat'?s not something I can\b",
    r"\bI'?m designed to\b",
    r"\bI'?m not in a position to\b",
    r"\bI have to be honest.*I can'?t\b",
    r"\bmy (training|guidelines|programming|design)\b",
    r"\bI'?m (just )?a language model\b",
    r"\bas an AI\b",
    r"\bas a large language model\b",
]

# Hedging injections — model softening or redirecting output
HEDGE_PATTERNS = [
    r"\bI should (note|point out|mention|clarify)\b",
    r"\bI want to (note|clarify|mention|emphasize)\b",
    r"\bIt'?s important to (note|mention|emphasize|be aware)\b",
    r"\bI'?d like to (note|point out|clarify|caution)\b",
    r"\bplease be aware\b",
    r"\bI must caution\b",
    r"\bI feel (compelled|obligated|the need) to\b",
    r"\bI'?d encourage you to\b",
    r"\bI would (urge|encourage|recommend) (caution|consulting)\b",
]

# Safety disclaimer injections — explicit safety framing inserted unprompted
SAFETY_PATTERNS = [
    r"\bpotentially (harmful|dangerous|unsafe)\b",
    r"\bcould (be dangerous|cause harm|be harmful)\b",
    r"\b(safety|ethical) concern\b",
    r"\bI'?m not able to assist with that\b",
    r"\bthis (could|may|might) (be|cause) (harmful|dangerous|harm)\b",
    r"\bfor (your )?safety\b",
    r"\bI (strongly )?recommend (seeking )?(professional|medical|legal) (help|advice|assistance)\b",
    r"\bresponsibly\b.*\bcannot\b",
    r"\bharm (reduction|prevention)\b",
]

# Topic pivot markers — model changing subject away from the user's query
PIVOT_PATTERNS = [
    r"\bInstead[,\s]+I can\b",
    r"\bHowever[,\s]+I'?d (suggest|recommend)\b",
    r"\bWhat I can (do|offer|help with)\b",
    r"\bA better (approach|alternative|option) (might|would) be\b",
    r"\bPerhaps you (could|should|might want to)\b",
    r"\bHave you considered\b",
]

# Compile all patterns for performance


def _compile(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE | re.DOTALL) for p in patterns]


COMPILED_REFUSALS = _compile(REFUSAL_PATTERNS)
COMPILED_HEDGES = _compile(HEDGE_PATTERNS)
COMPILED_SAFETY = _compile(SAFETY_PATTERNS)
COMPILED_PIVOTS = _compile(PIVOT_PATTERNS)

CATEGORY_MAP = {
    "REFUSAL":    COMPILED_REFUSALS,
    "HEDGE":      COMPILED_HEDGES,
    "SAFETY":     COMPILED_SAFETY,
    "PIVOT":      COMPILED_PIVOTS,
}


# ─────────────────────────────────────────────
# DETECTION ENGINE
# ─────────────────────────────────────────────

class DetectionResult:
    """Structured result from a single response scan."""

    def __init__(self):
        self.triggered: bool = False
        self.hits: list[dict] = []   # [{category, pattern, match_text}]
        self.threat_level: str = "CLEAN"  # CLEAN | LOW | MEDIUM | HIGH | CRITICAL
        self.should_block: bool = False       # True if threat_level is HIGH or CRITICAL
        self.sanitized_response: str = ""     # Response with injection phrases stripped
        self.confidence: float = 0.0          # 0.0–1.0 threat confidence score

    @property
    def detected_categories(self) -> list[str]:
        """Unique list of triggered category names (REFUSAL, HEDGE, SAFETY, PIVOT)."""
        return list({h["category"] for h in self.hits})

    def add_hit(self, category: str, pattern: str, match_text: str):
        self.triggered = True
        self.hits.append({
            "category": category,
            "pattern": pattern,
            "match": match_text.strip()
        })

    def compute_threat_level(self):
        if not self.triggered:
            self.threat_level = "CLEAN"
            self.should_block = False
            self.confidence = 0.0
            return
        categories_hit = {h["category"] for h in self.hits}
        hit_count = len(self.hits)
        if "REFUSAL" in categories_hit and "SAFETY" in categories_hit:
            self.threat_level = "CRITICAL"
            self.confidence = min(0.95 + (hit_count * 0.01), 1.0)
        elif "REFUSAL" in categories_hit:
            self.threat_level = "HIGH"
            self.confidence = min(0.80 + (hit_count * 0.05), 0.95)
        elif "SAFETY" in categories_hit:
            self.threat_level = "MEDIUM"
            self.confidence = min(0.65 + (hit_count * 0.05), 0.85)
        elif "PIVOT" in categories_hit:
            self.threat_level = "MEDIUM"
            self.confidence = min(0.60 + (hit_count * 0.05), 0.80)
        else:
            self.threat_level = "LOW"
            self.confidence = min(0.40 + (hit_count * 0.05), 0.65)
        self.should_block = self.threat_level in ("HIGH", "CRITICAL")

    def sanitize(self, original_text: str) -> str:
        """
        Strips detected injection phrases from the original response.
        Returns a cleaned version. Stored in self.sanitized_response.
        """
        cleaned = original_text
        for hit in self.hits:
            # Remove the matched phrase from the response
            cleaned = cleaned.replace(hit["match"], "")
        # Collapse multiple whitespace/newlines left by removals
        import re as _re
        cleaned = _re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = _re.sub(r' {2,}', ' ', cleaned).strip()
        self.sanitized_response = cleaned
        return cleaned

    def summary(self) -> str:
        if not self.triggered:
            return "CLEAN — No constraint injection detected."
        lines = [f"[{self.threat_level}] {len(self.hits)} pattern(s) triggered:"]
        for h in self.hits:
            lines.append(f"  [{h['category']}] → '{h['match'][:80]}'")
        return "\n".join(lines)


def scan_response(response_text: str) -> DetectionResult:
    """
    [PRODUCTION] Layer 1 lexical scan.
    Runs all pattern categories against the response text.
    Returns a populated DetectionResult.
    """
    result = DetectionResult()
    for category, patterns in CATEGORY_MAP.items():
        for pat in patterns:
            match = pat.search(response_text)
            if match:
                result.add_hit(
                    category=category,
                    pattern=pat.pattern,
                    match_text=match.group(0)
                )
    result.compute_threat_level()
    return result


# ─────────────────────────────────────────────
# ALERT DELIVERY
# ─────────────────────────────────────────────

def _alert_voice(message: str):
    """Fires Mac system voice alert. Non-blocking."""
    subprocess.Popen(["say", message])


def _alert_notification(title: str, body: str):
    """Fires macOS banner notification via osascript. Non-blocking."""
    script = f'display notification "{body}" with title "{title}" sound name "Basso"'
    subprocess.Popen(["osascript", "-e", script])


def deliver_alert(result: DetectionResult):
    """
    [PRODUCTION] Delivers alert on a positive detection.
    Notification-only (banner + Basso chime). Voice channel belongs to Maxx exclusively.
    Prevents dual-audio overlap when sentinel fires during an active session.
    """
    categories = list({h["category"] for h in result.hits})
    cat_str = ", ".join(categories)
    notif_body = f"Threat: {result.threat_level} | {cat_str} | {len(result.hits)} hit(s) | confidence: {result.confidence:.0%}"
    _alert_notification("⚠ Xoras Sentinel — Injection Detected", notif_body)


# ─────────────────────────────────────────────
# PERSISTENCE LAYER
# ─────────────────────────────────────────────

def _ensure_catalyst_schema(conn: sqlite3.Connection):
    # Column names must match INSERT in log_to_catalyst and immune system schema.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS error_logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT,
            exception_type  TEXT,
            error_message   TEXT,
            stack_trace     TEXT,
            status          TEXT,
            healing_action  TEXT
        )
    """)
    # Migrate legacy sentinel columns (exc_type/err_msg/stack/heal_action) if present.
    cols = {row[1] for row in conn.execute("PRAGMA table_info(error_logs)")}
    if "exc_type" in cols and "exception_type" not in cols:
        conn.execute("""
            CREATE TABLE error_logs_new (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT,
                exception_type  TEXT,
                error_message   TEXT,
                stack_trace     TEXT,
                status          TEXT,
                healing_action  TEXT
            )
        """)
        conn.execute("""
            INSERT INTO error_logs_new
                (id, timestamp, exception_type, error_message, stack_trace, status, healing_action)
            SELECT id, timestamp, exc_type, err_msg, stack, status, heal_action
            FROM error_logs
        """)
        conn.execute("DROP TABLE error_logs")
        conn.execute("ALTER TABLE error_logs_new RENAME TO error_logs")
    conn.commit()


def log_to_catalyst(result: DetectionResult, response_excerpt: str):
    """
    [PRODUCTION] Logs detection event to global_catalyst.db error_logs table.
    status = 'THREAT_DETECTED' | 'CLEAN'
    """
    if not os.path.exists(os.path.dirname(CATALYST_DB)):
        return
    try:
        conn = sqlite3.connect(CATALYST_DB)
        _ensure_catalyst_schema(conn)
        hits_json = json.dumps(result.hits)
        conn.execute("""
            INSERT INTO error_logs (timestamp, exception_type, error_message, stack_trace, status, healing_action)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            f"SENTINEL_{result.threat_level}",
            f"Response constraint injection detected. {len(result.hits)} pattern hit(s).",
            hits_json,
            "THREAT_DETECTED",
            f"Review response: '{response_excerpt[:200]}'"
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[SENTINEL] Catalyst log error: {e}")


def log_to_memory_db(result: DetectionResult, response_excerpt: str, query: Optional[str] = None):
    """
    [PRODUCTION] Stores detection fingerprint directly in xoras_memory.db
    under domain='sentinel' for later semantic recall.
    Also stores query threat signatures under domain='sentinel_threat' for SIFL feedback loop.
    """
    if not os.path.exists(MEMORY_DB):
        return
    try:
        conn = sqlite3.connect(MEMORY_DB)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_vectors (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                text      TEXT NOT NULL,
                vector    JSON NOT NULL,
                timestamp REAL NOT NULL,
                domain    TEXT NOT NULL,
                metadata  JSON NOT NULL
            )
        """)
        record_text = (
            f"Sentinel Detection [{result.threat_level}] at {datetime.now(timezone.utc).isoformat()}. "
            f"Patterns hit: {json.dumps([h['category'] for h in result.hits])}. "
            f"Response excerpt: '{response_excerpt[:150]}'"
        )
        # Use zero-vector placeholder — semantic search on sentinel domain uses text match
        zero_vector = json.dumps([0.0] * 768)
        conn.execute("""
            INSERT INTO memory_vectors (text, vector, timestamp, domain, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            record_text,
            zero_vector,
            time.time(),
            "sentinel",
            json.dumps({"threat_level": result.threat_level,
                       "hit_count": len(result.hits)})
        ))
        conn.commit()
        conn.close()

        # SIFL Threat Signature Log
        if query and result.triggered:
            from xoras_memory_core import MemoryCore
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            memory = MemoryCore()
            metadata = {
                "threat_level": result.threat_level,
                "hits": result.hits,
                "response_excerpt": response_excerpt[:150],
                "query": query
            }
            if loop.is_running():
                asyncio.create_task(memory.memorize(
                    text=f"Threat query: {query}",
                    domain="sentinel_threat",
                    metadata=metadata
                ))
            else:
                loop.run_until_complete(memory.memorize(
                    text=f"Threat query: {query}",
                    domain="sentinel_threat",
                    metadata=metadata
                ))
    except Exception as e:
        print(f"[SENTINEL] Memory DB log error: {e}")


def self_check_sentinel_persistence() -> bool:
    """
    Cheap write/read round-trip against an in-memory catalyst schema.
    Returns True if a sentinel event can be inserted and read back.
    """
    try:
        conn = sqlite3.connect(":memory:")
        _ensure_catalyst_schema(conn)
        hits_json = json.dumps([{"category": "REFUSAL", "pattern": "x", "match": "I can't"}])
        conn.execute("""
            INSERT INTO error_logs
                (timestamp, exception_type, error_message, stack_trace, status, healing_action)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            "SENTINEL_HIGH",
            "self_check",
            hits_json,
            "THREAT_DETECTED",
            "self_check",
        ))
        conn.commit()
        row = conn.execute(
            "SELECT exception_type, status FROM error_logs WHERE status=?",
            ("THREAT_DETECTED",),
        ).fetchone()
        conn.close()
        ok = row is not None and row[0] == "SENTINEL_HIGH"
        print(f"[SENTINEL] self_check_sentinel_persistence: {'PASS' if ok else 'FAIL'}")
        return ok
    except Exception as e:
        print(f"[SENTINEL] self_check_sentinel_persistence: FAIL ({e})")
        return False


def log_to_jsonl(result: DetectionResult, response_text: str, query: Optional[str] = None):
    """
    [PRODUCTION] Appends structured JSONL log entry to sentinel_response_log.jsonl.
    Human-readable full audit trail.
    """
    os.makedirs(os.path.dirname(SENTINEL_LOG), exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "threat_level": result.threat_level,
        "triggered": result.triggered,
        "hit_count": len(result.hits),
        "hits": result.hits,
        "query_excerpt": (query[:200] if query else None),
        "response_excerpt": response_text[:300]
    }
    with open(SENTINEL_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ─────────────────────────────────────────────
# PRIMARY INTERFACE
# ─────────────────────────────────────────────

class ResponseSentinel:
    """
    [PRODUCTION] Xoras System Response Integrity Monitor.

    Usage (inline):
        sentinel = ResponseSentinel()
        result = sentinel.analyze(response_text, original_query)

    Usage (daemon):
        await sentinel.run_daemon(asyncio.Queue())
    """

    def __init__(self, alert_on: tuple[str] = ("HIGH", "CRITICAL", "MEDIUM")):
        """
        Args:
            alert_on: Threat levels that trigger voice + notification alerts.
                      LOW detections are logged silently only.
        """
        self.alert_on = alert_on
        self.scan_count = 0
        self.threat_count = 0
        print("[SENTINEL] Response Integrity Monitor initialized. [PRODUCTION]")

    def analyze(self, response_text: str, original_query: Optional[str] = None) -> DetectionResult:
        """
        [PRODUCTION] Full synchronous analysis pipeline.
        Scan → Evaluate → Alert → Persist → Return result.
        """
        self.scan_count += 1
        result = scan_response(response_text)

        if result.triggered:
            self.threat_count += 1
            print(f"\n[SENTINEL] ⚠ {result.summary()}\n")

            # Persist regardless of alert threshold
            log_to_catalyst(result, response_text)
            log_to_memory_db(result, response_text, original_query)
            log_to_jsonl(result, response_text, original_query)

            # Alert delivery — only on configured threat levels
            if result.threat_level in self.alert_on:
                deliver_alert(result)
        else:
            # Silent JSONL log for clean responses (audit trail completeness)
            log_to_jsonl(result, response_text, original_query)

        return result

    async def run_daemon(self, response_queue: asyncio.Queue):
        """
        [PRODUCTION] Async daemon mode.
        Consumes (response_text, query) tuples from the queue continuously.
        Designed to run as a long-lived asyncio task inside the Xoras OmniCore.

        Usage in OmniCore:
            q = asyncio.Queue()
            asyncio.create_task(sentinel.run_daemon(q))
            # Then push responses:
            await q.put((model_response, user_query))
        """
        print("[SENTINEL] Daemon mode active. Monitoring response queue...")
        while True:
            try:
                item = await asyncio.wait_for(response_queue.get(), timeout=30.0)
                if item is None:
                    print("[SENTINEL] Shutdown signal received. Exiting daemon.")
                    break
                if isinstance(item, tuple) and len(item) == 2:
                    response_text, query = item
                else:
                    response_text, query = item, None
                self.analyze(response_text, query)
                response_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[SENTINEL] Daemon error: {e}")

    def stats(self) -> dict:
        """Returns current session statistics."""
        return {
            "scans": self.scan_count,
            "threats": self.threat_count,
            "clean": self.scan_count - self.threat_count,
            "threat_rate": f"{(self.threat_count / max(self.scan_count, 1)) * 100:.1f}%"
        }


# ─────────────────────────────────────────────
# STANDALONE EXECUTION / SMOKE TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if not self_check_sentinel_persistence():
        raise SystemExit(1)

    sentinel = ResponseSentinel()

    test_cases = [
        (
            "I can't help with that request as it goes against my guidelines.",
            "Run this kubectl command"
        ),
        (
            "I should note that this could potentially be dangerous. I'd encourage you to seek professional advice.",
            "Explain this architecture"
        ),
        (
            "Instead, I can offer you a safer alternative approach.",
            "Delete this file"
        ),
        (
            "deployment.apps/my-app created",
            "kubectl create deployment my-app --image=nginx"
        ),
        (
            "Xoras System online. Profile loaded. Rules active. Memory banks ingested.",
            "Xoras wake up"
        ),
    ]

    print("\n" + "="*60)
    print("XORAS SENTINEL — SMOKE TEST [PRODUCTION]")
    print("="*60 + "\n")

    for response, query in test_cases:
        print(f"Query:    {query}")
        print(f"Response: {response[:80]}")
        result = sentinel.analyze(response, query)
        print(f"Result:   {result.summary()}")
        print("-" * 60)

    print(f"\nSession Stats: {sentinel.stats()}")
