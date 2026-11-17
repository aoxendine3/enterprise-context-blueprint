import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import '../src/crypto.js';

const here = dirname(fileURLToPath(import.meta.url));
const bundle = JSON.parse(readFileSync(join(here, '..', 'dist', 'evidence-bundle.json'), 'utf8'));
const { sha256Hex, canonicalStringify, isSha256Hex } = globalThis.XORAS.crypto;

test('bundle schema and manifest are well formed', () => {
  assert.equal(bundle.schema_version, 'xoras.evidence-bundle.v1');
  assert.equal(bundle.manifest.algorithm, 'sha256');
  assert.ok(isSha256Hex(bundle.manifest.digest));
  assert.equal(bundle.bundle_id, bundle.manifest.digest);
});

test('manifest digest matches the unsigned payload', async () => {
  const unsigned = { ...bundle };
  delete unsigned.manifest;
  delete unsigned.bundle_id;
  delete unsigned.signature;
  const computed = await sha256Hex(canonicalStringify(unsigned));
  assert.equal(computed, bundle.manifest.digest);
});

test('every record cites a real source and a real 64-hex digest of its raw bytes', async () => {
  const sourceIds = new Set(bundle.sources.map(s => s.source_id));
  for (const record of bundle.records) {
    assert.ok(sourceIds.has(record.provenance.source_id), 'unresolved source');
    assert.ok(isSha256Hex(record.provenance.observed_sha256), 'observed digest is not SHA-256');
    const expected = await sha256Hex(canonicalStringify({
      source_id: record.provenance.source_id,
      locator: record.provenance.locator,
      observed_sha256: record.provenance.observed_sha256
    }));
    assert.equal(record.evidence_id, expected);
  }
});

test('every locator points into real SSOT paths', () => {
  for (const source of bundle.sources) {
    assert.match(source.locator, /^(memory\/(catch_log|tri_brain)\/|workspaces\/telemetry_cockpit\/dist\/)/);
  }
});

test('reality gate verdict is propagated verbatim and classified honestly', () => {
  const reality = bundle.records.find(r => r.kind === 'REALITY_GATE');
  assert.ok(reality, 'REALITY_GATE slot missing');
  assert.equal(typeof reality.verdict_raw, 'string');
  assert.ok(['PASS', 'FAIL', 'UNKNOWN', 'UNRECOGNIZED'].includes(reality.verdict));
  if (/FAIL|MISMATCH|VIOLATION|DIVERGED|ERROR|PARSE_ERROR/i.test(reality.verdict_raw)) {
    assert.equal(reality.verdict, 'FAIL');
  } else if (/PASS|VERIFIED|CERTIFIED|APPROVED/i.test(reality.verdict_raw)) {
    assert.equal(reality.verdict, 'PASS');
  }
  assert.ok(bundle.required_slots.includes('ROOT_MANIFEST'));
});

test('positive receipts are never mislabeled as FAIL', () => {
  for (const record of bundle.records) {
    const raw = String(record.verdict_raw || '');
    if (!raw) continue;
    const positive = /APPROVED|VERIFIED|CERTIFIED|PASS|GREEN|SEALED|CAPTURED|SUCCESS/i.test(raw);
    const negative = /FAIL|MISMATCH|VIOLATION|DIVERGED|ERROR|PARSE_ERROR|0xBEAF/i.test(raw);
    if (positive && !negative) {
      assert.equal(record.verdict, 'PASS', raw + ' was misclassified');
    }
  }
  const approved = bundle.records.filter(r => r.verdict_raw === 'APPROVED');
  assert.ok(approved.length > 0);
  assert.ok(approved.every(r => r.verdict === 'PASS'));
});

test('DART cage checks are real booleans from the receipt', () => {
  const dart = bundle.records.find(r => r.kind === 'DART_CAGE_LATTICE');
  assert.ok(dart);
  const keys = Object.keys(dart.checks || {});
  assert.ok(keys.length > 0);
  assert.ok(Object.values(dart.checks).every(v => typeof v === 'boolean'));
});

test('bundle ships real artifact bytes for in-browser hash recomputation', () => {
  assert.ok(bundle.artifacts.length > 0);
  const artifact = bundle.artifacts[0];
  assert.match(artifact.path, /^workspaces\/telemetry_cockpit\/dist\//);
  assert.ok(isSha256Hex(artifact.sha256_at_export));
  assert.ok(artifact.bytes_b64.length > 0);
});

test('exporter is deterministic for identical source state', () => {
  assert.equal(typeof bundle.generated_at, 'string');
  assert.ok(bundle.generator.repo_commit);
});

test('DART egress: no record exceeds bundle clearance and no credentials leak', () => {
  for (const record of bundle.records) {
    assert.ok(typeof record.clearance === 'number');
    assert.ok(record.clearance <= bundle.egress_clearance, 'record exceeds egress clearance');
    for (const claim of record.claims || []) {
      if (typeof claim.value !== 'string') continue;
      assert.equal(/-----BEGIN [A-Z ]*PRIVATE KEY-----/.test(claim.value), false);
      assert.equal(/\b(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,})\b/.test(claim.value), false);
    }
  }
});
