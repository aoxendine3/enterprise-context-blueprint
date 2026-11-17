import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import '../src/crypto.js';
import '../src/drift.js';
import '../src/state-machine.js';
import '../src/evidence-adapter.js';

const here = dirname(fileURLToPath(import.meta.url));
const bundlePath = join(here, '..', 'dist', 'evidence-bundle.json');
const c = globalThis.XORAS.crypto;
const adapter = globalThis.XORAS.evidenceAdapter;
const drift = globalThis.XORAS.drift;

test('crypto accepts Uint8Array and ArrayBuffer inputs', async () => {
  const bytes = new TextEncoder().encode('abc');
  const expected = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad';
  assert.equal(await c.sha256Hex(bytes), expected);
  assert.equal(await c.sha256Hex(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength)), expected);
  assert.equal(c.toBytes(12345), null);
});

test('canonicalization rejects non-finite numbers', () => {
  assert.throws(() => c.canonicalStringify({ x: NaN }), /NON_FINITE_NUMBER/);
  assert.throws(() => c.canonicalStringify({ x: Infinity }), /NON_FINITE_NUMBER/);
});

test('state-machine terminal-halt helper', () => {
  assert.equal(globalThis.XORAS.stateMachine.isTerminalHalt('HALTED'), true);
  assert.equal(globalThis.XORAS.stateMachine.isTerminalHalt('DIVERGED'), false);
});

test('drift rejects non-numeric and mismatched-length vectors', () => {
  for (const [a, b] of [['abc', [1]], [[1, 2], [1]], [[1, 2], [1, 2, 3]], [[0, 0], [1, 1]]]) {
    const result = drift.semanticDrift(a, b);
    assert.equal(result.drift, null);
    assert.equal(result.stream_tag, 'UNVERIFIED');
  }
});

async function fresh() {
  return JSON.parse(readFileSync(bundlePath, 'utf8'));
}

test('adapter rejects null, wrong schema, invalid manifest, invalid shape, empty bundle', async () => {
  for (const bad of [null, {}, { schema_version: 'wrong' }]) {
    const s = await adapter.loadBundle(bad);
    assert.equal(s.verification.state, 'HALTED');
    assert.equal(s.verification.reason, 'INVALID_BUNDLE');
  }
  let b = await fresh();
  b.manifest.algorithm = 'md5';
  assert.equal((await adapter.loadBundle(b)).verification.failures.includes('INVALID_MANIFEST'), true);

  b = await fresh();
  delete b.records;
  assert.equal((await adapter.loadBundle(b)).verification.failures.includes('INVALID_SHAPE'), true);

  b = await fresh();
  b.records = [];
  assert.equal((await adapter.loadBundle(b)).verification.failures.includes('EMPTY_BUNDLE'), true);
});

test('adapter rejects a wrong trust-root schema version', async () => {
  const previous = globalThis.XORAS_TRUST_ROOT;
  globalThis.XORAS_TRUST_ROOT = { schema_version: 'wrong', pinned_bundle_digest: 'a'.repeat(64) };
  try {
    const b = await fresh();
    const s = await adapter.loadBundle(b);
    assert.equal(s.verification.state, 'HALTED');
    assert.ok(s.verification.failures.includes('INVALID_TRUST_ROOT'));
  } finally {
    globalThis.XORAS_TRUST_ROOT = previous;
  }
});

test('adapter derives a real drift metric when vectors are present', async () => {
  const b = await fresh();
  const p = {
    source_id: 'test:drift',
    locator: 'memory/catch_log/TEST_DRIFT_RECEIPT.json',
    observed_sha256: 'd'.repeat(64)
  };
  const evidenceId = await c.sha256Hex(c.canonicalStringify(p));
  b.sources.push({ source_id: p.source_id, type: 'receipt_json', locator: p.locator,
                   captured_at: '', observed_sha256: p.observed_sha256, byte_count: 1 });
  b.records.push({
    evidence_id: evidenceId, kind: 'DRIFT_VECTORS', subject: 'test-drift',
    claims: [{ key: 'goal_vector', value: [1, 0] }, { key: 'thought_vector', value: [0, 1] }],
    verdict: 'PASS', verdict_raw: 'TEST_PASS',
    provenance: { ...p, captured_at: '', attestation: 'ATTESTED_BY_EXPORTER' },
    raw_ref: p.locator, backed: true
  });
  await resign(b);
  const loaded = await adapter.loadBundle(b);
  assert.ok(loaded.metrics.semantic_drift);
  assert.equal(loaded.metrics.semantic_drift.halted, true);
  assert.equal(loaded.metrics.semantic_drift.status, 'DERIVED');
  const verified = await adapter.verifySnapshot(loaded, b);
  assert.equal(verified.verification.state, 'HALTED');
  assert.ok(verified.verification.failures.some(f => f.reason === 'DRIFT_THRESHOLD_EXCEEDED'));
});

test('missing RECOMPUTED_IN_BROWSER bytes fail closed', async () => {
  const b = await fresh();
  const target = b.records.find(r => (r.provenance || {}).attestation === 'RECOMPUTED_IN_BROWSER');
  assert.ok(target);
  b.artifacts = [];
  await resign(b);
  const loaded = await adapter.loadBundle(b);
  const verified = await adapter.verifySnapshot(loaded, b);
  assert.equal(verified.verification.state, 'HALTED');
  assert.ok(verified.verification.failures.some(f => f.reason === 'EVIDENCE_ABSENT'));
});

async function resign(bundle) {
  const unsigned = { ...bundle };
  delete unsigned.manifest;
  delete unsigned.bundle_id;
  delete unsigned.signature;
  bundle.manifest.digest = await c.sha256Hex(c.canonicalStringify(unsigned));
  bundle.bundle_id = bundle.manifest.digest;
}

test('oversized bundles are rejected before expensive hashing', async () => {
  const b = await fresh();
  b.records = new Array(5001).fill(null).map(() => ({ evidence_id: 'x' }));
  const s = await adapter.loadBundle(b);
  assert.equal(s.verification.state, 'HALTED');
  assert.ok(s.verification.failures.includes('BUNDLE_TOO_LARGE'));

  const huge = await fresh();
  huge.notes = 'x'.repeat(12 * 1024 * 1024);
  const s2 = await adapter.loadBundle(huge);
  assert.equal(s2.verification.state, 'HALTED');
  assert.equal(s2.verification.reason, 'BUNDLE_TOO_LARGE');
});

test('record above DART egress clearance fails closed', async () => {
  const b = await fresh();
  b.records[0].clearance = 3;
  assert.ok(b.egress_clearance < 3);
  await resign(b);
  const loaded = await adapter.loadBundle(b);
  const verified = await adapter.verifySnapshot(loaded, b);
  assert.equal(verified.verification.state, 'HALTED');
  assert.ok(verified.verification.failures.some(f => f.reason === 'EGRESS_CLEARANCE_VIOLATION'));
});
