import { test } from 'node:test';
import assert from 'node:assert/strict';
import '../src/crypto.js';
import '../src/drift.js';

const drift = globalThis.XORAS.drift;

test('cosine similarity of identical vectors is 1 and drift is 0', () => {
  const result = drift.semanticDrift([1, 0, 0], [1, 0, 0]);
  assert.equal(result.cosine, 1);
  assert.equal(result.drift, 0);
  assert.equal(result.halted, false);
  assert.equal(result.stream_tag, 'DERIVED_FROM_RECEIPT_CLAIMS');
});

test('orthogonal vectors produce drift 1 and halt', () => {
  const result = drift.semanticDrift([1, 0], [0, 1]);
  assert.equal(result.cosine, 0);
  assert.equal(result.drift, 1);
  assert.equal(result.halted, true);
  assert.equal(result.reason, 'DRIFT_ABOVE_THRESHOLD');
});

test('threshold boundary: 0.18 is the fail-closed line', () => {
  assert.equal(drift.DRIFT_THRESHOLD, 0.18);
  assert.equal(drift.MIN_SIMILARITY, 0.82);
  const below = drift.semanticDrift([1, 0], [0.83, Math.sqrt(1 - 0.83 ** 2)]);
  const above = drift.semanticDrift([1, 0], [0.81, Math.sqrt(1 - 0.81 ** 2)]);
  assert.equal(below.halted, false);
  assert.equal(above.halted, true);
});

test('missing or invalid vectors never fabricate a drift number', () => {
  for (const [goal, thought] of [[null, null], [[], []], [[1, NaN], [1, 2]], [[1], [1, 2]]]) {
    const result = drift.semanticDrift(goal, thought);
    assert.equal(result.drift, null);
    assert.equal(result.stream_tag, 'UNVERIFIED');
    assert.equal(result.halted, false);
  }
});
