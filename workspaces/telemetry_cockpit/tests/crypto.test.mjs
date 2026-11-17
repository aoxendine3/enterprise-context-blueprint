import { test } from 'node:test';
import assert from 'node:assert/strict';
import '../src/crypto.js';

const { sha256Hex, isSha256Hex, canonicalStringify } = globalThis.XORAS.crypto;

const VECTORS = [
  ['', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'],
  ['abc', 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'],
  ['hello world', 'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'],
  ['The quick brown fox jumps over the lazy dog',
   'd7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592'],
  ['a'.repeat(1_000_000), 'cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0']
];

test('SHA-256 known vectors produce exactly 64 lowercase hex chars', async () => {
  for (const [input, expected] of VECTORS) {
    const actual = await sha256Hex(input);
    assert.equal(actual, expected);
    assert.match(actual, /^[0-9a-f]{64}$/);
  }
});

test('null and undefined return null, never a fabricated digest', async () => {
  assert.equal(await sha256Hex(null), null);
  assert.equal(await sha256Hex(undefined), null);
});

test('rejects the old 32-character fake digest', () => {
  assert.equal(isSha256Hex('4a89f1c2d09e881b7741a209f3c11e90'), false);
  assert.equal(isSha256Hex('e3b0c44298fc1c149afbf4c8996fb924'), false);
  assert.equal(isSha256Hex(VECTORS[0][1]), true);
});

test('deterministic across 100 calls (no Date.now salt)', async () => {
  const first = await sha256Hex('determinism');
  for (let i = 0; i < 100; i += 1) {
    assert.equal(await sha256Hex('determinism'), first);
  }
});

test('canonicalStringify sorts keys and emits no whitespace', () => {
  const a = canonicalStringify({ b: 1, a: { d: 4, c: 3 } });
  const b = canonicalStringify({ a: { c: 3, d: 4 }, b: 1 });
  assert.equal(a, '{"a":{"c":3,"d":4},"b":1}');
  assert.equal(a, b);
});

test('avalanche: one-bit input change changes most of the digest', async () => {
  const a = await sha256Hex('avalanche-A');
  const b = await sha256Hex('avalanche-B');
  let diff = 0;
  for (let i = 0; i < a.length; i += 1) if (a[i] !== b[i]) diff += 1;
  assert.ok(diff > 24, `expected strong avalanche, got ${diff}/64`);
});
