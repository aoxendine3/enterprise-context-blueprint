/* XORAS Cockpit - DOM renderer. Pure projection of TelemetrySnapshot.
   No inline handlers, no innerHTML, no computed truth in this file. */
(function (root) {
  'use strict';
  var doc = root.document;
  var XORAS = (root.XORAS = root.XORAS || {});
  var adapter = XORAS.evidenceAdapter;
  var machine = XORAS.stateMachine;

  var currentSnapshot = null;
  var currentBundle = null;

  function el(tag, className, text) {
    var node = doc.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function badge(text, tone) {
    return el('span', 'badge badge-' + tone, text);
  }

  function renderBanner(snapshot) {
    var banner = doc.getElementById('mode-banner');
    clear(banner);
    if (snapshot.mode === 'SIMULATION') {
      banner.className = 'banner banner-sim';
      banner.appendChild(el('strong', '', 'MODE: SIMULATION — NOTHING IS RECEIPT-BACKED'));
      banner.appendChild(el('span', '', 'All values below are UNVERIFIED. No receipt or database row has been read.'));
    } else if (snapshot.mode === 'RECEIPT_BACKED_INVALID') {
      banner.className = 'banner banner-halt';
      banner.appendChild(el('strong', '', 'MODE: BUNDLE REJECTED'));
      banner.appendChild(el('span', '', 'The loaded bundle failed structural verification.'));
    } else {
      banner.className = 'banner banner-backed';
      banner.appendChild(el('strong', '', 'MODE: RECEIPT-BACKED'));
      banner.appendChild(el('span', 'mono', (snapshot.bundle_manifest_digest || '').slice(0, 16)));
    }
  }

  function renderVerification(snapshot) {
    var panel = doc.getElementById('verification-panel');
    clear(panel);
    var v = snapshot.verification || { state: 'UNKNOWN', reason: 'NONE', failures: [] };
    panel.appendChild(el('div', 'panel-label', 'VERIFICATION STATE'));
    var row = el('div', 'verification-row');
    var tone = v.state === 'VERIFIED' ? 'ok' : (v.state === 'HALTED' || v.state === 'DIVERGED' ? 'halt' : 'warn');
    row.appendChild(badge(v.state, tone));
    row.appendChild(el('span', 'reason', v.reason));
    panel.appendChild(row);
    if (v.failures && v.failures.length) {
      var list = el('ul', 'failure-list');
      v.failures.slice(0, 12).forEach(function (f) {
        list.appendChild(el('li', '', (f.reason || 'FAILURE') + ' :: ' +
          (f.evidenceId || f.slot || f.expected || 'unknown')));
      });
      panel.appendChild(list);
      if (v.failures.length > 12) {
        panel.appendChild(el('div', 'muted', '+' + (v.failures.length - 12) + ' more failures'));
      }
    }
  }

  function renderMetrics(snapshot) {
    var grid = doc.getElementById('metrics-grid');
    clear(grid);
    var keys = Object.keys(snapshot.metrics || {});
    if (keys.length === 0) {
      grid.appendChild(el('div', 'empty', 'No receipt-backed metrics available.'));
      return;
    }
    keys.forEach(function (key) {
      var m = snapshot.metrics[key];
      var card = el('div', 'metric-card');
      card.appendChild(el('div', 'metric-key', key));
      card.appendChild(el('div', 'metric-value', m.value));
      var foot = el('div', 'metric-foot');
      var tone = m.status === 'BACKED' ? 'ok' : (m.status === 'DERIVED' ? 'info' : 'warn');
      foot.appendChild(badge(m.status, tone));
      if (m.stream_tag) foot.appendChild(el('span', 'mono muted tiny', m.stream_tag));
      if (m.evidence_ids && m.evidence_ids.length) {
        foot.appendChild(el('span', 'mono muted', m.evidence_ids[0].slice(0, 12)));
      }
      card.appendChild(foot);
      if (m.derivation) card.appendChild(el('div', 'derivation', m.derivation));
      grid.appendChild(card);
    });
  }

  function renderUnknowns(snapshot) {
    var list = doc.getElementById('unknowns-list');
    clear(list);
    var unknowns = snapshot.unknowns || [];
    if (!unknowns.length) {
      list.appendChild(el('li', 'empty', 'None — every slot resolves to evidence.'));
      return;
    }
    unknowns.forEach(function (u) {
      list.appendChild(el('li', '', u.slot + ' — ' + u.reason));
    });
  }

  function renderRecords(snapshot) {
    var list = doc.getElementById('records-list');
    clear(list);
    var records = snapshot.records || [];
    doc.getElementById('record-count').textContent = String(records.length);
    if (!records.length) {
      list.appendChild(el('div', 'empty', 'No records loaded. Evidence is absent, so nothing can be verified.'));
      return;
    }
    records.slice(0, 60).forEach(function (r) {
      var row = el('div', 'record-row');
      var head = el('div', 'record-head');
      head.appendChild(badge(r.kind || 'UNKNOWN', 'info'));
      head.appendChild(badge(r.verdict || 'UNKNOWN',
        r.verdict === 'FAIL' ? 'halt'
          : (r.verdict === 'UNRECOGNIZED' ? 'warn' : 'info')));
      head.appendChild(el('span', 'record-subject', r.subject));
      if (r.verdict_raw) head.appendChild(el('span', 'mono muted tiny', r.verdict_raw));
      row.appendChild(head);
      var p = r.provenance || {};
      row.appendChild(el('div', 'mono muted tiny', p.locator || 'no locator'));
      row.appendChild(el('div', 'mono tiny', p.observed_sha256 || 'NO DIGEST'));
      list.appendChild(row);
    });
    if (records.length > 60) {
      list.appendChild(el('div', 'muted', '+' + (records.length - 60) + ' more records (not hidden from verification)'));
    }
  }

  function renderControls(snapshot) {
    var exportBtn = doc.getElementById('btn-export');
    var canExport = machine.canMutate(snapshot.verification.state) && snapshot.mode === 'RECEIPT_BACKED';
    exportBtn.disabled = !canExport;
    exportBtn.title = canExport ? 'Export verified snapshot' : 'Disabled — verification is not VERIFIED';
  }

  function render(snapshot) {
    currentSnapshot = snapshot;
    renderBanner(snapshot);
    renderVerification(snapshot);
    renderMetrics(snapshot);
    renderUnknowns(snapshot);
    renderRecords(snapshot);
    renderControls(snapshot);
  }

  async function loadFromText(text) {
    var bundle;
    try {
      bundle = JSON.parse(text);
    } catch (err) {
      render(adapter.parseFailureSnapshot());
      return;
    }
    currentBundle = bundle;
    var loaded = await adapter.loadBundle(bundle);
    var verified = await adapter.verifySnapshot(loaded, bundle);
    render(verified);
  }

  function exportSnapshot() {
    if (!currentSnapshot || !machine.canMutate(currentSnapshot.verification.state)) return;
    var payload = {
      schema_version: 'xoras.telemetry-snapshot.v1',
      bundle_manifest_digest: currentSnapshot.bundle_manifest_digest,
      verification: currentSnapshot.verification,
      metrics: currentSnapshot.metrics,
      records: currentSnapshot.records.map(function (r) {
        return { evidence_id: r.evidence_id, kind: r.kind, subject: r.subject,
                 verdict: r.verdict, provenance: r.provenance };
      })
    };
    var blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    var url = root.URL.createObjectURL(blob);
    var link = doc.createElement('a');
    link.href = url;
    link.download = 'xor-cockpit-snapshot.json';
    doc.body.appendChild(link);
    link.click();
    doc.body.removeChild(link);
    root.URL.revokeObjectURL(url);
  }

  function init() {
    render(adapter.simulationSnapshot());

    var input = doc.getElementById('file-input');
    input.addEventListener('change', async function (event) {
      var file = event.target.files && event.target.files[0];
      if (!file) return;
      await loadFromText(await file.text());
    });

    doc.getElementById('btn-export').addEventListener('click', exportSnapshot);
    doc.getElementById('btn-reset').addEventListener('click', function () {
      currentBundle = null;
      input.value = '';
      render(adapter.simulationSnapshot());
    });

    root.__XORAS_TEST__ = {
      render: render,
      loadFromText: loadFromText,
      getSnapshot: function () { return currentSnapshot; },
      getBundle: function () { return currentBundle; },
      simulation: function () { return adapter.simulationSnapshot(); }
    };

    // Same-origin auto-load: when served over HTTP(S), the signed bundle sits
    // next to this page; load it once. Relative path only — no external
    // origin can ever be contacted. File:// keeps the manual-only contract.
    // Every failure path stays SIMULATION: the transport is never trusted,
    // the WebCrypto signature verification is.
    var proto = root.location && root.location.protocol;
    if (proto === 'https:' || proto === 'http:') {
      fetch('./evidence-bundle.json')
        .then(function (res) {
          if (!res.ok) throw new Error('HTTP ' + res.status);
          return res.text();
        })
        .then(function (text) { return loadFromText(text); })
        .catch(function () { /* fail closed: stay SIMULATION */ });
    }
  }

  if (doc.readyState === 'loading') {
    doc.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})(typeof window !== 'undefined' ? window : this);
