# AST Security Gating Architecture

## Overview
The **XORAS AST Security Engine** (`xoras.ast_security`) performs static syntax tree inspection and entropy analysis on code payloads prior to execution by the runtime harness.

## Security Rules
1. **Forbidden Functions**: `eval()`, `exec()`, `compile()`, `__import__()`.
2. **Subprocess Rules**: Calls to `subprocess.Popen` or `os.system` with `shell=True` or dangerous arguments (`rm -rf`) are intercepted and rejected.
3. **Entropy Secret Scanner**: Regular expression analysis targeting AWS keys, GitHub tokens, Slack tokens, and private RSA key blocks.

## Safety Score Calculation
Each violation reduces the safety score:
$$\text{Safety Score} = \max\left(0.0, 1.0 - 0.35 \times n_{\text{violations}}\right)$$
Only payloads with a safety score of $1.0$ (0 violations) advance to runtime tool execution.
