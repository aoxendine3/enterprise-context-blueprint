/* XORAS Cockpit - single evidence adapter. This is the only code permitted
   to produce a VERIFIED / DIVERGED / HALTED verdict. */
(function (root) {
  'use strict';
  var XORAS = (root.XORAS = root.XORAS || {});
  var crypto = XORAS.crypto;
  var machine = XORAS.stateMachine;

  var SCHEMA = 'xoras.evidence-bundle.v1';
  var MAX_RECORDS = 5000;
  var MAX_SOURCES = 5000;
  var MAX_BUNDLE_CHARS = 12 * 1024 * 1024;
  var REQUIRED_SLOTS = [
    'REALITY_GATE', 'DART_CAGE_LATTICE', 'MERKLE_CHECKPOINT',
    'ROOT_MANIFEST', 'GOLDEN_CHECKPOINT', 'HASH_ASSERT', 'DRIFT_VECTORS'
  ];

  // UI slots with no real source become explicit unknowns, never defaults.
  var UI_SLOTS = {
    'sdi_percent': 'State divergence index',
    'static_score': 'Static validation score',
    'tools_ready': 'Tools ready',
    'sig_ratio': 'Signal ratio'
  };

  function freeze(value) {
    if (value && typeof value === 'object' && !Object.isFrozen(value)) {
      Object.keys(value).forEach(function (key) { freeze(value[key]); });
      Object.freeze(value);
    }
    return value;
  }

  function unknown(slot, reason) {
    return { slot: slot, reason: reason };
  }

  function halted(reason, failures, snapshot) {
    var next = snapshot || {};
    next.verification = { state: 'HALTED', reason: reason, failures: failures || [] };
    return freeze(next);
  }

  function firstRecord(records, kind) {
    for (var i = 0; i < records.length; i += 1) {
      if (records[i].kind === kind) return records[i];
    }
    return null;
  }

  function claim(record, key) {
    if (!record || !Array.isArray(record.claims)) return null;
    for (var i = 0; i < record.claims.length; i += 1) {
      if (record.claims[i].key === key) return record.claims[i].value;
    }
    return null;
  }

  function metric(key, value, status, evidenceIds, derivation) {
    if ((status === 'BACKED' || status === 'DERIVED') &&
        (!Array.isArray(evidenceIds) || evidenceIds.length === 0)) {
      throw new Error('BACKED_METRIC_WITHOUT_EVIDENCE:' + key);
    }
    var streamTag = status === 'BACKED'
      ? 'SOURCE_RECEIPT_CLAIM'
      : (status === 'DERIVED' ? 'DERIVED_FROM_RECEIPT_CLAIMS' : 'UNVERIFIED');
    return {
      key: key,
      value: value,
      status: status,
      stream_tag: streamTag,
      evidence_ids: evidenceIds || [],
      derivation: derivation || ''
    };
  }

  function deriveMetrics(records, unknowns) {
    var metrics = {};

    var dart = firstRecord(records, 'DART_CAGE_LATTICE');
    if (dart && dart.checks && typeof dart.checks === 'object') {
      var values = Object.keys(dart.checks).map(function (k) { return dart.checks[k]; });
      var passed = values.filter(function (v) { return v === true; }).length;
      metrics.dart_cage_checks = metric(
        'dart_cage_checks', passed + '/' + values.length, 'DERIVED', [dart.evidence_id],
        'count(true check values) in DART_CAGE_LATTICE receipt'
      );
    } else {
      unknowns.push(unknown('dart_cage_checks', 'NO_SOURCE'));
    }

    var reality = firstRecord(records, 'REALITY_GATE');
    if (reality) {
      metrics.reality_gate_verdict = metric(
        'reality_gate_verdict', reality.verdict_raw || reality.verdict, 'BACKED',
        [reality.evidence_id], 'verbatim verdict from REALITY_GATE receipt'
      );
      var gp = claim(reality, 'gates_passed');
      var gf = claim(reality, 'gates_failed');
      if (gp !== null && gf !== null) {
        metrics.production_gates = metric(
          'production_gates', String(gp) + ' passed / ' + String(gf) + ' failed',
          'BACKED', [reality.evidence_id], 'claims from REALITY_GATE receipt'
        );
      }
    } else {
      unknowns.push(unknown('reality_gate_verdict', 'NO_SOURCE'));
    }

    var driftRecord = firstRecord(records, 'DRIFT_VECTORS');
    var goalVector = driftRecord ? claim(driftRecord, 'goal_vector') : null;
    var thoughtVector = driftRecord ? claim(driftRecord, 'thought_vector') : null;
    if (Array.isArray(goalVector) && Array.isArray(thoughtVector) && XORAS.drift) {
      var driftResult = XORAS.drift.semanticDrift(goalVector, thoughtVector);
      var driftMetric = metric(
        'semantic_drift', driftResult.drift,
        driftResult.stream_tag === 'DERIVED_FROM_RECEIPT_CLAIMS' && driftResult.drift !== null
          ? 'DERIVED' : 'UNVERIFIED',
        [driftRecord.evidence_id],
        '1 - cosine(goal_vector, thought_vector); threshold 0.18'
      );
      driftMetric.cosine = driftResult.cosine;
      driftMetric.halted = driftResult.halted;
      driftMetric.stream_tag = driftResult.stream_tag;
      metrics.semantic_drift = driftMetric;
    } else {
      unknowns.push(unknown('semantic_drift', 'NO_SOURCE'));
    }

    var traceCount = records.filter(function (r) { return r.kind === 'TRACE_STEP'; }).length;
    if (traceCount > 0) {
      metrics.lineage_sample = metric(
        'lineage_sample', traceCount, 'DERIVED',
        records.filter(function (r) { return r.kind === 'TRACE_STEP'; })
          .slice(0, 1).map(function (r) { return r.evidence_id; }),
        'count of sampled lineage_nodes rows in this bundle (not a total)'
      );
    }

    var merkle = firstRecord(records, 'MERKLE_CHECKPOINT');
    if (merkle && merkle.digests && merkle.digests.merkle_root) {
      metrics.merkle_root = metric(
        'merkle_root', merkle.digests.merkle_root, 'BACKED',
        [merkle.evidence_id], 'merkle_root from signed checkpoint'
      );
    } else {
      unknowns.push(unknown('merkle_root', 'NO_SOURCE'));
    }

    var golden = firstRecord(records, 'GOLDEN_CHECKPOINT');
    var goldenRate = claim(golden, 'pass_rate');
    if (goldenRate !== null) {
      metrics.golden_pass_rate = metric(
        'golden_pass_rate', goldenRate, 'BACKED', [golden.evidence_id],
        'pass_rate from GOLDEN_GROUNDEDNESS receipt'
      );
    } else {
      unknowns.push(unknown('golden_pass_rate', 'NO_SOURCE'));
    }

    Object.keys(UI_SLOTS).forEach(function (slot) {
      unknowns.push(unknown(slot, 'NO_SOURCE'));
    });

    return metrics;
  }

  async function loadBundle(bundle) {
    var failures = [];
    if (!bundle || bundle.schema_version !== SCHEMA) failures.push('SCHEMA_MISMATCH');
    var manifest = bundle && bundle.manifest;
    if (!manifest || manifest.algorithm !== 'sha256' || !crypto.isSha256Hex(manifest.digest)) {
      failures.push('INVALID_MANIFEST');
    }
    if (!bundle || !Array.isArray(bundle.records) || !Array.isArray(bundle.sources)) {
      failures.push('INVALID_SHAPE');
    }
    if (bundle && Array.isArray(bundle.records) && bundle.records.length === 0) {
      failures.push('EMPTY_BUNDLE');
    }
    if (bundle && Array.isArray(bundle.sources) && bundle.sources.length === 0) {
      failures.push('EMPTY_BUNDLE');
    }
    if (bundle && Array.isArray(bundle.records) && bundle.records.length > MAX_RECORDS) {
      failures.push('BUNDLE_TOO_LARGE');
    }
    if (bundle && Array.isArray(bundle.sources) && bundle.sources.length > MAX_SOURCES) {
      failures.push('BUNDLE_TOO_LARGE');
    }
    // The shipped build embeds a pinned bundle digest. A bundle that merely
    // self-computes a consistent manifest is not authenticated.
    var trustRoot = root.XORAS_TRUST_ROOT;
    if (trustRoot) {
      if (trustRoot.schema_version !== 'xoras.cockpit.trust-root.v1') {
        failures.push('INVALID_TRUST_ROOT');
      } else if (trustRoot.pinned_bundle_digest !== (manifest && manifest.digest)) {
        failures.push('TRUST_ROOT_MISMATCH');
      } else if (typeof trustRoot.pinned_public_key_spki_b64 !== 'string' ||
                 !trustRoot.pinned_public_key_spki_b64) {
        failures.push('MISSING_SIGNING_KEY_PIN');
      } else if (typeof trustRoot.build_seq !== 'number') {
        failures.push('MISSING_BUILD_SEQ_PIN');
      } else if (bundle.build_seq !== trustRoot.build_seq) {
        failures.push('BUILD_SEQ_MISMATCH');
      } else {
        var sigEnv = bundle.signature;
        if (!sigEnv || sigEnv.algorithm !== 'Ed25519' ||
            sigEnv.encoding !== 'raw64-hex' || typeof sigEnv.value !== 'string') {
          failures.push('SIGNATURE_MISSING');
        }
      }
    }
    if (failures.length) {
      return halted('INVALID_BUNDLE', failures, {
        schema_version: SCHEMA,
        mode: 'RECEIPT_BACKED_INVALID',
        bundle_manifest_digest: null,
        records: [],
        metrics: {},
        unknowns: [{ slot: 'bundle', reason: 'INVALID_BUNDLE' }],
        verification: null
      });
    }

    var unsigned = {};
    Object.keys(bundle).forEach(function (key) {
      if (key !== 'manifest' && key !== 'bundle_id' && key !== 'signature') {
        unsigned[key] = bundle[key];
      }
    });
    var canonicalPayload;
    try {
      canonicalPayload = crypto.canonicalStringify(unsigned);
    } catch (err) {
      return halted('INVALID_BUNDLE', ['CANONICALIZATION_FAILED'], {
        schema_version: SCHEMA, mode: 'RECEIPT_BACKED_INVALID',
        bundle_manifest_digest: manifest.digest, records: [], metrics: {},
        unknowns: [{ slot: 'bundle', reason: 'CANONICALIZATION_FAILED' }], verification: null
      });
    }
    if (canonicalPayload.length > MAX_BUNDLE_CHARS) {
      return halted('BUNDLE_TOO_LARGE', [{
        reason: 'BUNDLE_TOO_LARGE', chars: canonicalPayload.length, cap: MAX_BUNDLE_CHARS
      }], {
        schema_version: SCHEMA, mode: 'RECEIPT_BACKED_INVALID',
        bundle_manifest_digest: manifest.digest, records: [], metrics: {},
        unknowns: [{ slot: 'bundle', reason: 'BUNDLE_TOO_LARGE' }], verification: null
      });
    }
    var computed;
    try {
      computed = await crypto.sha256Hex(canonicalPayload);
    } catch (err) {
      return halted('WEBCRYPTO_UNAVAILABLE', [String(err)], {
        schema_version: SCHEMA, mode: 'RECEIPT_BACKED_INVALID',
        bundle_manifest_digest: manifest.digest, records: [], metrics: {},
        unknowns: [{ slot: 'webcrypto', reason: 'SOURCE_UNREADABLE' }], verification: null
      });
    }
    if (computed !== manifest.digest) {
      return halted('MANIFEST_MISMATCH', [{
        expected: manifest.digest, actual: computed, reason: 'BUNDLE_TAMPERED'
      }], {
        schema_version: SCHEMA, mode: 'RECEIPT_BACKED_INVALID',
        bundle_manifest_digest: manifest.digest, records: [], metrics: {},
        unknowns: [{ slot: 'bundle', reason: 'HASH_MISMATCH' }], verification: null
      });
    }

    if (trustRoot && !failures.length) {
      var signed = false;
      try {
        signed = await crypto.verifyEd25519(
          crypto.toBytes(canonicalPayload),
          bundle.signature.value,
          trustRoot.pinned_public_key_spki_b64
        );
      } catch (err) {
        return halted('WEBCRYPTO_UNAVAILABLE', [String(err)], {
          schema_version: SCHEMA, mode: 'RECEIPT_BACKED_INVALID',
          bundle_manifest_digest: manifest.digest, records: [], metrics: {},
          unknowns: [{ slot: 'signature', reason: 'WEBCRYPTO_UNAVAILABLE' }], verification: null
        });
      }
      if (!signed) {
        return halted('BAD_BUNDLE_SIGNATURE', [{ reason: 'SIGNATURE_MISMATCH' }], {
          schema_version: SCHEMA, mode: 'RECEIPT_BACKED_INVALID',
          bundle_manifest_digest: manifest.digest, records: [], metrics: {},
          unknowns: [{ slot: 'bundle', reason: 'BAD_BUNDLE_SIGNATURE' }], verification: null
        });
      }
    }

    var sourceIds = {};
    bundle.sources.forEach(function (s) { sourceIds[s.source_id] = true; });
    var validRecords = [];
    var recordFailures = [];
    var seenIds = {};
    for (var i = 0; i < bundle.records.length; i += 1) {
      var r = bundle.records[i];
      var p = r.provenance || {};
      var expectedId;
      try {
        expectedId = await crypto.sha256Hex(crypto.canonicalStringify({
          source_id: p.source_id, locator: p.locator, observed_sha256: p.observed_sha256
        }));
      } catch (err) {
        recordFailures.push({ reason: 'WEBCRYPTO_UNAVAILABLE' });
        continue;
      }
      if (r.backed !== true || !sourceIds[p.source_id] || expectedId !== r.evidence_id) {
        recordFailures.push({ evidenceId: r.evidence_id, reason: 'INVALID_RECORD' });
        continue;
      }
      if (typeof r.clearance === 'number' &&
          typeof bundle.egress_clearance === 'number' &&
          r.clearance > bundle.egress_clearance) {
        recordFailures.push({ evidenceId: r.evidence_id, reason: 'EGRESS_CLEARANCE_VIOLATION' });
        continue;
      }
      if (seenIds[r.evidence_id]) {
        recordFailures.push({ evidenceId: r.evidence_id, reason: 'DUPLICATE_EVIDENCE_REPLAY' });
        continue;
      }
      seenIds[r.evidence_id] = true;
      validRecords.push(r);
    }

    var unknowns = [];
    var kinds = {};
    validRecords.forEach(function (r) { kinds[r.kind] = true; });
    // Required slots are a code invariant, never a bundle-supplied value.
    // A bundle cannot lower its own evidence requirements.
    var required = REQUIRED_SLOTS;
    var missingSlots = required.filter(function (slot) { return !kinds[slot]; });
    var failingRecords = validRecords.filter(function (r) {
      return r.verdict === 'FAIL' || r.verdict === 'UNRECOGNIZED';
    });

    var snapshot = {
      schema_version: 'xoras.telemetry-snapshot.v1',
      mode: 'RECEIPT_BACKED',
      bundle_manifest_digest: manifest.digest,
      generator: bundle.generator || null,
      records: validRecords,
      metrics: deriveMetrics(validRecords, unknowns),
      unknowns: unknowns,
      verification: {
        state: 'REMEDIATING',
        reason: 'VERIFYING',
        failures: []
      },
      preflight: {
        missing_slots: missingSlots,
        failing_record_ids: failingRecords.map(function (r) { return r.evidence_id; }),
        record_failures: recordFailures
      }
    };
    return freeze(snapshot);
  }

  async function verifySnapshot(snapshot, bundle) {
    // A structural halt is authoritative. Verification must never overwrite it
    // with a PASS just because the (rejected) bundle has no preflight failures.
    var hardHaltReasons = [
      'INVALID_BUNDLE', 'MANIFEST_MISMATCH', 'WEBCRYPTO_UNAVAILABLE', 'INVALID_JSON',
      'BUNDLE_TOO_LARGE', 'BAD_BUNDLE_SIGNATURE'
    ];
    if (snapshot.verification && snapshot.verification.state === 'HALTED' &&
        hardHaltReasons.indexOf(snapshot.verification.reason) !== -1) {
      return snapshot;
    }

    var failures = [];
    var pre = snapshot.preflight || {};

    (pre.missing_slots || []).forEach(function (slot) {
      failures.push({ slot: slot, reason: 'MISSING_EVIDENCE' });
    });
    var byId = {};
    (snapshot.records || []).forEach(function (r) { byId[r.evidence_id] = r; });
    (pre.failing_record_ids || []).forEach(function (id) {
      failures.push({
        evidenceId: id,
        reason: (byId[id] && byId[id].verdict === 'UNRECOGNIZED')
          ? 'UNRECOGNIZED_VERDICT' : 'RECEIPT_ATTESTED_FAILURE'
      });
    });
    (pre.record_failures || []).forEach(function (f) { failures.push(f); });

    var driftMetric = (snapshot.metrics || {}).semantic_drift;
    if (driftMetric && driftMetric.halted === true) {
      failures.push({ slot: 'semantic_drift', reason: 'DRIFT_THRESHOLD_EXCEEDED' });
    }

    var artifacts = {};
    ((bundle && bundle.artifacts) || []).forEach(function (a) { artifacts[a.path] = a; });
    for (var i = 0; i < snapshot.records.length; i += 1) {
      var r = snapshot.records[i];
      if (r.kind !== 'HASH_ASSERT') continue;
      var attestation = (r.provenance || {}).attestation;
      if (attestation !== 'RECOMPUTED_IN_BROWSER') continue;
      var artifact = artifacts[r.subject];
      if (!artifact || !artifact.bytes_b64) {
        failures.push({ evidenceId: r.evidence_id, reason: 'EVIDENCE_ABSENT' });
        continue;
      }
      var bytes = Uint8Array.from(atob(artifact.bytes_b64), function (c) { return c.charCodeAt(0); });
      var actual = await crypto.sha256Hex(bytes);
      var expected = (r.digests || {}).sha256 || null;
      if (!expected || actual !== expected) {
        failures.push({ evidenceId: r.evidence_id, expected: expected, actual: actual, reason: 'HASH_MISMATCH' });
      }
    }

    var state;
    var reason;
    if (failures.length === 0) {
      state = 'VERIFIED';
      reason = 'ALL_REQUIRED_EVIDENCE_PRESENT';
    } else {
      state = 'HALTED';
      reason = failures.some(function (f) { return f.reason === 'HASH_MISMATCH'; })
        ? 'HASH_MISMATCH'
        : 'FAIL_CLOSED';
    }
    var next = Object.assign({}, snapshot, {
      verification: { state: state, reason: reason, failures: failures }
    });
    return freeze(next);
  }

  function simulationSnapshot() {
    var unknowns = Object.keys(UI_SLOTS).map(function (slot) {
      return unknown(slot, 'NO_SOURCE');
    });
    unknowns.push({ slot: 'all', reason: 'NO_BUNDLE_LOADED' });
    return freeze({
      schema_version: 'xoras.telemetry-snapshot.v1',
      mode: 'SIMULATION',
      bundle_manifest_digest: null,
      records: [],
      metrics: {},
      unknowns: unknowns,
      verification: { state: 'UNVERIFIED', reason: 'NO_EVIDENCE_LOADED', failures: [] },
      preflight: { missing_slots: [], failing_record_ids: [], record_failures: [] }
    });
  }

  function parseFailureSnapshot() {
    return freeze({
      schema_version: 'xoras.telemetry-snapshot.v1',
      mode: 'RECEIPT_BACKED_INVALID',
      bundle_manifest_digest: null,
      records: [],
      metrics: {},
      unknowns: [{ slot: 'bundle', reason: 'SOURCE_UNREADABLE' }],
      verification: { state: 'HALTED', reason: 'INVALID_JSON', failures: [{ reason: 'PARSE_ERROR' }] },
      preflight: { missing_slots: [], failing_record_ids: [], record_failures: [] }
    });
  }

  XORAS.evidenceAdapter = {
    SCHEMA: SCHEMA,
    REQUIRED_SLOTS: REQUIRED_SLOTS,
    loadBundle: loadBundle,
    verifySnapshot: verifySnapshot,
    simulationSnapshot: simulationSnapshot,
    parseFailureSnapshot: parseFailureSnapshot
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = XORAS.evidenceAdapter;
})(typeof globalThis !== 'undefined' ? globalThis : this);
