import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import '../src/crypto.js';
import '../src/state-machine.js';
import '../src/evidence-adapter.js';

const here = dirname(fileURLToPath(import.meta.url));
const bundlePath = join(here, '..', 'dist', 'evidence-bundle.json');
const adapter = globalThis.XORAS.evidenceAdapter;

async function resign(bundle) {
  const { sha256Hex, canonicalStringify } = globalThis.XORAS.crypto;
  const unsigned = { ...bundle };
  delete unsigned.manifest;
  delete unsigned.bundle_id;
  delete unsigned.signature;
  bundle.manifest.digest = await sha256Hex(canonicalStringify(unsigned));
  bundle.bundle_id = bundle.manifest.digest;
  return bundle;
}

// Synthetic fixture records used only to satisfy code-defined required slots
// in a unit test. They are never shipped in the real bundle.
async function injectSlot(bundle, kind) {
  const { sha256Hex, canonicalStringify } = globalThis.XORAS.crypto;
  const sourceId = "test:" + kind;
  const locator = "memory/catch_log/TEST_FIXTURE_RECEIPT.json";
  const provenance = {
    source_id: sourceId,
    locator: locator,
    captured_at: "1970-01-01T00:00:00Z",
    observed_sha256: "c".repeat(64),
    attestation: "ATTESTED_BY_EXPORTER"
  };
  const evidenceId = await sha256Hex(canonicalStringify({
    source_id: sourceId, locator: locator, observed_sha256: provenance.observed_sha256
  }));
  bundle.sources.push({
    source_id: sourceId, type: "receipt_json", locator: locator,
    captured_at: provenance.captured_at, observed_sha256: provenance.observed_sha256,
    byte_count: 1
  });
  bundle.records.push({
    evidence_id: evidenceId, kind: kind, subject: "test-fixture",
    claims: [], verdict: "PASS", verdict_raw: "TEST_PASS",
    provenance: provenance, raw_ref: locator, backed: true
  });
}

test('simulation snapshot contains no backed values', () => {
  const s = adapter.simulationSnapshot();
  assert.equal(s.mode, 'SIMULATION');
  assert.equal(s.verification.state, 'UNVERIFIED');
  assert.equal(Object.keys(s.metrics).length, 0);
  assert.ok(s.unknowns.length > 0);
});

test('parse failure halts closed', () => {
  const s = adapter.parseFailureSnapshot();
  assert.equal(s.verification.state, 'HALTED');
  assert.equal(s.verification.reason, 'INVALID_JSON');
});

test('state is a pure function of failures: any failure halts, no failure verifies', async () => {
  const bundle = JSON.parse(readFileSync(bundlePath, 'utf8'));
  const loaded = await adapter.loadBundle(bundle);
  const verified = await adapter.verifySnapshot(loaded, bundle);
  assert.equal(verified.mode, 'RECEIPT_BACKED');
  const hasFailures = verified.verification.failures.length > 0;
  assert.equal(verified.verification.state, hasFailures ? 'HALTED' : 'VERIFIED');
  assert.equal(globalThis.XORAS.stateMachine.canMutate(verified.verification.state), !hasFailures);
});

test('real bundle: no metric is BACKED without evidence ids', async () => {
  const bundle = JSON.parse(readFileSync(bundlePath, 'utf8'));
  const loaded = await adapter.loadBundle(bundle);
  for (const [key, m] of Object.entries(loaded.metrics)) {
    if (m.status === 'BACKED' || m.status === 'DERIVED') {
      assert.ok(m.evidence_ids.length > 0, `${key} lacks evidence`);
    }
  }
});

test('real bundle: DART cage checks are derived from the receipt', async () => {
  const bundle = JSON.parse(readFileSync(bundlePath, 'utf8'));
  const loaded = await adapter.loadBundle(bundle);
  assert.ok(loaded.metrics.dart_cage_checks);
  assert.match(loaded.metrics.dart_cage_checks.value, /^\d+\/\d+$/);
  assert.equal(loaded.metrics.dart_cage_checks.status, 'DERIVED');
});

test('real bundle: reality gate verdict is the verbatim receipt value', async () => {
  const bundle = JSON.parse(readFileSync(bundlePath, 'utf8'));
  const loaded = await adapter.loadBundle(bundle);
  const receipt = JSON.parse(readFileSync(join(here, '..', '..', '..',
    'memory', 'catch_log', 'REALITY_GATE_RECEIPT.json'), 'utf8'));
  assert.ok(loaded.metrics.reality_gate_verdict);
  assert.equal(loaded.metrics.reality_gate_verdict.value, receipt.verdict);
  assert.equal(loaded.metrics.reality_gate_verdict.status, 'BACKED');
});

test('real bundle: golden pass rate is backed and mirrors the live SSOT receipt', async () => {
  const receipt = JSON.parse(readFileSync(join(here, '..', '..', '..', 'memory', 'catch_log', 'GOLDEN_GROUNDEDNESS_RECEIPT.json'), 'utf8'));
  const bundle = JSON.parse(readFileSync(bundlePath, 'utf8'));
  const loaded = await adapter.loadBundle(bundle);
  assert.ok(loaded.metrics.golden_pass_rate);
  // The bundle is a build-time snapshot of the repo's real golden receipt;
  // it must equal it exactly (divergence = fabrication, fail closed).
  assert.equal(Number(loaded.metrics.golden_pass_rate.value), receipt.pass_rate);
  assert.equal(loaded.metrics.golden_pass_rate.status, 'BACKED');
});

test('templated metric slots with no source are UNVERIFIED unknowns', async () => {
  const bundle = JSON.parse(readFileSync(bundlePath, 'utf8'));
  const loaded = await adapter.loadBundle(bundle);
  const slots = loaded.unknowns.map(u => u.slot);
  for (const slot of ['sdi_percent', 'static_score', 'tools_ready', 'sig_ratio']) {
    assert.ok(slots.includes(slot), `${slot} must be an unknown`);
    assert.equal(loaded.metrics[slot], undefined);
  }
});

test('tampered manifest fails closed with MANIFEST_MISMATCH', async () => {
  const bundle = JSON.parse(readFileSync(bundlePath, 'utf8'));
  bundle.generator.version = 'TAMPERED';
  const loaded = await adapter.loadBundle(bundle);
  assert.equal(loaded.verification.state, 'HALTED');
  assert.equal(loaded.verification.reason, 'MANIFEST_MISMATCH');
});

test('tampered record id fails closed via failure list', async () => {
  const bundle = JSON.parse(readFileSync(bundlePath, 'utf8'));
  const unsigned = { ...bundle };
  delete unsigned.manifest;
  delete unsigned.bundle_id;
  delete unsigned.signature;
  const { sha256Hex, canonicalStringify } = globalThis.XORAS.crypto;
  bundle.records[0].evidence_id = 'a'.repeat(64);
  bundle.manifest.digest = await sha256Hex(canonicalStringify(unsigned));
  const loaded = await adapter.loadBundle(bundle);
  const verified = await adapter.verifySnapshot(loaded, bundle);
  assert.equal(verified.verification.state, 'HALTED');
  assert.ok(verified.verification.failures.some(f => f.reason === 'INVALID_RECORD'));
});

test('missing required slot fails closed with MISSING_EVIDENCE', async () => {
  const bundle = JSON.parse(readFileSync(bundlePath, 'utf8'));
  bundle.required_slots = ['A_SLOT_THAT_DOES_NOT_EXIST'];
  await resign(bundle);
  const loaded = await adapter.loadBundle(bundle);
  const verified = await adapter.verifySnapshot(loaded, bundle);
  assert.equal(verified.verification.state, 'HALTED');
  assert.ok(verified.verification.failures.some(f => f.reason === 'MISSING_EVIDENCE'));
});

test('injected FAIL verdict halts even when all other evidence is present', async () => {
  const bundle = JSON.parse(readFileSync(bundlePath, 'utf8'));
  bundle.records.forEach(r => { r.verdict = 'PASS'; });
  await injectSlot(bundle, 'ROOT_MANIFEST');
  await injectSlot(bundle, 'DRIFT_VECTORS');
  await resign(bundle);
  const loaded = await adapter.loadBundle(bundle);
  const clean = await adapter.verifySnapshot(loaded, bundle);
  assert.equal(clean.verification.state, 'VERIFIED');
  assert.equal(globalThis.XORAS.stateMachine.canMutate(clean.verification.state), true);

  // Snapshot freezing protects the original records; mutate a fresh parse.
  const tampered = JSON.parse(readFileSync(bundlePath, 'utf8'));
  tampered.records.forEach(r => { r.verdict = 'PASS'; });
  tampered.records[0].verdict = 'FAIL';
  await injectSlot(tampered, 'ROOT_MANIFEST');
  await injectSlot(tampered, 'DRIFT_VECTORS');
  await resign(tampered);
  const loaded2 = await adapter.loadBundle(tampered);
  const verified2 = await adapter.verifySnapshot(loaded2, tampered);
  assert.equal(verified2.verification.state, 'HALTED');
  assert.ok(verified2.verification.failures.some(f => f.reason === 'RECEIPT_ATTESTED_FAILURE'));
});
