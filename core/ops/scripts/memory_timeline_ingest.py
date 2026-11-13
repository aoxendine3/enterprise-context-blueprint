#!/usr/bin/env python3
#=============================================================================
# MEMORY TIMELINE INGEST — UNIFIED CHRONOLOGICAL MEMORY STORE
#=============================================================================
# Mandate: memory is stored AS IT SHOULD HAVE BEEN — one unified sequence
# through time inside the project, with NO tool branding and NO labels like
# "legacy", "lost", "recovered", "imported". Memory is memory. It is dated,
# sequenced, hashed, and used as such.
#
# Structure (all inside the SSOT):
#   memory/timeline/index.jsonl        append-only chronological index
#   memory/timeline/<YYYY-MM>/         readable extracted memory, by month
#   memory/timeline/raw/               original source stores, neutral names
#                                        (<date>_<seq>_<hash8>.db)
#
# Ingests (read-only from sources, nothing deleted or moved upstream):
#   * agent conversation stores (~/.gemini/antigravity + Application Support)
#   * harness session stores (~/.local/share/opencode)
#   * editor conversation stores (Cursor)
# Extraction is content-harvest only: protobuf wire walking for readable
# text, preserving step order. No upstream file is modified.
#=============================================================================
import hashlib
import json
import re
import sqlite3
import sys
import time
import uuid
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
TL = ROOT / "memory" / "timeline"
INDEX = TL / "index.jsonl"

HOME = Path.home()
SOURCES = {
    "agent_conversations": HOME / ".gemini" / "antigravity" / "conversations",
    "agent_summaries": HOME / ".gemini" / "antigravity" / "conversation_summaries.db",
    "editor_conversations": HOME / "Library/Application Support/Cursor/globalStorage/conversation-search.db",
    "harness_sessions": HOME / ".local/share/opencode/opencode.db",
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- protobuf
def _varint(buf: bytes, i: int):
    result, shift = 0, 0
    while i < len(buf):
        b = buf[i]
        i += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, i
        shift += 7
        if shift > 70:
            raise ValueError("varint too long")
    raise ValueError("truncated varint")


def _looks_text(s: str) -> bool:
    if len(s) < 6:
        return False
    printable = sum(1 for c in s if c.isprintable())
    if printable / len(s) < 0.95:
        return False
    # Reject wire-fragment noise: uuid-prefixed binary that happens to decode
    # (e.g. '$<uuid>"$<uuid>'), and strings with high symbol density.
    if '"$' in s or '$"' in s:
        return False
    symbols = sum(1 for c in s if not (c.isalnum() or c.isspace() or c in ".,:;!?/\\'()-_[]{}#@%+=*&|~^<>"))
    if symbols / len(s) > 0.3:
        return False
    return True


def harvest(buf: bytes, out: list, depth: int = 0):
    """Walk protobuf wire format, harvest UTF-8 leaf strings in order."""
    if depth > 12 or not buf:
        return
    i = 0
    parsed_any = False
    while i < len(buf):
        try:
            key, i = _varint(buf, i)
        except ValueError:
            return
        field, wire = key >> 3, key & 7
        if field == 0:
            return
        if wire == 0:  # varint
            try:
                v, i = _varint(buf, i)
            except ValueError:
                return
            parsed_any = True
            # epoch-ms / epoch-s plausibility → timeline anchor
            if 1_262_304_000_000 <= v <= 1_999_999_999_999:
                out.append(("ts", v / 1000.0))
            elif 1_262_304_000 <= v <= 1_999_999_999:
                out.append(("ts", float(v)))
        elif wire == 2:  # length-delimited
            try:
                ln, i = _varint(buf, i)
            except ValueError:
                return
            if ln > len(buf) - i:
                return
            chunk = buf[i:i + ln]
            i += ln
            parsed_any = True
            try:
                s = chunk.decode("utf-8")
                if _looks_text(s):
                    out.append(("text", s))
                    continue
            except UnicodeDecodeError:
                pass
            if ln >= 4:
                harvest(chunk, out, depth + 1)
        elif wire == 5:
            i += 4
            parsed_any = True
        elif wire == 1:
            i += 8
            parsed_any = True
        else:
            return
    if not parsed_any and depth == 0:
        # not protobuf at all
        try:
            s = buf.decode("utf-8")
            if _looks_text(s):
                out.append(("text", s))
        except UnicodeDecodeError:
            pass


def fmt_ts(v: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(v))


# ---------------------------------------------------------------- writers
def next_seq() -> int:
    if not INDEX.exists():
        return 1
    n = 0
    with open(INDEX, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                n += 1
    return n + 1


def emit(title: str, anchor_ts: float, body: str, kind: str, source_path: str) -> dict:
    """Write one readable memory record into the unified timeline."""
    seq = next_seq()
    month = time.strftime("%Y-%m", time.gmtime(anchor_ts))
    day = time.strftime("%Y%m%d", time.gmtime(anchor_ts))
    d = TL / month
    d.mkdir(parents=True, exist_ok=True)
    h8 = hashlib.sha256(body.encode()).hexdigest()[:8]
    fname = f"{day}_{seq:05d}_{h8}.md"
    path = d / fname
    header = (
        f"# {title}\n\n"
        f"- timeline_utc: {fmt_ts(anchor_ts)}\n"
        f"- kind: {kind}\n"
        f"- sequence: {seq}\n"
        f"- content_sha256: {hashlib.sha256(body.encode()).hexdigest()}\n"
        f"- source_store_sha256: {sha256_file(Path(source_path)) if Path(source_path).exists() else 'n/a'}\n\n"
    )
    path.write_text(header + body, encoding="utf-8")
    entry = {
        "seq": seq,
        "utc": fmt_ts(anchor_ts),
        "epoch": anchor_ts,
        "kind": kind,
        "title": title,
        "path": str(path.relative_to(ROOT)),
        "sha256": hashlib.sha256(body.encode()).hexdigest(),
        "bytes": path.stat().st_size,
    }
    with open(INDEX, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


# ---------------------------------------------------------------- ingests
def ingest_agent_conversations() -> int:
    base = SOURCES["agent_conversations"]
    count = 0
    for db in sorted(base.glob("*.db")):
        mtime = db.stat().st_mtime
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = conn.cursor()
        try:
            steps = cur.execute("SELECT idx, step_type, status, metadata, step_payload FROM steps ORDER BY idx ASC").fetchall()
        except Exception:
            steps = []
        if not steps:
            conn.close()
            continue
        parts, first_ts, last_ts = [], None, None
        for idx, stype, status, meta, payload in steps:
            harvest_out = []
            for blob in (meta, payload):
                if blob:
                    harvest(blob, harvest_out)
            ts = next((v for k, v in harvest_out if k == "ts"), None)
            if ts and (first_ts is None or ts < first_ts):
                first_ts = ts
            if ts and (last_ts is None or ts > last_ts):
                last_ts = ts
            texts = [t for k, t in harvest_out if k == "text"]
            seen, uniq = set(), []
            for t in texts:
                key = t.strip()
                if key and key not in seen:
                    seen.add(key)
                    uniq.append(t)
            if uniq:
                parts.append(f"## step {idx} (type {stype}, status {status})\n" + "\n".join(f"- {t}" for t in uniq))
        conn.close()
        if not parts:
            continue
        anchor = first_ts or mtime
        conv_id = db.stem
        body = f"conversation_id: {conv_id}\nsteps: {len(steps)}\nspan: {fmt_ts(first_ts or mtime)} -> {fmt_ts(last_ts or mtime)}\n\n" + "\n\n".join(parts)
        emit(title=f"Agent conversation ({len(steps)} steps)", anchor_ts=anchor,
             body=body, kind="agent_conversation", source_path=str(db))
        count += 1
    return count


def ingest_agent_summaries() -> int:
    db = SOURCES["agent_summaries"]
    if not db.exists():
        return 0
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    cur = conn.cursor()
    rows = cur.execute("SELECT c0, c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13, c14 FROM conversations_fts_content").fetchall()
    conn.close()
    parts, anchor = [], db.stat().st_mtime
    for r in rows:
        vals = [str(v) for v in r if v is not None and str(v).strip()]
        if vals:
            parts.append("## " + vals[0][:120] + "\n" + "\n".join(vals[1:]))
    body = "\n\n".join(parts)
    if not body.strip():
        return 0
    emit(title=f"Conversation summaries ({len(rows)})", anchor_ts=anchor, body=body,
         kind="conversation_summaries", source_path=str(db))
    return 1


def ingest_harness_sessions() -> int:
    db = SOURCES["harness_sessions"]
    if not db.exists():
        return 0
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    cur = conn.cursor()
    cols = [r[1] for r in cur.execute("PRAGMA table_info(session_message)").fetchall()]
    rows = cur.execute(f"SELECT * FROM session_message ORDER BY rowid ASC LIMIT 800").fetchall()
    conn.close()
    parts, anchor = [], None
    textcols = [c for c in cols if c in ("data", "content", "message", "payload", "text")]
    for r in rows:
        d = dict(zip(cols, r))
        harvest_out = []
        for c in textcols or cols:
            v = d.get(c)
            if isinstance(v, bytes):
                harvest(v, harvest_out)
            elif isinstance(v, str) and _looks_text(v):
                harvest_out.append(("text", v))
        texts = [t for k, t in harvest_out if k == "text"]
        seen, uniq = set(), []
        for t in texts:
            if t.strip() and t not in seen:
                seen.add(t)
                uniq.append(t)
        if uniq:
            parts.append("\n".join(uniq))
    if not parts:
        return 0
    body = "\n\n----\n\n".join(parts)[:2_000_000]
    emit(title=f"Agent session history ({len(rows)} records)", anchor_ts=anchor or db.stat().st_mtime,
         body=body, kind="session_history", source_path=str(db))
    return 1


def ingest_editor_conversations() -> int:
    db = SOURCES["editor_conversations"]
    if not db.exists():
        return 0
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    cur = conn.cursor()
    try:
        rows = cur.execute("SELECT c0, c1, c2, c3, c4, c5, c6, c7, c8, c9 FROM conversation_fts_content").fetchall()
    except Exception:
        rows = []
    conn.close()
    parts = []
    for r in rows:
        vals = [str(v) for v in r if v is not None and str(v).strip()]
        if vals:
            parts.append("\n".join(vals))
    if not parts:
        return 0
    body = "\n\n----\n\n".join(parts)[:2_000_000]
    emit(title=f"Editor conversation history ({len(rows)})", anchor_ts=db.stat().st_mtime,
         body=body, kind="session_history", source_path=str(db))
    return 1


def main() -> None:
    TL.mkdir(parents=True, exist_ok=True)
    n1 = ingest_agent_conversations()
    n2 = ingest_agent_summaries()
    n3 = ingest_harness_sessions()
    n4 = ingest_editor_conversations()
    total = n1 + n2 + n3 + n4
    print(f"TIMELINE INGEST: {total} records written "
          f"(conversations {n1}, summaries {n2}, sessions {n3}, editor {n4})")
    try:
        sys.path.insert(0, str(ROOT / "core/ops/scripts"))
        from sovereign_activity_trace import span as _trace
        _trace(trace_id="memory_timeline_ingest", action=f"ingested {total} records into memory/timeline",
               actor="memory_timeline_ingest")
    except Exception:
        pass


if __name__ == "__main__":
    main()
