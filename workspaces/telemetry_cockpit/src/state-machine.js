/* XORAS Cockpit - fail-closed verification state machine. */
(function (root) {
  'use strict';
  var XORAS = (root.XORAS = root.XORAS || {});

  var STATES = ['UNVERIFIED', 'REMEDIATING', 'VERIFIED', 'DIVERGED', 'HALTED'];

  var TRANSITIONS = [
    { from: 'UNVERIFIED', event: 'LOAD_BUNDLE', to: 'REMEDIATING' },
    { from: 'UNVERIFIED', event: 'MISSING_EVIDENCE', to: 'HALTED' },
    { from: 'REMEDIATING', event: 'VERIFY_OK', to: 'VERIFIED' },
    { from: 'REMEDIATING', event: 'VERIFY_FAIL', to: 'DIVERGED' },
    { from: 'REMEDIATING', event: 'ABORT', to: 'HALTED' },
    { from: 'VERIFIED', event: 'ASSERT_MISMATCH', to: 'DIVERGED' },
    { from: 'VERIFIED', event: 'EVIDENCE_MISSING', to: 'HALTED' },
    { from: 'DIVERGED', event: 'HALT', to: 'HALTED' },
    { from: 'DIVERGED', event: 'BEGIN_REMEDIATION', to: 'REMEDIATING' },
    { from: 'HALTED', event: 'BEGIN_REMEDIATION', to: 'REMEDIATING' }
  ];

  function transition(from, event) {
    var match = null;
    for (var i = 0; i < TRANSITIONS.length; i += 1) {
      if (TRANSITIONS[i].from === from && TRANSITIONS[i].event === event) {
        match = TRANSITIONS[i];
        break;
      }
    }
    if (!match) {
      return { ok: false, from: from, to: from, reason: 'ILLEGAL_TRANSITION' };
    }
    return { ok: true, from: from, to: match.to, reason: 'OK' };
  }

  function initialState() {
    return { state: 'UNVERIFIED', reason: 'NO_EVIDENCE_LOADED' };
  }

  // Only VERIFIED permits state-mutating actions. No override control exists.
  function canMutate(state) {
    return state === 'VERIFIED';
  }

  function isTerminalHalt(state) {
    return state === 'HALTED';
  }

  XORAS.stateMachine = {
    STATES: STATES,
    TRANSITIONS: TRANSITIONS,
    transition: transition,
    initialState: initialState,
    canMutate: canMutate,
    isTerminalHalt: isTerminalHalt
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = XORAS.stateMachine;
})(typeof globalThis !== 'undefined' ? globalThis : this);
