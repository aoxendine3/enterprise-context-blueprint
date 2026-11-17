import { test } from 'node:test';
import assert from 'node:assert/strict';
import '../src/crypto.js';
import '../src/state-machine.js';

const machine = globalThis.XORAS.stateMachine;

test('initial state is UNVERIFIED, never VERIFIED', () => {
  assert.deepEqual(machine.initialState(), {
    state: 'UNVERIFIED', reason: 'NO_EVIDENCE_LOADED'
  });
});

test('all legal transitions resolve', () => {
  for (const t of machine.TRANSITIONS) {
    const result = machine.transition(t.from, t.event);
    assert.equal(result.ok, true, `${t.from} + ${t.event}`);
    assert.equal(result.to, t.to);
  }
});

test('illegal transitions are rejected without changing state', () => {
  for (const t of machine.TRANSITIONS) {
    for (const event of ['FORCE_RESUME', 'OVERRIDE', 'SET_VERIFIED', t.event + '_BAD']) {
      if (machine.TRANSITIONS.some(x => x.from === t.from && x.event === event)) continue;
      const result = machine.transition(t.from, event);
      assert.equal(result.ok, false, `${t.from} + ${event} must be rejected`);
      assert.equal(result.to, t.from);
      assert.equal(result.reason, 'ILLEGAL_TRANSITION');
    }
  }
});

test('DIVERGED cannot jump directly to VERIFIED', () => {
  const result = machine.transition('DIVERGED', 'VERIFY_OK');
  assert.equal(result.ok, false);
});

test('HALTED requires remediation and verification before VERIFIED', () => {
  assert.equal(machine.transition('HALTED', 'VERIFY_OK').ok, false);
  assert.equal(machine.transition('HALTED', 'BEGIN_REMEDIATION').to, 'REMEDIATING');
  assert.equal(machine.transition('REMEDIATING', 'VERIFY_OK').to, 'VERIFIED');
});

test('only VERIFIED permits mutating actions', () => {
  assert.equal(machine.canMutate('VERIFIED'), true);
  for (const s of machine.STATES.filter(s => s !== 'VERIFIED')) {
    assert.equal(machine.canMutate(s), false, `${s} must be blocked`);
  }
});

test('there is no FORCE RESUME event in the entire machine', () => {
  const flat = machine.TRANSITIONS.map(t => t.event.toUpperCase()).join('|');
  assert.equal(/FORCE|RESUME|OVERRIDE|BYPASS/.test(flat), false);
});
