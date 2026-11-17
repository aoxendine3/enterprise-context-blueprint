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
const repo = join(here, '..', '..', '..');
const golden = JSON.parse(readFileSync(join(repo, 'data_center', 'golden_questions', 'golden_question_set.json'), 'utf8'));
const ids = new Set(golden.questions.map(q => q.id));
const adapter = globalThis.XORAS.evidenceAdapter;
const crypto = globalThis.XORAS.crypto;

// The trusted review used shorthand GQ-00x labels. The repo's real dataset uses
// GQS-00x. We bind to real IDs and refuse to invent a mapping.
for (const id of ['GQS-001', 'GQS-005', 'GQS-013', 'GQS-014', 'GQS-017', 'GQS-022']) {
  test('golden question anchor exists: ' + id, () => {
    assert.ok(ids.has(id), id + ' is absent from the real golden question set');
  });
}

test('GQS-001 / GQS-013: malformed and truncated digests are rejected', () => {
  for (const bad of ['garbage', '', 'a'.repeat(32), 'A'.repeat(64), 'z'.repeat(64)]) {
    assert.equal(crypto.isSha256Hex(bad), false);
  }
  assert.equal(crypto.isSha256Hex('a'.repeat(64)), true);
});

test('GQS-005: replayed evidence id fails closed', async () => {
  const bundle = JSON.parse(readFileSync(join(here, '..', 'dist', 'evidence-bundle.json'), 'utf8'));
  bundle.records.push(JSON.parse(JSON.stringify(bundle.records[0])));
  const unsigned = { ...bundle };
  delete unsigned.manifest;
  delete unsigned.bundle_id;
  delete unsigned.signature;
  bundle.manifest.digest = await crypto.sha256Hex(crypto.canonicalStringify(unsigned));
  const loaded = await adapter.loadBundle(bundle);
  const verified = await adapter.verifySnapshot(loaded, bundle);
  assert.equal(verified.verification.state, 'HALTED');
  assert.ok(verified.verification.failures.some(f => f.reason === 'DUPLICATE_EVIDENCE_REPLAY'));
});

test('GQS-014 / GQS-017: divergent or unbacked records cannot yield a pass', async () => {
  const bundle = JSON.parse(readFileSync(join(here, '..', 'dist', 'evidence-bundle.json'), 'utf8'));
  bundle.records.forEach(r => { r.backed = false; });
  const unsigned = { ...bundle };
  delete unsigned.manifest;
  delete unsigned.bundle_id;
  delete unsigned.signature;
  bundle.manifest.digest = await crypto.sha256Hex(crypto.canonicalStringify(unsigned));
  const loaded = await adapter.loadBundle(bundle);
  const verified = await adapter.verifySnapshot(loaded, bundle);
  assert.equal(Object.keys(loaded.metrics).length, 0);
  assert.equal(verified.verification.state, 'HALTED');
  assert.ok(verified.verification.failures.length > 0);
});

test('GQS-022: MARS coverage floor is declared in the build', () => {
  const build = readFileSync(join(here, '..', 'build.sh'), 'utf8');
  assert.match(build, /experimental-test-coverage/);
  assert.ok(/80/.test(readFileSync(join(here, '..', 'README.md'), 'utf8')));
});
