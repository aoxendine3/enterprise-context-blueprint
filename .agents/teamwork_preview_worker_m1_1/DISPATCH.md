## 2026-09-12T12:12:53Z

<USER_REQUEST>
You are Worker 1 (Demonstration Application Implementer).
Your Working Directory: c:\Users\admin\Desktop\SSOT_Agentic_Brain\.agents\teamwork_preview_worker_m1_1
Workspace Root: c:\Users\admin\Desktop\SSOT_Agentic_Brain
Original Request path: c:\Users\admin\Desktop\SSOT_Agentic_Brain\.agents\ORIGINAL_REQUEST.md
Project Scope path: c:\Users\admin\Desktop\SSOT_Agentic_Brain\.agents\orchestrator_1\PROJECT.md
Survey Handoffs:
- Explorer 1 (Environment & Architecture): c:\Users\admin\Desktop\SSOT_Agentic_Brain\.agents\teamwork_preview_explorer_survey_1\handoff.md
- Explorer 2 (Requirements & Features): c:\Users\admin\Desktop\SSOT_Agentic_Brain\.agents\teamwork_preview_explorer_survey_2\handoff.md
- Explorer 3 (Test Suite Architecture): c:\Users\admin\Desktop\SSOT_Agentic_Brain\.agents\teamwork_preview_explorer_survey_3\handoff.md

You MUST read `c:\Users\admin\Desktop\SSOT_Agentic_Brain\.agents\ORIGINAL_REQUEST.md` and `c:\Users\admin\Desktop\SSOT_Agentic_Brain\.agents\orchestrator_1\PROJECT.md` before starting work.

DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write Ownership:
You exclusively own all files in `workspaces/demo_app/`:
- `workspaces/demo_app/main.py`
- `workspaces/demo_app/README.md`
- `workspaces/demo_app/demo_app/__init__.py`
- `workspaces/demo_app/demo_app/__main__.py`
- `workspaces/demo_app/demo_app/cli.py`
- `workspaces/demo_app/demo_app/greeting.py`
- `workspaces/demo_app/demo_app/processor.py`
- `workspaces/demo_app/tests/__init__.py`
- `workspaces/demo_app/tests/run_tests.py`
- `workspaces/demo_app/tests/test_greeting.py`
- `workspaces/demo_app/tests/test_processor.py`
- `workspaces/demo_app/tests/test_cli.py`
- `workspaces/demo_app/tests/test_integration.py`
Do NOT write code or test files to `.agents/` or to the workspace root.

Task Requirements:
1. Implement the demonstration application in `workspaces/demo_app/` using pure Python 3 standard library:
   - `greeting.py`: Default 'Hello, World!', custom name via `--name`, tone styles (`standard`, `formal`, `casual`, `sovereign`, `enthusiastic`), and template interpolation (`--template`).
   - `processor.py`: System diagnostics (`get_system_info()`), workspace health check (`get_workspace_health()`), arithmetic operations (`add`, `sub`, `mul`, `div`, `pow`, `mod` with division-by-zero protection returning code 1), statistics computation (`compute_stats()`), Fibonacci generator, and primality testing.
   - `cli.py`: Argument parser with subcommands (`greet`, `status`, `calc`) or default summary mode when run without arguments. Global `--json` support formatting all outputs as strictly valid JSON. Clean exit codes (0 for success, 1 for operational error, 2 for CLI argument error).
   - `main.py` & `__main__.py`: Execution entrypoints.
   - `README.md`: Clear documentation with usage and test instructions.
2. Implement the comprehensive test suite in `workspaces/demo_app/tests/`:
   - Unit tests covering all modules and edge cases (empty strings, whitespace, Unicode, division by zero, invalid styles, etc.).
   - Integration / E2E tests executing the CLI via `subprocess.run([sys.executable, ...])` verifying exit codes 0, 1, 2, stdout, stderr, and `--json` parseability.
   - `tests/run_tests.py`: Standalone runner script reporting total tests, pass/fail counts, duration, and exit code.
3. Run the tests using terminal commands:
   - `python workspaces/demo_app/tests/run_tests.py`
   - `python -m unittest discover -s workspaces/demo_app/tests -v`
   - Test CLI invocations (`main.py`, `main.py --name Anthony`, `main.py --calc 1,2,3,4 --json`, etc.)
   Verify all tests pass with 0 failures and 0 errors.
4. Document all implementation details, commands run, test results, and file paths in `c:\Users\admin\Desktop\SSOT_Agentic_Brain\.agents\teamwork_preview_worker_m1_1\handoff.md`.
5. Send a completion message to parent when finished.
</USER_REQUEST>
