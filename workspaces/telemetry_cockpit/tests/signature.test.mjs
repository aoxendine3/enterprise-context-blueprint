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
const dist = join(here, '..', 'dist');
const adapter = globalThis.XORAS.evidenceAdapter;
const c = globalThis.XORAS.crypto;

function shippedTrustRoot() {
  const js = readFileSync(join(dist, 'trust_root.js'), 'utf8');
  const start = js.indexOf('{');
  const end = js.lastIndexOf('}');
  return JSON.parse(js.slice(start, end + 1));
}

test('shipped bundle carries Ed25519 signature and a pinned public key', async () => {
  const bundle = JSON.parse(readFileSync(join(dist, 'evidence-bundle.json'), 'utf8'));
  const root = shippedTrustRoot();
  assert.equal(bundle.signature.algorithm, 'Ed25519');
  assert.equal(bundle.signature.encoding, 'raw64-hex');
  assert.match(bundle.signature.value, /^[0-9a-f]{128}$/);
  assert.match(root.pinned_public_key_spki_b64, /^[A-Za-z0-9+/]+={0,2}$/);
  assert.equal(root.pinned_bundle_digest, bundle.manifest.digest);

  globalThis.XORAS_TRUST_ROOT = root;
  try {
    const loaded = await adapter.loadBundle(bundle);
    assert.notEqual(loaded.verification.reason, 'BAD_BUNDLE_SIGNATURE');
    assert.ok(!loaded.verification.failures.includes('SIGNATURE_MISSING'));
  } finally {
    delete globalThis.XORAS_TRUST_ROOT;
  }
});

test('tampered record with recomputed digest is rejected as BAD_BUNDLE_SIGNATURE', async () => {
  const bundle = JSON.parse(readFileSync(join(dist, 'evidence-bundle.json'), 'utf8'));
  globalThis.XORAS_TRUST_ROOT = shippedTrustRoot();
  try {
    bundle.generator.version = 'TAMPERED';
    const unsigned = { ...bundle };
    delete unsigned.manifest;
    delete unsigned.bundle_id;
    delete unsigned.signature;
    bundle.manifest.digest = await c.sha256Hex(c.canonicalStringify(unsigned));
    bundle.bundle_id = bundle.manifest.digest;
    globalThis.XORAS_TRUST_ROOT.pinned_bundle_digest = bundle.manifest.digest;
    const loaded = await adapter.loadBundle(bundle);
    assert.equal(loaded.verification.state, 'HALTED');
    assert.equal(loaded.verification.reason, 'BAD_BUNDLE_SIGNATURE');
  } finally {
    delete globalThis.XORAS_TRUST_ROOT;
  }
});

test('missing signature fails closed when pin is present', async () => {
  const bundle = JSON.parse(readFileSync(join(dist, 'evidence-bundle.json'), 'utf8'));
  globalThis.XORAS_TRUST_ROOT = shippedTrustRoot();
  try {
    delete bundle.signature;
    const loaded = await adapter.loadBundle(bundle);
    assert.equal(loaded.verification.state, 'HALTED');
    assert.ok(loaded.verification.failures.includes('SIGNATURE_MISSING'));
  } finally {
    delete globalThis.XORAS_TRUST_ROOT;
  }
});

test('foreign public key pin fails closed', async () => {
  const bundle = JSON.parse(readFileSync(join(dist, 'evidence-bundle.json'), 'utf8'));
  const root = shippedTrustRoot();
  root.pinned_public_key_spki_b64 =
    'MCowBQYDK2VwAyEAsYOYQ0r6Dmly4OPkaL7NL1vFJ3bfFvo65nBIdfRdRxk=';
  globalThis.XORAS_TRUST_ROOT = root;
  try {
    const loaded = await adapter.loadBundle(bundle);
    assert.equal(loaded.verification.state, 'HALTED');
    assert.equal(loaded.verification.reason, 'BAD_BUNDLE_SIGNATURE');
  } finally {
    delete globalThis.XORAS_TRUST_ROOT;
  }
});

test('replayed build sequence fails closed as BUILD_SEQ_MISMATCH', async () => {
  const bundle = JSON.parse(readFileSync(join(dist, 'evidence-bundle.json'), 'utf8'));
  const root = shippedTrustRoot();
  bundle.build_seq = root.build_seq - 1;
  const unsigned = { ...bundle };
  delete unsigned.manifest;
  delete unsigned.bundle_id;
  delete unsigned.signature;
  bundle.manifest.digest = await c.sha256Hex(c.canonicalStringify(unsigned));
  bundle.bundle_id = bundle.manifest.digest;
  root.pinned_bundle_digest = bundle.manifest.digest;
  globalThis.XORAS_TRUST_ROOT = root;
  try {
    const loaded = await adapter.loadBundle(bundle);
    assert.equal(loaded.verification.state, 'HALTED');
    assert.ok(loaded.verification.failures.includes('BUILD_SEQ_MISMATCH'));
  } finally {
    delete globalThis.XORAS_TRUST_ROOT;
  }
});
