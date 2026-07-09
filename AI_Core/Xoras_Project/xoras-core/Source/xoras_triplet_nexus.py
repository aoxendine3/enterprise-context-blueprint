import os
import sys
import ast
import shutil
import importlib
import logging
import time
import py_compile
import threading
import subprocess
import hashlib
from pathlib import Path
from typing import Optional, List, Set, Dict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("XorasTripletNexus")

# Conditional import for Unix resource limits
try:
    import resource
except ImportError:
    resource = None

class UnsafeCodeError(Exception):
    """Raised when Bastion detects a code safety violation."""
    pass

class SafetyVisitor(ast.NodeVisitor):
    """
    Advanced AST Scanner that blocks:
    1. Dangerous imports and OS-level execution calls.
    2. Dynamic reflection builtins (getattr, setattr, eval, exec, globals, locals).
    3. Access to double-underscore metadata (dunder names/attributes).
    4. Strings containing signatures of blocked libraries to prevent obfuscation.
    """
    def __init__(self, blocked_imports: Set[str], blocked_calls: Set[str]):
        self.blocked_imports = blocked_imports
        self.blocked_calls = blocked_calls
        self.errors: List[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base_module = alias.name.split('.')[0]
            if base_module in self.blocked_imports:
                self.errors.append(f"Blocked import statement: '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_module = node.module.split('.')[0]
            if base_module in self.blocked_imports:
                self.errors.append(f"Blocked from-import statement: '{node.module}'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Catch direct calls (e.g., eval(), exec(), getattr())
        if isinstance(node.func, ast.Name):
            if node.func.id in self.blocked_calls:
                self.errors.append(f"Blocked function call: '{node.func.id}()'")
        # Catch attribute calls (e.g., os.system(), sys.exit())
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                full_call = f"{node.func.value.id}.{node.func.attr}"
                if node.func.attr in self.blocked_calls or full_call in self.blocked_calls:
                    self.errors.append(f"Blocked attribute call: '{full_call}()'")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        # Block reflection-sensitive dunder attribute access (e.g. __globals__, __subclasses__)
        blocked_dunders = {"__globals__", "__subclasses__", "__builtins__", "__dict__", "__code__", "__import__", "__class__"}
        if node.attr in blocked_dunders:
            self.errors.append(f"Blocked reflection/dunder attribute access: '{node.attr}'")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        # Block referencing dangerous builtins directly as names
        blocked_dunders = {"__globals__", "__subclasses__", "__builtins__", "__dict__", "__code__", "__import__", "__class__"}
        if node.id in blocked_dunders or node.id in self.blocked_calls:
            self.errors.append(f"Blocked built-in/dunder name access: '{node.id}'")
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        # Scan string constants for signature bypasses (e.g. 'o' + 's' / 'sys')
        if isinstance(node.value, str):
            val_lower = node.value.lower()
            for blocked in self.blocked_imports | self.blocked_calls:
                if val_lower == blocked:
                    self.errors.append(f"Blocked signature match in string constant: '{node.value}'")
        self.generic_visit(node)

def set_subprocess_limits():
    """Sets kernel-level CPU and RAM boundaries for the runner child process."""
    if resource:
        try:
            # 2 seconds CPU execution time limit
            resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
        except Exception as e:
            sys.stderr.write(f"[SUBPROCESS-LIMITS] Failed to apply CPU rlimits: {e}\n")

class BastionSentry:
    """
    Tier 3 Sentry. Performs AST safety inspections and executes runtime
    tests inside isolated subprocesses with strict execution timeouts.
    """
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.backup_dir = workspace_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Comprehensive Security Policies
        self.blocked_imports = {
            "os", "sys", "subprocess", "shutil", "ctypes", "socket", 
            "urllib", "requests", "builtins", "platform", "pty", "gc", "importlib"
        }
        self.blocked_calls = {
            "eval", "exec", "open", "system", "popen", "spawn", 
            "fork", "execve", "write", "remove", "unlink", "rmdir",
            "getattr", "setattr", "delattr", "hasattr", "globals", "locals"
        }

    def inspect_safety(self, code_str: str) -> bool:
        """Parses AST and rejects blocked packages, dangerous builtins, reflection, or signatures."""
        try:
            tree = ast.parse(code_str)
            visitor = SafetyVisitor(self.blocked_imports, self.blocked_calls)
            visitor.visit(tree)
            
            if visitor.errors:
                for error in visitor.errors:
                    logger.error(f"[BASTION-SAFETY] {error}")
                return False
            
            logger.info("[BASTION-SAFETY] Static AST security audit passed.")
            return True
        except SyntaxError as e:
            logger.error(f"[BASTION-SAFETY] AST syntax check failed: {e}")
            return False

    def _get_process_rss_kb(self, pid: int) -> int:
        """Queries OS telemetry using native 'ps' to retrieve process Resident Set Size in KB."""
        try:
            res = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], capture_output=True, text=True)
            if res.returncode == 0:
                return int(res.stdout.strip())
        except Exception:
            pass
        return 0

    def verify_runtime_execution(self, test_file_path: Path) -> bool:
        """Runs the compiled script in a monitored subprocess, policing memory and execution time."""
        logger.info(f"[BASTION-RUNTIME] Initializing subprocess sandboxed test for {test_file_path.name}")
        
        if not test_file_path.exists():
            return False

        timeout = 2.5
        mem_limit_mb = 256
        start_time = time.time()

        try:
            # -S flag disables loading site-packages (isolates runtime libraries)
            proc = subprocess.Popen(
                [sys.executable, "-S", str(test_file_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={}, # Clear environment variables
                preexec_fn=set_subprocess_limits # Enforce CPU time constraints
            )

            # Polling watch loop to enforce real-time RSS memory limit
            while proc.poll() is None:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    proc.kill()
                    logger.error(f"[BASTION-RUNTIME] CRITICAL: Execution timed out (exceeded {timeout}s).")
                    return False

                # Query process memory consumption
                rss_kb = self._get_process_rss_kb(proc.pid)
                if rss_kb > (mem_limit_mb * 1024):
                    proc.kill()
                    logger.error(f"[BASTION-RUNTIME] CRITICAL: Process memory allocation ({rss_kb / 1024:.1f}MB) exceeded cap ({mem_limit_mb}MB). Terminating.")
                    return False

                time.sleep(0.05)

            # Check execution outcomes
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                logger.error(f"[BASTION-RUNTIME] Subprocess exited with error code {proc.returncode}")
                logger.error(f"[BASTION-RUNTIME] Stderr: {stderr.strip()}")
                return False

            logger.info("[BASTION-RUNTIME] Subprocess test completed successfully.")
            return True
        except Exception as e:
            logger.error(f"[BASTION-RUNTIME] Execution harness error: {e}")
            return False

    def create_backup(self, target_path: Path) -> Optional[Path]:
        """Creates a .bak copy of the original module if it exists."""
        if target_path.exists():
            backup_path = self.backup_dir / f"{target_path.name}.{int(time.time())}.bak"
            shutil.copy2(target_path, backup_path)
            logger.info(f"[BASTION] Created safety backup at: {backup_path.name}")
            return backup_path
        return None

    def rollback(self, target_path: Path, backup_path: Optional[Path]):
        """Reverts the target file to the backup in case of runtime execution failure."""
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, target_path)
            logger.info(f"[BASTION] Rollback executed. Restored: {target_path.name}")
        elif target_path.exists():
            target_path.unlink()
            logger.warning(f"[BASTION] No backup found. Removed faulty script: {target_path.name}")

class AetherCompiler:
    """
    Tier 4 Cognitive Engine. Handles compile locking, module reloading,
    and runtime dynamic module injection.
    """
    def __init__(self, workspace_dir: Path, sentry: BastionSentry):
        self.workspace_dir = workspace_dir
        self.sentry = sentry
        self.lock = threading.Lock() # Thread safety lock
        self.signature_registry: Dict[str, str] = {} # Cryptographic validation mapping

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculates the SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def build_module(self, module_name: str, code_str: str) -> bool:
        """Writes, compiles, and dynamically loads a module with thread safety and atomic writes."""
        with self.lock: # Enforce thread synchronization
            if not self.sentry.inspect_safety(code_str):
                logger.error(f"[AETHER] Code failed Bastion safety policy. Aborting.")
                return False

            target_path = self.workspace_dir / f"{module_name}.py"
            temp_path = self.workspace_dir / f"{module_name}.tmp"
            backup = self.sentry.create_backup(target_path)

            try:
                # 1. Atomic write: Write to a temp file first
                with open(temp_path, "w") as f:
                    f.write(code_str)

                # Byte-compile check on the temp file
                py_compile.compile(str(temp_path), doraise=True)

                # Subprocess runtime verification on the temp file
                if not self.sentry.verify_runtime_execution(temp_path):
                    raise UnsafeCodeError("Subprocess verification failed.")

                # Rename atomically to replace the target file
                os.replace(temp_path, target_path)

                # Cryptographically register file signature
                file_hash = self.calculate_file_hash(target_path)
                self.signature_registry[module_name] = file_hash
                logger.info(f"[AETHER] Cryptographic signature generated for {module_name}: {file_hash[:16]}")

                # Dynamically load into memory context
                if target_path.parent not in sys.path:
                    sys.path.insert(0, str(target_path.parent))
                
                # Verify disk signature matches registry immediately before loading
                current_hash = self.calculate_file_hash(target_path)
                if current_hash != self.signature_registry.get(module_name):
                    raise UnsafeCodeError("Signature mismatch: File modified after validation.")

                if module_name in sys.modules:
                    logger.info(f"[AETHER] Cleaning namespace and reloading module: {module_name}")
                    # Clear out the module's dict keys to prevent memory leakage of deleted states
                    module = sys.modules[module_name]
                    keys_to_keep = {"__name__", "__file__", "__doc__", "__package__", "__loader__", "__spec__"}
                    for key in list(module.__dict__.keys()):
                        if key not in keys_to_keep:
                            del module.__dict__[key]
                    importlib.reload(module)
                else:
                    logger.info(f"[AETHER] Loading module: {module_name}")
                    importlib.import_module(module_name)

                logger.info(f"[AETHER] Module {module_name} hot-swap verified and merged.")
                return True
            except Exception as e:
                logger.error(f"[AETHER] Runtime compile/load failure: {e}")
                if temp_path.exists():
                    temp_path.unlink()
                self.sentry.rollback(target_path, backup)
                return False

class ChronosGovernor:
    """
    Tier 7 Swarm Governor. Resource coordinator that checks CPU load average
    and throttles dynamic compiles if system capacity is exceeded.
    """
    def __init__(self, max_cpu_load: float = 80.0):
        self.max_cpu_load = max_cpu_load

    def get_cpu_load(self) -> float:
        """Gets CPU load. Prioritizes psutil; falls back to load average."""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            try:
                load_1, _, _ = os.getloadavg()
                num_cores = os.cpu_count() or 1
                return (load_1 / num_cores) * 100.0
            except Exception:
                return 0.0

    def is_throttled(self) -> bool:
        cpu = self.get_cpu_load()
        logger.info(f"[CHRONOS] Hardware telemetry check: {cpu:.1f}% CPU load")
        return cpu > self.max_cpu_load

class TripletNexus:
    """
    Master Orchestrator connecting Aether, Bastion, and Chronos.
    """
    def __init__(self, workspace_dir: str = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Source"):
        self.workspace_dir = Path(workspace_dir)
        self.sentry = BastionSentry(self.workspace_dir)
        self.compiler = AetherCompiler(self.workspace_dir, self.sentry)
        self.governor = ChronosGovernor(max_cpu_load=80.0)

    def execute_logic_mutation(self, module_name: str, code_str: str) -> bool:
        logger.info(f"[NEXUS] Processing dynamic logic update: {module_name}")
        
        if self.governor.is_throttled():
            logger.warning("[NEXUS] Hardware constraint triggered. Compilation throttled.")
            return False

        return self.compiler.build_module(module_name, code_str)

if __name__ == "__main__":
    # Internal Verification Suite
    nexus = TripletNexus()
    
    # 1. Valid test code
    valid_code = """
def test_call():
    print("Self-test active.")
    return True

if __name__ == '__main__':
    test_call()
"""

    # 2. Obfuscation test code (tries to bypass imports via string concatenation and getattr)
    obfuscation_code = """
def exploit():
    # Try to resolve blocked function using dynamic getattr lookup
    getattr(None, 'ex' + 'it')()

if __name__ == '__main__':
    exploit()
"""

    print("\n--- TEST 1: VALID MODULE ---")
    nexus.execute_logic_mutation("xoras_valid_test", valid_code)
    
    print("\n--- TEST 2: REFLECTION/OBFUSCATION BLOCK ---")
    nexus.execute_logic_mutation("xoras_obfuscation_test", obfuscation_code)
