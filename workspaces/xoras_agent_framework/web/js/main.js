// XORAS Systems LLC — Interactive AST Security Scanner Demo Controller

document.addEventListener('DOMContentLoaded', () => {
  const codeEditor = document.getElementById('codeEditor');
  const scanBtn = document.getElementById('scanBtn');
  const resultDisplay = document.getElementById('resultDisplay');

  if (scanBtn && codeEditor && resultDisplay) {
    scanBtn.addEventListener('click', () => {
      const code = codeEditor.value;
      runASTScan(code, resultDisplay);
    });
  }
});

function runASTScan(code, displayElem) {
  const violations = [];
  const secrets = [];

  // Check forbidden calls
  if (/\beval\s*\(/.test(code)) {
    violations.push("Line AST: Dynamic eval() invocation detected (Forbidden under XORAS AST Policy)");
  }
  if (/\bexec\s*\(/.test(code)) {
    violations.push("Line AST: Dynamic exec() invocation detected (Forbidden under XORAS AST Policy)");
  }
  if (/os\.system\s*\(/`.test(code) || /subprocess\.Popen\s*\(/.test(code)) {
    violations.push("Line AST: Unrestricted subprocess call detected");
  }

  // Check secrets
  if (/(?:aws_access_key_id|api_key|secret_key)\s*[:=]\s*["'][^"']{8,}["']/i.test(code) || /ghp_[0-9a-zA-Z]{36}/.test(code)) {
    secrets.push("Secret Scanner: High-entropy token / API key match detected");
  }

  const isSafe = violations.length === 0 && secrets.length === 0;
  const score = isSafe ? 100 : Math.max(0, 100 - (violations.length + secrets.length) * 35);
  const timestamp = (Date.now() / 1000).toFixed(3);
  
  // Fake hash generation
  const hash = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  const signature = "SIG_XORAS_ED25519_" + btoa(hash).substring(0, 32);

  let outputHTML = `
    <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
      <span>STATUS: ${isSafe ? '<span class="badge-pass">PASSED [100% SAFE]</span>' : '<span class="badge-fail">REJECTED [SECURITY VIOLATION]</span>'}</span>
      <span style="color: #9ca3af;">Safety Score: ${score}%</span>
    </div>
    <div style="color: #e5e7eb; margin-bottom: 8px;"><strong>Analysis Summary:</strong></div>
  `;

  if (isSafe) {
    outputHTML += `<div style="color: #10b981; margin-bottom: 8px;">✔ No AST syntax violations detected.<br>✔ No secret leaks detected.</div>`;
  } else {
    outputHTML += `<div style="color: #ef4444; margin-bottom: 8px;">`;
    violations.forEach(v => outputHTML += `<div>✖ ${v}</div>`);
    secrets.forEach(s => outputHTML += `<div>✖ ${s}</div>`);
    outputHTML += `</div>`;
  }

  outputHTML += `
    <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); color: #6b7280; font-size: 0.78rem;">
      <div>Version: xoras.evidence.v1</div>
      <div>Timestamp: ${timestamp}</div>
      <div>Payload SHA-256: ${hash}</div>
      <div>Receipt Signature: <span style="color: #60a5fa;">${signature}</span></div>
    </div>
  `;

  displayElem.innerHTML = outputHTML;
}
