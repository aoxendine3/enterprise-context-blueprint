import sys
import traceback
import sqlite3
import os
import time
import hashlib
import requests
import py_compile
import shutil


class XorasImmuneSystem:
    def __init__(
        self,
        db_path=(
            "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/"
            "Omni_Dojo_Sandbox/Error_Catalyst/global_catalyst.db"
        ),
        llm_endpoint="http://192.168.1.133:11434/api/generate",
        model="qwen2.5-coder:1.5b"
    ):
        self.db_path = db_path
        self.llm_endpoint = llm_endpoint
        self.model = model
        self.original_excepthook = sys.excepthook
        sys.excepthook = self._global_exception_handler

    def _log_to_db(self, exc_type, err_msg, tb_str, status, heal_action):
        try:
            conn = sqlite3.connect(self.db_path)
            # Use the global_catalyst.db schema for error logs
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS error_logs
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               timestamp TEXT,
                               exception_type TEXT,
                               error_message TEXT,
                               stack_trace TEXT,
                               status TEXT DEFAULT 'OPEN',
                               healing_action TEXT)''')

            cursor.execute(
                '''INSERT INTO error_logs
                   (timestamp, exception_type, error_message, stack_trace,
                    status, healing_action)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (str(time.time()), str(exc_type), str(err_msg), tb_str,
                 status, heal_action)
            )
            conn.commit()
            err_id = cursor.lastrowid
            conn.close()
            return err_id
        except Exception as e:
            print(f"[IMMUNE-SYSTEM] Failed to log error: {e}")
            return None

    def _update_db_status(self, err_id, status, heal_action):
        if not err_id:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE error_logs SET status=?, healing_action=? WHERE id=?",
                (status, heal_action, err_id)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _generate_patch(self, file_path, exc_type, err_msg, tb_str):
        print(f"[IMMUNE-SYSTEM] Analyzing fracture in {file_path} via local LLM...")
        try:
            with open(file_path, "r") as f:
                source_code = f.read()
        except Exception:
            return None

        prompt = f"""You are the Xoras Active Immune System. \
A critical exception occurred in the following Python file.
Exception Type: {exc_type}
Error Message: {err_msg}
Traceback:
{tb_str}

Source Code:
```python
{source_code}
```

Provide ONLY the completely rewritten, corrected Python source code. \
Do not include markdown formatting backticks around the final output, \
just pure python code. Do not include explanations."""

        try:
            response = requests.post(
                self.llm_endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            if response.status_code == 200:
                data = response.json()
                patched_code = data.get("response", "").strip()
                # Clean markdown if model still included it
                if patched_code.startswith("```python"):
                    patched_code = patched_code[9:]
                if patched_code.endswith("```"):
                    patched_code = patched_code[:-3]
                return patched_code.strip()
            else:
                print(
                    "[IMMUNE-SYSTEM] LLM API returned status "
                    f"{response.status_code}: {response.text}"
                )
        except Exception as e:
            print(f"[IMMUNE-SYSTEM] LLM Patch generation failed: {e}")
        return None

    def _auto_apply_enabled(self):
        return os.environ.get("XORAS_IMMUNE_AUTO_APPLY", "").strip() == "1"

    def _apply_patch(self, file_path, patched_code):
        """
        Returns (artifact_path, outcome) where outcome is
        'applied' | 'proposed' | 'failed'.

        Default is SAFE MODE (propose-only). Auto-apply requires
        XORAS_IMMUNE_AUTO_APPLY=1.
        """
        digest = hashlib.sha256(patched_code.encode("utf-8")).hexdigest()

        # SAFE MODE (default): write proposal, log path/hash, do not hot-swap.
        if not self._auto_apply_enabled():
            propose_path = f"{file_path}.proposed.{digest[:12]}.py"
            with open(propose_path, "w") as f:
                f.write(patched_code)
            try:
                py_compile.compile(propose_path, doraise=True)
                print(
                    "[IMMUNE-SYSTEM] SAFE MODE: propose-only "
                    "(set XORAS_IMMUNE_AUTO_APPLY=1 to enable auto-apply)"
                )
                print(
                    f"[IMMUNE-SYSTEM] proposed_path={propose_path} "
                    f"sha256={digest}"
                )
                return propose_path, "proposed"
            except py_compile.PyCompileError as e:
                print(f"[IMMUNE-SYSTEM] Proposed patch syntax check failed: {e}")
                return propose_path, "failed"

        # Auto-apply path (explicit opt-in only)
        backup_path = file_path + ".bak"
        shutil.copy2(file_path, backup_path)

        test_path = file_path + ".test"
        with open(test_path, "w") as f:
            f.write(patched_code)

        try:
            # Fast syntax compile check
            py_compile.compile(test_path, doraise=True)
            print("[IMMUNE-SYSTEM] Syntax check passed. Injecting patch...")

            # Hot-swap the file
            shutil.copy2(test_path, file_path)
            os.remove(test_path)
            return backup_path, "applied"
        except py_compile.PyCompileError as e:
            print(f"[IMMUNE-SYSTEM] Syntax check failed: {e}")
            os.remove(test_path)
            return backup_path, "failed"

    def _global_exception_handler(self, exc_type, exc_value, exc_traceback):
        # Prevent recursive immune failures
        sys.excepthook = self.original_excepthook

        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(f"\\\\n\\\\n[IMMUNE-SYSTEM] CRITICAL FAULT DETECTED\\\\n{tb_str}")

        err_id = self._log_to_db(exc_type.__name__, str(
            exc_value), tb_str, "FRACTURED", "Awaiting AI Intervention")

        # Extract the file where the exception occurred
        tb = traceback.extract_tb(exc_traceback)
        target_file = None
        for frame in reversed(tb):
            if not frame.filename.startswith("<"):
                target_file = frame.filename
                break

        if not target_file or not os.path.exists(target_file):
            print(
                "[IMMUNE-SYSTEM] Fault cannot be localized to a physical "
                "file. System Halting."
            )
            self._update_db_status(err_id, "FATAL", "Un-localizable fault")
            sys.exit(1)

        # Retry logic
        for attempt in range(3):
            print(f"[IMMUNE-SYSTEM] Healing attempt {attempt + 1}/3...")
            patched_code = self._generate_patch(
                target_file, exc_type.__name__, str(exc_value), tb_str)
            if not patched_code:
                continue

            artifact, outcome = self._apply_patch(target_file, patched_code)

            if outcome == "applied":
                print(
                    f"[IMMUNE-SYSTEM] Module {target_file} patched. "
                    "Generating hot-swap trigger."
                )
                self._update_db_status(
                    err_id, "HEALED",
                    f"Successfully rewrote logic in {target_file}"
                )

                # We attempt to dynamically reload the module if it's imported,
                # but since we caught this globally, the main thread has already
                # unspooled. The process will exit, but the next run will be
                # permanently fixed.
                print(
                    "[IMMUNE-SYSTEM] System structural integrity restored. "
                    "Reboot recommended."
                )
                sys.exit(0)

            elif outcome == "proposed":
                self._update_db_status(
                    err_id, "PROPOSED",
                    f"Patch proposed (not applied): {artifact}"
                )
                print(
                    "[IMMUNE-SYSTEM] SAFE MODE complete. "
                    "Manual review required; source unchanged."
                )
                sys.exit(1)

            else:
                if self._auto_apply_enabled() and artifact:
                    print("[IMMUNE-SYSTEM] Reverting to backup...")
                    shutil.copy2(artifact, target_file)

        print("[IMMUNE-SYSTEM] All 3 healing attempts failed. KILL SWITCH ENGAGED.")
        self._update_db_status(err_id, "FATAL", "Patch attempts exhausted")
        sys.exit(1)


def activate_immune_system():
    # Only needs to be instantiated to hook sys
    XorasImmuneSystem()
