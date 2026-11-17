import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const dist = join(root, 'dist');
const src = join(root, 'src');

const html = readFileSync(join(dist, 'index.html'), 'utf8');
const js = readFileSync(join(dist, 'cockpit.js'), 'utf8');
const css = readFileSync(join(dist, 'cockpit.css'), 'utf8');
const allJs = ['crypto.js', 'drift.js', 'state-machine.js', 'evidence-adapter.js', 'app.js']
  .map(f => readFileSync(join(src, f), 'utf8')).join('\n');
// Comments that *describe* removed sinks are not sinks. Scan executable text.
const codeOnly = allJs
  .replace(/\/\*[\s\S]*?\*\//g, '')
  .replace(/^\s*\/\/.*$/gm, '');
const allSource = html + js + css + codeOnly;

test('no external network references anywhere', () => {
  assert.equal(/https?:\/\//.test(allSource), false, 'external URL found');
  assert.equal(/cdn\.tailwindcss\.com/.test(allSource), false);
});

test('strict CSP present with connect-src self and no unsafe-inline', () => {
  assert.match(html, /Content-Security-Policy/);
  assert.match(html, /connect-src 'self'/);
  assert.equal(/connect-src 'none'/.test(html), false);
  assert.equal(/unsafe-inline/.test(html), false);
  assert.equal(/unsafe-eval/.test(html), false);
});

test('auto-load is same-origin relative only, never cross-origin', () => {
  assert.match(codeOnly, /fetch\('\.\/evidence-bundle\.json'\)/, 'auto-load must target the relative sibling bundle');
  const protoGuard = codeOnly.match(/proto === 'https:' \|\| proto === 'http:'/);
  assert.ok(protoGuard, 'auto-load must be gated to HTTP(S) transport');
  // No absolute or protocol-relative target may appear inside any fetch call.
  for (const m of codeOnly.matchAll(/fetch\(([^)]*)\)/g)) {
    assert.equal(/['"`]https?:\/\//.test(m[1]), false, 'cross-origin fetch target: ' + m[1]);
    assert.equal(/['"`]\/\//.test(m[1]), false, 'protocol-relative fetch target: ' + m[1]);
  }
});

test('no fake hash primitives', () => {
  for (const pattern of ['pseudoSha256', 'Math.imul', '2654435761', '1597334677', '0xdeadbeef']) {
    assert.equal(allSource.includes(pattern), false, pattern + ' still present');
  }
});

test('no hardcoded pass or mutable verification global', () => {
  assert.equal(/passed\s*:\s*true/.test(codeOnly), false);
  assert.equal(/state\.halted\s*=/.test(codeOnly), false);
  assert.equal(/FORCE\s*RESUME/.test(codeOnly), false);
  assert.equal(/forceResumeExecution/.test(codeOnly), false);
});

test('no string-templated injection sinks', () => {
  assert.equal(/innerHTML/.test(codeOnly), false);
  assert.equal(/insertAdjacentHTML/.test(codeOnly), false);
  assert.equal(/document\.write/.test(codeOnly), false);
  assert.equal(/onclick\s*=/.test(codeOnly), false);
  assert.equal(/\beval\s*\(/.test(codeOnly), false);
  assert.equal(/new Function\s*\(/.test(codeOnly), false);
});

test('no nondeterministic salts in hash or id paths', () => {
  assert.equal(/Date\.now/.test(codeOnly), false);
  assert.equal(/Math\.random/.test(codeOnly), false);
});

test('real WebCrypto digest is the only hash primitive', () => {
  assert.match(allJs, /crypto\.subtle\.digest\(['"]SHA-256['"]/);
  assert.match(allJs, /TextEncoder/);
});

test('dist bundle is a concatenation of all four modules', () => {
  for (const marker of ['XORAS.crypto', 'XORAS.drift', 'XORAS.stateMachine', 'XORAS.evidenceAdapter', '__XORAS_TEST__']) {
    assert.ok(js.includes(marker), marker + ' missing from dist');
  }
});

test('no fabricated telemetry constants from the old mockup', () => {
  for (const value of ['0.012%', '94.8', '91.4%', '14/14', '3,910 tok', 'e3b0c442..924']) {
    assert.equal(allJs.includes(value), false, value + ' still hardcoded');
  }
});
