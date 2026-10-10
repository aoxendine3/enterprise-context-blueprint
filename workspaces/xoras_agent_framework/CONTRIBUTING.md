# Contributing to XORAS Agentic Framework

We welcome contributions to the **XORAS Agentic Environment & Governance Framework**.

## Development Workflow

1. Fork the repository and clone your branch locally.
2. Install development dependencies:
   ```bash
   pip install -e .[dev]
   ```
3. Run the unit test suite before submitting pull requests:
   ```bash
   PYTHONPATH=. pytest tests/
   ```
4. Ensure all code changes maintain 100% AST safety compliance and structured JSON-L trace receipts.
