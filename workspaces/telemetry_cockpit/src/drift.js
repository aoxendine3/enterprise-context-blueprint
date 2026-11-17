/* XORAS Cockpit - real semantic drift metric. No simulated values.
   Drift(N) = 1 - cosine(goal, thought). Threshold from the operational standard. */
(function (root) {
  'use strict';
  var XORAS = (root.XORAS = root.XORAS || {});

  var DRIFT_THRESHOLD = 0.18;
  var MIN_SIMILARITY = 0.82;

  function validVector(vec) {
    return Array.isArray(vec) && vec.length > 0 && vec.every(function (n) {
      return typeof n === 'number' && Number.isFinite(n);
    });
  }

  function cosineSimilarity(a, b) {
    if (!validVector(a) || !validVector(b) || a.length !== b.length) return null;
    var dot = 0, na = 0, nb = 0;
    for (var i = 0; i < a.length; i += 1) {
      dot += a[i] * b[i];
      na += a[i] * a[i];
      nb += b[i] * b[i];
    }
    if (na === 0 || nb === 0) return null;
    return dot / (Math.sqrt(na) * Math.sqrt(nb));
  }

  function semanticDrift(goalVector, thoughtVector) {
    var cosine = cosineSimilarity(goalVector, thoughtVector);
    if (cosine === null) {
      return {
        cosine: null,
        drift: null,
        stream_tag: 'UNVERIFIED',
        reason: 'NO_VALID_VECTORS',
        halted: false
      };
    }
    var drift = 1 - cosine;
    return {
      cosine: cosine,
      drift: drift,
      stream_tag: 'DERIVED_FROM_RECEIPT_CLAIMS',
      reason: (drift > DRIFT_THRESHOLD || cosine < MIN_SIMILARITY)
        ? 'DRIFT_ABOVE_THRESHOLD' : 'WITHIN_THRESHOLD',
      halted: drift > DRIFT_THRESHOLD || cosine < MIN_SIMILARITY
    };
  }

  XORAS.drift = {
    DRIFT_THRESHOLD: DRIFT_THRESHOLD,
    MIN_SIMILARITY: MIN_SIMILARITY,
    validVector: validVector,
    cosineSimilarity: cosineSimilarity,
    semanticDrift: semanticDrift
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = XORAS.drift;
})(typeof globalThis !== 'undefined' ? globalThis : this);
