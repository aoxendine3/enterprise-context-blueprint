/* XORAS Cockpit - real SHA-256 only. No fallback, no fabrication. */
(function (root) {
  'use strict';
  var XORAS = (root.XORAS = root.XORAS || {});
  var encoder = new TextEncoder();

  function isSha256Hex(value) {
    return typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
  }

  function toHex(buffer) {
    var bytes = new Uint8Array(buffer);
    var out = '';
    for (var i = 0; i < bytes.length; i += 1) {
      out += bytes[i].toString(16).padStart(2, '0');
    }
    return out;
  }

  function toBytes(input) {
    if (input === null || input === undefined) return null;
    if (typeof input === 'string') return encoder.encode(input);
    if (input instanceof Uint8Array) return input;
    if (input instanceof ArrayBuffer) return new Uint8Array(input);
    return null;
  }

  async function sha256Hex(input) {
    var bytes = toBytes(input);
    if (bytes === null) return null;
    if (!root.crypto || !root.crypto.subtle) {
      throw new Error('WEBCRYPTO_UNAVAILABLE');
    }
    var digest = await root.crypto.subtle.digest('SHA-256', bytes);
    var hex = toHex(digest);
    if (!isSha256Hex(hex)) throw new Error('INVALID_DIGEST_LENGTH');
    return hex;
  }

  // Deterministic canonicalization matching Python:
  // json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=False)
  function canonicalStringify(value) {
    if (value === null) return 'null';
    var type = typeof value;
    if (type === 'string') return JSON.stringify(value);
    if (type === 'boolean') return value ? 'true' : 'false';
    if (type === 'number') {
      if (!Number.isFinite(value)) throw new Error('NON_FINITE_NUMBER');
      return JSON.stringify(value);
    }
    if (Array.isArray(value)) {
      return '[' + value.map(canonicalStringify).join(',') + ']';
    }
    if (type === 'object') {
      var keys = Object.keys(value).sort();
      var parts = [];
      for (var i = 0; i < keys.length; i += 1) {
        parts.push(JSON.stringify(keys[i]) + ':' + canonicalStringify(value[keys[i]]));
      }
      return '{' + parts.join(',') + '}';
    }
    throw new Error('UNSUPPORTED_TYPE');
  }

  function base64ToBytes(b64) {
    if (typeof b64 !== 'string' || !/^[A-Za-z0-9+/]+={0,2}$/.test(b64)) {
      throw new Error('INVALID_BASE64');
    }
    var binary;
    try { binary = atob(b64); } catch (err) { throw new Error('INVALID_BASE64'); }
    var out = new Uint8Array(binary.length);
    for (var i = 0; i < binary.length; i += 1) out[i] = binary.charCodeAt(i);
    return out;
  }

  function signatureHexToBytes(hex) {
    if (typeof hex !== 'string' || !/^[0-9a-f]{128}$/.test(hex)) {
      throw new Error('INVALID_SIGNATURE_ENCODING');
    }
    var out = new Uint8Array(64);
    for (var i = 0; i < 64; i += 1) {
      out[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
    }
    return out;
  }

  async function verifyEd25519(messageBytes, signatureHex, spkiB64) {
    if (!root.crypto || !root.crypto.subtle) throw new Error('WEBCRYPTO_UNAVAILABLE');
    var key = await root.crypto.subtle.importKey(
      'spki', base64ToBytes(spkiB64), { name: 'Ed25519' }, false, ['verify']
    );
    return root.crypto.subtle.verify(
      { name: 'Ed25519' }, key, signatureHexToBytes(signatureHex), messageBytes
    );
  }

  XORAS.crypto = {
    sha256Hex: sha256Hex,
    isSha256Hex: isSha256Hex,
    canonicalStringify: canonicalStringify,
    toBytes: toBytes,
    base64ToBytes: base64ToBytes,
    signatureHexToBytes: signatureHexToBytes,
    verifyEd25519: verifyEd25519
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = XORAS.crypto;
})(typeof globalThis !== 'undefined' ? globalThis : this);
