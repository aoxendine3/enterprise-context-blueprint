#!/usr/bin/env python3
"""
Evidence Ledger (Chunk 1): append-only, hash-chained, Ed25519-signed rows.

Row = one claim + pointers to evidence + verdict. Not an essay.
  row_hash = sha256(canonical_json(row without row_hash/sig))
  sig      = Ed25519(author_key, row_hash)
  prev_hash chains each row to the one before it (genesis prev = 64 zeros).

Verifier trusts only: the ledger file, the public keys, and the evidence files
on disk (it re-hashes them). It does not trust the authoring agent.

Honest limits (recorded, not hidden):
  * Keys live on this machine. Signatures prove chain integrity and key use,
    NOT independence of the signer from the swarm. Independent attestation
    needs a key held off-box.
  * Evidence drift is reported, not auto-fixed: a changed file means the claim
    was made about different bytes.

CLI:
  evidence_ledger.py verify [--path LEDGER]
  evidence_ledger.py selftest
"""
import hashlib, json, os, shutil, sys, tempfile, time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

ROOT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
LEDGER = os.path.join(ROOT, "memory/catch_log/evidence_ledger.jsonl")
KEYDIR = os.path.join(ROOT, ".sovereign/crypto_keys/agents")
GENESIS = "0" * 64
KINDS = {"FINDING", "CLAIM", "PROBE", "RESULT", "RETRACTION", "DEPRECATION"}
VERDICTS = {"PROVEN", "REFUTED", "UNVERIFIED", "CONTRADICTED"}


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest(), os.path.getsize(path)


def _load_priv(agent):
    with open(os.path.join(KEYDIR, agent, "ed25519_priv.pem"), "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def _load_pub(agent, keydir=None):
    with open(os.path.join(keydir or KEYDIR, agent, "ed25519_pub.pem"), "rb") as f:
        return serialization.load_pem_public_key(f.read())


def _rows(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def evidence_for(files=(), probes=()):
    ev = []
    for p in files:
        full = p if os.path.isabs(p) else os.path.join(ROOT, p)
        digest, size = sha256_file(full)
        ev.append({"path": os.path.relpath(full, ROOT), "sha256": digest, "bytes": size})
    for pr in probes:
        ev.append({"probe": pr})
    return ev


def append_row(agent, kind, subject, claim, verdict, evidence, path=LEDGER):
    assert kind in KINDS and verdict in VERDICTS
    rows = _rows(path)
    row = {
        "seq": len(rows),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prev_hash": rows[-1]["row_hash"] if rows else GENESIS,
        "agent": agent, "kind": kind, "subject": subject,
        "claim": claim, "verdict": verdict, "evidence": evidence,
    }
    row["row_hash"] = hashlib.sha256(canon(row)).hexdigest()
    row["sig"] = _load_priv(agent).sign(bytes.fromhex(row["row_hash"])).hex()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:          # append-only: never opened for write/truncate
        f.write(json.dumps(row, sort_keys=True) + "\n")
        f.flush(); os.fsync(f.fileno())
    return row


def verify(path=LEDGER, keydir=None, check_evidence=True):
    """Returns (ok, problems). Every problem names a seq and a reason."""
    problems, prev = [], GENESIS
    rows = _rows(path)
    for i, r in enumerate(rows):
        body = {k: v for k, v in r.items() if k not in ("row_hash", "sig")}
        if r.get("seq") != i:
            problems.append((i, "SEQ_GAP_OR_REORDER"))
        if r.get("prev_hash") != prev:
            problems.append((i, "CHAIN_BREAK"))
        if hashlib.sha256(canon(body)).hexdigest() != r.get("row_hash"):
            problems.append((i, "ROW_HASH_MISMATCH(tampered content)"))
        try:
            _load_pub(r["agent"], keydir).verify(bytes.fromhex(r["sig"]), bytes.fromhex(r["row_hash"]))
        except Exception:
            problems.append((i, "BAD_SIGNATURE"))
        if check_evidence:
            for e in r.get("evidence", []):
                if "path" in e:
                    full = os.path.join(ROOT, e["path"])
                    if not os.path.exists(full):
                        problems.append((i, f"EVIDENCE_MISSING:{e['path']}"))
                    elif sha256_file(full)[0] != e["sha256"]:
                        problems.append((i, f"EVIDENCE_DRIFT:{e['path']}"))
        prev = r.get("row_hash", "")
    return (not problems), problems


def selftest():
    """Mutate a COPY six adversarial ways; each must be caught. Real ledger untouched."""
    tmp = tempfile.mkdtemp()
    cp = os.path.join(tmp, "l.jsonl")
    shutil.copy(LEDGER, cp)
    lines = open(cp).read().splitlines()
    assert len(lines) >= 3, "need >=3 rows to self-test"
    results = {}

    # 1. edit a claim in a middle row
    r = json.loads(lines[1]); r["claim"] += " (adversarial edit)"
    open(cp, "w").write("\n".join([lines[0], json.dumps(r, sort_keys=True)] + lines[2:]) + "\n")
    results["edit_claim"] = verify(cp, check_evidence=False)

    # 2. delete a middle row
    open(cp, "w").write("\n".join([lines[0]] + lines[2:]) + "\n")
    results["delete_row"] = verify(cp, check_evidence=False)

    # 3. corrupt signature bytes
    r = json.loads(lines[1]); r["sig"] = "00" * 64
    open(cp, "w").write("\n".join([lines[0], json.dumps(r, sort_keys=True)] + lines[2:]) + "\n")
    results["corrupt_sig"] = verify(cp, check_evidence=False)

    # 4. foreign key substitution (valid Ed25519 signature from rogue unauthorized key)
    rogue_priv = ed25519.Ed25519PrivateKey.generate()
    r = json.loads(lines[1])
    r["sig"] = rogue_priv.sign(bytes.fromhex(r["row_hash"])).hex()
    open(cp, "w").write("\n".join([lines[0], json.dumps(r, sort_keys=True)] + lines[2:]) + "\n")
    results["foreign_key"] = verify(cp, check_evidence=False)

    # 5. bit-flip in row_hash
    r = json.loads(lines[1])
    hash_bytes = bytearray.fromhex(r["row_hash"])
    hash_bytes[0] ^= 0x01 # 1-bit flip
    r["row_hash"] = hash_bytes.hex()
    open(cp, "w").write("\n".join([lines[0], json.dumps(r, sort_keys=True)] + lines[2:]) + "\n")
    results["bit_flip_hash"] = verify(cp, check_evidence=False)

    # 6. evidence file bit drift
    fake_ev = os.path.join(tmp, "fake_ev.txt")
    with open(fake_ev, "wb") as f: f.write(b"SACRED_ORIGINAL_EVIDENCE_BYTES_v1")
    ev_digest, ev_sz = sha256_file(fake_ev)
    test_ledger = os.path.join(tmp, "drift_ledger.jsonl")
    row_ev = {
        "seq": 0, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prev_hash": GENESIS, "agent": "maxx", "kind": "CLAIM", "subject": "drift_test",
        "claim": "Testing evidence drift detection", "verdict": "PROVEN",
        "evidence": [{"path": fake_ev, "sha256": ev_digest, "bytes": ev_sz}]
    }
    row_ev["row_hash"] = hashlib.sha256(canon(row_ev)).hexdigest()
    row_ev["sig"] = _load_priv("maxx").sign(bytes.fromhex(row_ev["row_hash"])).hex()
    with open(test_ledger, "w") as f: f.write(json.dumps(row_ev, sort_keys=True) + "\n")
    
    # Now mutate the evidence file by 1 bit
    with open(fake_ev, "wb") as f: f.write(b"SACRED_ORIGINAL_EVIDENCE_BYTES_v2")
    results["evidence_drift"] = verify(test_ledger, check_evidence=True)

    shutil.rmtree(tmp)
    allcaught = True
    for name, (ok, probs) in results.items():
        caught = not ok
        allcaught &= caught
        print(f"  {name:16s} -> {'CAUGHT' if caught else 'MISSED'}  {sorted({p[1].split(':')[0] for p in probs})}")
    return allcaught


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "verify":
        path = sys.argv[sys.argv.index("--path") + 1] if "--path" in sys.argv else LEDGER
        check_ev = "--no-evidence" not in sys.argv
        ok, probs = verify(path, check_evidence=check_ev)
        print(f"rows={len(_rows(path))} chain+sigs{' +evidence' if check_ev else ''} ok={ok}")
        for seq, why in probs:
            print(f"  row {seq}: {why}")
        sys.exit(0 if ok else 1)
    if cmd == "selftest":
        sys.exit(0 if selftest() else 1)
