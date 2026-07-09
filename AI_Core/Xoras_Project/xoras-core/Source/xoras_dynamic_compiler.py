"""
xoras_dynamic_compiler.py
Zordax Systems — AST-Audited Dynamic Runtime Class Synthesis

This engine allows the Meta Orchestrator to dynamically synthesize, security-audit,
compile, and execute specialized agent classes at runtime.

Security Constraints (Deny-by-Default):
  - Abstract Syntax Tree (AST) validation: Only whitelisted node types allowed.
  - Import Restriction: Only allow safe standard libraries (asyncio, json, time, etc.) and project db.
  - Builtins Restrictions: Block `eval`, `exec`, `open`, `compile`, etc.
  - Method Budget: Enforce <= 30 lines per function definition.
  - Execution Isolation: Executes code in isolated namespaces.
  - Heap & Memory Protection: Worker process recycling after N=100 compilations.

Author: Zordax Systems / Maxx
Standard: If you can see improvements, it is not done.
"""

from __future__ import annotations

import ast
import asyncio
import json
import logging
import multiprocessing
import sys
import time
import threading
import os
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

try:
    import psutil
except ImportError:
    psutil = None

# ─── Configuration ────────────────────────────────────────────────────────────

ALLOWED_NODE_TYPES: Set[type] = {
    ast.Module,
    ast.ClassDef,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.arguments,
    ast.arg,
    ast.Pass,
    ast.Return,
    ast.Assign,
    ast.AnnAssign,
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Constant,
    ast.Call,
    ast.Attribute,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.List,
    ast.Dict,
    ast.Tuple,
    ast.Subscript,
    ast.Slice,
    ast.FormattedValue,
    ast.JoinedStr,
    ast.expr_context,
    ast.boolop,
    ast.operator,
    ast.unaryop,
    ast.cmpop,
    ast.comprehension,
    ast.keyword,
    ast.alias,
    ast.Import,
    ast.ImportFrom,
    ast.Try,
    ast.ExceptHandler,
    ast.Expr,
    ast.Await,
    ast.AugAssign,
}

ALLOWED_IMPORTS: Set[str] = {
    "asyncio",
    "json",
    "time",
    "dataclasses",
    "typing",
    "pathlib",
    "logging",
    "uuid",
    "math",
    "random",
    "xoras_vector_db",
}

ALLOWED_BUILTINS: Set[str] = {
    "print",
    "len",
    "range",
    "str",
    "int",
    "float",
    "bool",
    "list",
    "dict",
    "set",
    "tuple",
    "enumerate",
    "zip",
    "min",
    "max",
    "sum",
    "abs",
    "round",
    "isinstance",
    "issubclass",
    "super",
    "__build_class__",
    "__import__",
}

MAX_FUNCTION_LINES = 30
RECYCLE_THRESHOLD = 100

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("XorasDynamicCompiler")


# ─── AST Security Auditor ──────────────────────────────────────────────────────

class XorasASTAuditor(ast.NodeVisitor):
    """
    AST Visitor that audits code strings before compilation.
    Enforces a strict deny-by-default security posture.
    """
    def __init__(self, code: str) -> None:
        self.code = code
        self.violations: List[str] = []

    def audit(self) -> Tuple[bool, List[str]]:
        try:
            tree = ast.parse(self.code)
            self.visit(tree)
        except SyntaxError as se:
            return False, [f"Syntax Error on line {se.lineno}: {se.msg}"]
        except Exception as e:
            return False, [f"AST Parsing failure: {str(e)}"]

        return len(self.violations) == 0, self.violations

    def visit(self, node: ast.AST) -> None:
        # 1. Verify Node Type is Whitelisted (allowing subclasses for operators/comparisons)
        if not any(issubclass(type(node), allowed_type) for allowed_type in ALLOWED_NODE_TYPES):
            self.violations.append(
                f"Line {getattr(node, 'lineno', 'unknown')}: Node type '{type(node).__name__}' is forbidden."
            )
            return

        # 2. Function name and line length audit
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines = (node.end_lineno or node.lineno) - node.lineno + 1
            if lines > MAX_FUNCTION_LINES:
                self.violations.append(
                    f"Line {node.lineno}: Function '{node.name}' exceeds maximum line budget ({lines} > {MAX_FUNCTION_LINES} lines)."
                )
            if node.name.startswith("__") and node.name.endswith("__") and node.name != "__init__":
                self.violations.append(
                    f"Line {node.lineno}: Defining double-underscore method '{node.name}' is forbidden."
                )

        # 3. Class name audit
        if isinstance(node, ast.ClassDef):
            if node.name.startswith("__") and node.name.endswith("__"):
                self.violations.append(
                    f"Line {node.lineno}: Defining double-underscore class '{node.name}' is forbidden."
                )

        super().visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            base_mod = alias.name.split(".")[0]
            if base_mod not in ALLOWED_IMPORTS:
                self.violations.append(
                    f"Line {node.lineno}: Import of module '{alias.name}' is forbidden."
                )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            base_mod = node.module.split(".")[0]
            if base_mod not in ALLOWED_IMPORTS:
                self.violations.append(
                    f"Line {node.lineno}: Import from module '{node.module}' is forbidden."
                )

    def visit_Name(self, node: ast.Name) -> None:
        if node.id == "__import__":
            self.violations.append(
                f"Line {node.lineno}: Direct access to '{node.id}' is forbidden."
            )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("__") and node.attr.endswith("__"):
            self.violations.append(
                f"Line {node.lineno}: Accessing double-underscore attributes like '{node.attr}' is forbidden."
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check builtins calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            builtins_dict = __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__
            if func_name not in ALLOWED_BUILTINS and func_name in builtins_dict:
                self.violations.append(
                    f"Line {node.lineno}: Calling builtin function '{func_name}' is forbidden."
                )
        self.generic_visit(node)


# ─── Compilation Worker Process ───────────────────────────────────────────────

class ResourceExhaustionError(Exception):
    pass

def _compiler_worker_loop(pipe_conn: multiprocessing.connection.Connection) -> None:
    """
    Subprocess execution loop. Runs in isolated process.
    Handles AST verification, class compilation, instantiation, and execution.
    Isolation limits memory fragmentation impact on host processes.
    """
    compiled_classes: Dict[str, type] = {}
    instances: Dict[str, Any] = {}
    compilation_count = 0
    active_execution = threading.Event()
    
    # ── Watcher Service (Memory & CPU Monitor) ──
    def watcher_service():
        if not psutil:
            return
        proc = psutil.Process(os.getpid())
        cpu_pinned_time = 0.0
        while True:
            time.sleep(0.01) # 10ms polling
            if not active_execution.is_set():
                cpu_pinned_time = 0.0
                continue
            
            try:
                mem_mb = proc.memory_info().rss / (1024 * 1024)
                cpu_pct = proc.cpu_percent()
                
                # OOM Defense
                if mem_mb > 500.0:
                    print(f"FATAL: Memory spike detected ({mem_mb:.2f}MB). Terminating worker.", file=sys.stderr)
                    os.kill(os.getpid(), signal.SIGKILL)
                    
                # CPU Pinning Defense (Infinite Loop)
                if cpu_pct > 95.0:
                    cpu_pinned_time += 0.01
                    if cpu_pinned_time > 1.5:
                        print("FATAL: CPU pinned at 100% for >1.5s (Infinite loop detected). Terminating worker.", file=sys.stderr)
                        os.kill(os.getpid(), signal.SIGKILL)
                else:
                    cpu_pinned_time = 0.0
            except psutil.NoSuchProcess:
                break
            except Exception:
                pass

    if psutil:
        watcher_thread = threading.Thread(target=watcher_service, daemon=True)
        watcher_thread.start()

    # Initialize localized sandbox namespace
    builtins_dict = __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__
    safe_globals = {
        "__builtins__": {b: builtins_dict[b] for b in ALLOWED_BUILTINS if b in builtins_dict},
        "__name__": "__main__",
        "__doc__": None,
        "__package__": None,
        "sys": sys,
    }
    
    # ── Asyncio Task Budgeting ──
    MAX_TASKS = 50
    active_tasks = 0
    task_lock = threading.Lock()
    
    def budgeted_create_task(coro, *args, **kwargs):
        nonlocal active_tasks
        with task_lock:
            if active_tasks >= MAX_TASKS:
                raise ResourceExhaustionError(f"Task budget exceeded. Max {MAX_TASKS} concurrent tasks allowed.")
            active_tasks += 1
            
        task = asyncio.create_task(coro, *args, **kwargs)
        
        def on_done(t):
            nonlocal active_tasks
            with task_lock:
                active_tasks = max(0, active_tasks - 1)
        task.add_done_callback(on_done)
        return task

    # Provide a restricted asyncio module
    class RestrictedAsyncio:
        pass
    r_asyncio = RestrictedAsyncio()
    for attr in dir(asyncio):
        if not attr.startswith("_"):
            setattr(r_asyncio, attr, getattr(asyncio, attr))
    r_asyncio.create_task = budgeted_create_task
    r_asyncio.ensure_future = budgeted_create_task
    safe_globals["asyncio"] = r_asyncio

    # Pre-load safe local modules into sandbox globals
    for name in ALLOWED_IMPORTS:
        if name == "asyncio":
            continue
        if name != "xoras_vector_db":
            try:
                safe_globals[name] = __import__(name)
            except ImportError:
                pass
        else:
            try:
                # Add source dir to path inside subprocess
                sys.path.insert(0, str(Path(__file__).parent))
                import xoras_vector_db
                safe_globals["xoras_vector_db"] = xoras_vector_db
            except Exception as e:
                logger.warning(f"Could not load xoras_vector_db in sandbox: {e}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        try:
            if not pipe_conn.poll(1.0):
                continue
            msg = pipe_conn.recv()
            if not isinstance(msg, dict):
                continue

            msg_type = msg.get("type")

            if msg_type == "exit":
                break

            elif msg_type == "compile":
                class_name = msg["class_name"]
                code = msg["code"]
                
                # Perform AST audit
                auditor = XorasASTAuditor(code)
                is_safe, violations = auditor.audit()
                if not is_safe:
                    pipe_conn.send({"status": "error", "message": "AST Audit Failed", "violations": violations})
                    continue

                try:
                    # Compile to bytecode
                    bytecode = compile(code, f"<dynamic_{class_name}>", "exec")
                    local_namespace: Dict[str, Any] = {}
                    exec(bytecode, safe_globals, local_namespace)

                    target_class = local_namespace.get(class_name)
                    if not target_class:
                        # Fallback: scan local namespace for any class
                        classes = [v for v in local_namespace.values() if isinstance(v, type)]
                        if classes:
                            target_class = classes[0]
                    
                    if not isinstance(target_class, type):
                        pipe_conn.send({"status": "error", "message": f"Compiled code did not define class '{class_name}'"})
                        continue

                    compiled_classes[class_name] = target_class
                    compilation_count += 1
                    pipe_conn.send({
                        "status": "success",
                        "compilation_count": compilation_count,
                        "recycled_needed": compilation_count >= RECYCLE_THRESHOLD
                    })

                except Exception as e:
                    pipe_conn.send({"status": "error", "message": f"Compilation/Namespace Load error: {str(e)}"})

            elif msg_type == "instantiate":
                class_name = msg["class_name"]
                instance_id = msg["instance_id"]
                args = msg.get("args", [])
                kwargs = msg.get("kwargs", {})

                if class_name not in compiled_classes:
                    pipe_conn.send({"status": "error", "message": f"Class '{class_name}' not compiled in this worker."})
                    continue

                try:
                    cls = compiled_classes[class_name]
                    instances[instance_id] = cls(*args, **kwargs)
                    pipe_conn.send({"status": "success"})
                except Exception as e:
                    pipe_conn.send({"status": "error", "message": f"Instantiation error: {str(e)}"})

            elif msg_type == "execute":
                instance_id = msg["instance_id"]
                method_name = msg["method"]
                args = msg.get("args", [])
                kwargs = msg.get("kwargs", {})

                if instance_id not in instances:
                    pipe_conn.send({"status": "error", "message": f"Instance '{instance_id}' not found."})
                    continue

                instance = instances[instance_id]
                method = getattr(instance, method_name, None)
                if not method:
                    pipe_conn.send({"status": "error", "message": f"Method '{method_name}' not found on instance."})
                    continue

                try:
                    active_execution.set()
                    try:
                        if asyncio.iscoroutinefunction(method):
                            # Run async method in local loop
                            result = loop.run_until_complete(method(*args, **kwargs))
                        else:
                            result = method(*args, **kwargs)
                        pipe_conn.send({"status": "success", "result": result})
                    finally:
                        active_execution.clear()
                except Exception as e:
                    pipe_conn.send({"status": "error", "message": f"Execution error: {str(e)}"})

        except Exception as ex:
            try:
                pipe_conn.send({"status": "error", "message": f"Fatal worker loop exception: {str(ex)}"})
            except Exception:
                pass


# ─── Dynamic Compiler Manager ─────────────────────────────────────────────────

class XorasDynamicCompiler:
    """
    Manages compiling dynamic agents in a recycled background worker process.
    Tracks active class definitions and handles automated recycling when N=100.
    """
    def __init__(self) -> None:
        self.active_classes: Dict[str, str] = {}  # class_name -> code
        self.active_instances: Dict[str, Tuple[str, List, Dict]] = {} # instance_id -> (class_name, args, kwargs)
        
        self.compilation_count = 0
        self.worker_proc: Optional[multiprocessing.Process] = None
        self.pipe_conn: Optional[multiprocessing.connection.Connection] = None
        self._lock = asyncio.Lock()

        # Metrics for the evolution daemon
        self.metrics_log_path = Path(__file__).parent / "compiler_metrics.json"
        self._init_worker()

    def _init_worker(self) -> None:
        """Spawn the compiler worker subprocess."""
        if self.worker_proc and self.worker_proc.is_alive():
            self._terminate_worker()

        parent_conn, child_conn = multiprocessing.Pipe()
        self.pipe_conn = parent_conn
        self.worker_proc = multiprocessing.Process(
            target=_compiler_worker_loop,
            args=(child_conn,),
            daemon=True
        )
        self.worker_proc.start()
        logger.info(f"[Compiler] Spawned new worker process [PID={self.worker_proc.pid}]")

        # Sync existing active classes to the new worker process
        for cname, code in self.active_classes.items():
            self.pipe_conn.send({"type": "compile", "class_name": cname, "code": code})
            res = self.pipe_conn.recv()
            if res.get("status") != "success":
                logger.error(f"[Compiler] Failed to restore class '{cname}' in recycled worker: {res.get('message')}")

        # Sync existing active instances
        for iid, (cname, args, kwargs) in self.active_instances.items():
            self.pipe_conn.send({
                "type": "instantiate",
                "class_name": cname,
                "instance_id": iid,
                "args": args,
                "kwargs": kwargs
            })
            res = self.pipe_conn.recv()
            if res.get("status") != "success":
                logger.error(f"[Compiler] Failed to restore instance '{iid}' in recycled worker: {res.get('message')}")

    def _terminate_worker(self) -> None:
        """Safely terminate the current worker subprocess."""
        if self.pipe_conn:
            try:
                self.pipe_conn.send({"type": "exit"})
            except Exception:
                pass
        if self.worker_proc:
            self.worker_proc.join(timeout=1.0)
            if self.worker_proc.is_alive():
                self.worker_proc.terminate()
        self.pipe_conn = None
        self.worker_proc = None

    def _record_metrics(self, compile_time_ms: float, success: bool, reason: str = "") -> None:
        """Write telemetry records to file for retrieval by Evolution Daemon."""
        record = {
            "timestamp": time.time(),
            "compile_time_ms": compile_time_ms,
            "success": success,
            "error_reason": reason,
            "total_compilations": self.compilation_count
        }
        try:
            records: List[Dict] = []
            if self.metrics_log_path.exists():
                try:
                    records = json.loads(self.metrics_log_path.read_text())
                except Exception:
                    pass
            records.append(record)
            # Keep last 500 records to prevent file bloat
            records = records[-500:]
            self.metrics_log_path.write_text(json.dumps(records, indent=2))
        except Exception as e:
            logger.error(f"Failed to record compiler metrics: {e}")

    async def compile_class(self, class_name: str, code: str) -> Tuple[bool, str]:
        """
        Submits code to worker for safety audit and runtime compilation.
        Handles automated recycling after N=100 compilations.
        """
        async with self._lock:
            start_time = time.perf_counter()
            if not self.pipe_conn:
                self._init_worker()

            # Submit compilation payload to subprocess
            self.pipe_conn.send({"type": "compile", "class_name": class_name, "code": code})
            
            # Non-blocking wait for pipe response
            poll_start = time.time()
            while not self.pipe_conn.poll(0.005):
                if time.time() - poll_start > 30.0:
                    self._terminate_worker()
                    self._init_worker()
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    self._record_metrics(elapsed_ms, False, "Compilation timed out (Infinite loop or memory crash). Worker restarted.")
                    return False, "Compilation timed out (Infinite loop or memory crash). Worker restarted."
                await asyncio.sleep(0.005)
            
            res = self.pipe_conn.recv()
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            if res.get("status") == "success":
                self.active_classes[class_name] = code
                self.compilation_count = res.get("compilation_count", 0)
                self._record_metrics(elapsed_ms, True)
                
                # Check for recycling trigger
                if res.get("recycled_needed") or self.compilation_count >= RECYCLE_THRESHOLD:
                    logger.info(f"[Compiler] Compilation count ({self.compilation_count}) reached threshold ({RECYCLE_THRESHOLD}). Recycling worker...")
                    self._init_worker()
                    self.compilation_count = 0
                
                return True, f"Compilation successful in {elapsed_ms:.2f}ms"
            else:
                violations = res.get("violations", [])
                err_msg = res.get("message", "Unknown error")
                detail = f"{err_msg}: {', '.join(violations)}" if violations else err_msg
                self._record_metrics(elapsed_ms, False, detail)
                return False, detail

    async def instantiate_agent(self, class_name: str, instance_id: str, *args, **kwargs) -> Tuple[bool, str]:
        """Spawns an instance of the compiled class inside the isolated worker namespace."""
        async with self._lock:
            if not self.pipe_conn:
                return False, "No active compiler worker"

            self.pipe_conn.send({
                "type": "instantiate",
                "class_name": class_name,
                "instance_id": instance_id,
                "args": args,
                "kwargs": kwargs
            })

            poll_start = time.time()
            while not self.pipe_conn.poll(0.005):
                if time.time() - poll_start > 30.0:
                    self._terminate_worker()
                    self._init_worker()
                    return False, "Instantiation timed out. Worker restarted."
                await asyncio.sleep(0.005)

            res = self.pipe_conn.recv()
            if res.get("status") == "success":
                self.active_instances[instance_id] = (class_name, list(args), kwargs)
                return True, f"Agent instance '{instance_id}' successfully created."
            return False, res.get("message", "Instantiation failed.")

    async def execute_agent_method(self, instance_id: str, method: str, *args, **kwargs) -> Any:
        """Executes a target method on a dynamic instance in the subprocess namespace."""
        async with self._lock:
            if not self.pipe_conn:
                raise RuntimeError("No active compiler worker")

            self.pipe_conn.send({
                "type": "execute",
                "instance_id": instance_id,
                "method": method,
                "args": args,
                "kwargs": kwargs
            })

            poll_start = time.time()
            while not self.pipe_conn.poll(0.005):
                if time.time() - poll_start > 30.0:
                    self._terminate_worker()
                    self._init_worker()
                    raise RuntimeError("Execution timed out (Infinite loop or memory crash). Worker restarted.")
                await asyncio.sleep(0.005)

            res = self.pipe_conn.recv()
            if res.get("status") == "success":
                return res.get("result")
            raise RuntimeError(f"Execution failed: {res.get('message')}")

    def cleanup(self) -> None:
        """Cleans up the compiler worker process."""
        self._terminate_worker()
        self.active_classes.clear()
        self.active_instances.clear()
