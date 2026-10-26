"""
XORAS Systems LLC — AST Security Engine & Secret Scanner
Performs strict Abstract Syntax Tree (AST) static analysis and entropy secret detection.

HONESTY NOTE — THIS IS A TRIPWIRE, NOT A SANDBOX
------------------------------------------------
A Python AST denylist is a best-effort *tripwire*. It catches common, careless, and
moderately obfuscated hostile code (direct/aliased eval/exec, dunder-walks, dangerous
imports, secret-path reads, network exfiltration helpers), but it can ALWAYS be bypassed by
a determined attacker (e.g. strings assembled at runtime with chr()/base64, dynamic
``getattr`` names, resource-exhaustion loops, abuse of allow-listed stdlib modules).
It must never be the only control around untrusted code. Real isolation requires
OS-level sandboxing (separate unprivileged process/container, seccomp/sandbox-exec,
no network namespace, read-only filesystem, CPU/memory/time limits).
Known unclosed bypass classes are recorded as strict-xfail tests in
``tests/test_ast_hardening_real.py``.
"""

import ast
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple


@dataclass
class ASTScanResult:
    is_safe: bool
    violations: List[str] = field(default_factory=list)
    secrets_detected: List[str] = field(default_factory=list)
    safety_score: float = 1.0
    nodes_analyzed: int = 0


# Dunder / frame attributes that expose interpreter internals (sandbox-escape primitives).
_DANGEROUS_ATTRS: Dict[str, str] = {
    "__bases__": "class hierarchy walk",
    "__base__": "class hierarchy walk",
    "__mro__": "class hierarchy walk",
    "__subclasses__": "subclass enumeration",
    "__globals__": "function globals access",
    "__builtins__": "builtins namespace access",
    "__code__": "code object access",
    "__closure__": "closure cell access",
    "__getattribute__": "raw attribute-access bypass",
    "__reduce__": "pickle-style reduce hook",
    "__reduce_ex__": "pickle-style reduce hook",
    "__loader__": "import loader access",
    "f_globals": "frame globals access",
    "f_builtins": "frame builtins access",
    "f_back": "frame stack walk",
    "gi_frame": "generator frame access",
    "gi_code": "generator code access",
    "cr_frame": "coroutine frame access",
    "ag_frame": "async-generator frame access",
    "tb_frame": "traceback frame access",
    "_getframe": "frame stack walk",
}

# Attribute names that are suspicious when fetched by (constant-foldable) getattr()/setattr().
_GETATTR_SUSPICIOUS: Set[str] = set(_DANGEROUS_ATTRS) | {
    "__class__", "__dict__", "__import__", "__init__", "system", "popen", "eval", "exec",
    "import_module", "Popen", "check_output", "check_call", "execv", "execl", "modules",
}

# Module attributes that betray a leaked internal import (e.g. ``glob.os.system``).
_LEAKY_MODULE_ATTRS: Set[str] = {"os", "subprocess", "builtins", "importlib", "ctypes", "posix", "nt", "_os"}

# Roots of denylisted modules (dotted prefix -> reason).
_DENY_MODULES: Dict[str, str] = {
    "ctypes": "Raw memory manipulation via ctypes is restricted.",
    "pty": "Pseudo-terminal creation via pty is prohibited.",
    "code": "Interactive interpreter via code module is restricted.",
    "codeop": "Interactive interpreter via codeop module is restricted.",
    "os": "Operating-system access via os module is restricted.",
    "posix": "Operating-system access via posix module is restricted.",
    "nt": "Operating-system access via nt module is restricted.",
    "subprocess": "Process spawning via subprocess is restricted.",
    "_posixsubprocess": "Process spawning via _posixsubprocess is restricted.",
    "multiprocessing": "Process spawning via multiprocessing is restricted.",
    "socket": "Raw network access via socket is restricted.",
    "socketserver": "Network servers via socketserver are restricted.",
    "pickle": "Unsafe deserialization via pickle is prohibited.",
    "_pickle": "Unsafe deserialization via _pickle is prohibited.",
    "cPickle": "Unsafe deserialization via cPickle is prohibited.",
    "cloudpickle": "Unsafe deserialization via cloudpickle is prohibited.",
    "dill": "Unsafe deserialization via dill is prohibited.",
    "shelve": "Unsafe deserialization via shelve (pickle-backed) is prohibited.",
    "marshal": "Unsafe deserialization via marshal is prohibited.",
    "importlib": "Dynamic import machinery via importlib is prohibited.",
    "imp": "Dynamic import machinery via imp is prohibited.",
    "runpy": "Dynamic code execution via runpy is prohibited.",
    "builtins": "Direct builtins module access is prohibited.",
    "gc": "Object-graph introspection via gc is prohibited.",
    "pdb": "Debugger access via pdb is prohibited.",
    "bdb": "Debugger access via bdb is prohibited.",
    "webbrowser": "Launching external programs via webbrowser is prohibited.",
    "urllib": "Network access via urllib is restricted.",
    "http": "Network access via http is restricted.",
    "requests": "Network access via requests is restricted.",
    "httpx": "Network access via httpx is restricted.",
    "aiohttp": "Network access via aiohttp is restricted.",
    "urllib3": "Network access via urllib3 is restricted.",
    "ftplib": "Network access via ftplib is restricted.",
    "smtplib": "Network access via smtplib is restricted.",
    "poplib": "Network access via poplib is restricted.",
    "imaplib": "Network access via imaplib is restricted.",
    "telnetlib": "Network access via telnetlib is restricted.",
    "xmlrpc": "Network access via xmlrpc is restricted.",
    "paramiko": "Remote shell access via paramiko is restricted.",
    "pexpect": "Process spawning via pexpect is restricted.",
}

# Dotted prefixes that are explicitly benign and exempt from the deny list above.
_ALLOW_MODULES: Set[str] = {
    "os.path",
    "urllib.parse",
    "urllib.error",
    "http.HTTPStatus",
    "http.HTTPMethod",
}

# Secret-bearing filesystem locations (matched against constant-folded string values).
_SECRET_PATH_PATTERNS: List[Tuple[str, str]] = [
    (r"(^|[/\\])\.ssh([/\\]|$)", ".ssh directory"),
    (r"id_(rsa|dsa|ecdsa|ed25519)", "SSH private key file"),
    (r"(^|[/\\])\.env(\.[\w.-]+)?$", ".env secrets file"),
    (r"/etc/(passwd|shadow|sudoers)", "system credential file"),
    (r"(^|[/\\])\.aws([/\\]|$)", "AWS credentials directory"),
    (r"(^|[/\\])\.gnupg([/\\]|$)", "GnuPG keyring directory"),
    (r"(^|[/\\])\.(netrc|npmrc|pypirc|git-credentials)$", "credential dotfile"),
    (r"(^|[/\\])\.kube([/\\]|$)", "Kubernetes credentials directory"),
    (r"(^|[/\\])\.docker[/\\]config", "Docker credentials"),
    (r"Library[/\\]Keychains", "macOS keychain"),
]

# Calls whose arguments are filesystem paths (checked against the secret-path patterns).
_PATH_FUNCS: Set[str] = {
    "open", "Path", "PurePath", "PosixPath", "PurePosixPath", "WindowsPath", "joinpath",
    "expanduser", "join", "listdir", "scandir", "walk", "glob", "rglob", "iglob", "read_text",
    "read_bytes", "write_text", "write_bytes", "copy", "copy2", "copyfile", "copytree", "move",
    "remove", "unlink", "rename", "stat", "exists", "is_file", "with_name", "load",
}

_FORMAT_DUNDER_RE = re.compile(r"\{[^{}]*(\.|\[)__\w+__")


class ASTSecurityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.violations: List[str] = []
        self.nodes_analyzed: int = 0

        # Unsafe call names
        self.forbidden_calls = {
            "eval": "Dynamic evaluation via eval() is strictly prohibited by XORAS AST Guardrails.",
            "exec": "Dynamic execution via exec() is strictly prohibited by XORAS AST Guardrails.",
            "compile": "Dynamic compilation via compile() is prohibited in agent runtime.",
            "__import__": "Dynamic import via __import__ is prohibited.",
            "breakpoint": "Debugger entry via breakpoint() is prohibited.",
            "globals": "Namespace introspection via globals() is prohibited.",
        }

        # Unsafe module imports (kept as a public attribute for backward compatibility)
        self.dangerous_modules = dict(_DENY_MODULES)

        self._aliases: Dict[str, str] = {}       # local name -> canonical dotted name
        self._consts: Dict[str, str] = {}        # local name -> constant string value
        self._handled: Set[int] = set()          # node ids already reported / subsumed
        self._seen: Set[Tuple[int, str]] = set()  # (lineno, message) dedupe

    # ---------------------------------------------------------------- helpers
    def _report(self, node, message: str) -> None:
        line = getattr(node, "lineno", "?")
        key = (line if isinstance(line, int) else -1, message)
        if key in self._seen:
            return
        self._seen.add(key)
        self.violations.append(f"Line {line}: {message}")

    def _fold(self, node) -> Optional[str]:
        """Constant-fold simple string expressions ('ex'+'ec', ''.join([...]), f'..', names bound to str)."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return node.value
            if isinstance(node.value, bytes):
                try:
                    return node.value.decode("utf-8", "replace")
                except Exception:
                    return None
            return None
        if isinstance(node, ast.Name):
            return self._consts.get(node.id)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Div)):
            left, right = self._fold(node.left), self._fold(node.right)
            if left is not None and right is not None:
                return left + ("/" if isinstance(node.op, ast.Div) else "") + right
            return None
        if isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                s = self._fold(v)
                if s is None:
                    return None
                parts.append(s)
            return "".join(parts)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "join"
            and len(node.args) == 1
            and isinstance(node.args[0], (ast.List, ast.Tuple))
        ):
            sep = self._fold(node.func.value)
            items = [self._fold(e) for e in node.args[0].elts]
            if sep is not None and all(i is not None for i in items):
                return sep.join(items)  # type: ignore[arg-type]
        return None

    def _resolve(self, node) -> Optional[str]:
        """Resolve an expression to a canonical dotted name, following simple aliases."""
        if isinstance(node, ast.Name):
            return self._aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            base = self._resolve(node.value)
            return f"{base}.{node.attr}" if base else None
        if isinstance(node, ast.Call):
            callee = self._resolve(node.func)
            if callee in ("__import__", "importlib.import_module", "builtins.__import__") and node.args:
                folded = self._fold(node.args[0])
                if folded:
                    return folded
        return None

    @staticmethod
    def _deny_reason(dotted: Optional[str], use_allow: bool = True) -> Optional[str]:
        if not dotted:
            return None
        if use_allow:
            for allowed in _ALLOW_MODULES:
                if dotted == allowed or dotted.startswith(allowed + "."):
                    return None
        parts = dotted.split(".")
        for i in range(len(parts), 0, -1):
            prefix = ".".join(parts[:i])
            if prefix in _DENY_MODULES:
                return _DENY_MODULES[prefix]
        return None

    def _forbidden_builtin(self, dotted: Optional[str]) -> Optional[str]:
        if not dotted:
            return None
        if dotted in self.forbidden_calls:
            return dotted
        if dotted.startswith("builtins.") and dotted[len("builtins."):] in self.forbidden_calls:
            return dotted[len("builtins."):]
        return None

    def _check_secret_path(self, node, value: Optional[str]) -> None:
        if not value:
            return
        for pattern, desc in _SECRET_PATH_PATTERNS:
            if re.search(pattern, value):
                self._report(node, f"Access to sensitive path ({desc}) is prohibited: '{value}'")
                return

    # ---------------------------------------------------------------- core
    def visit(self, node):
        self.nodes_analyzed += 1
        super().visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and id(node) not in self._handled:
            if node.id in ("__builtins__", "__loader__"):
                self._report(node, f"Access to {node.id} (interpreter internals) is prohibited.")
            else:
                resolved = self._aliases.get(node.id, node.id)
                name = self._forbidden_builtin(resolved)
                if name:
                    via = f" (referenced via alias '{node.id}')" if node.id != resolved else ""
                    self._report(node, f"{self.forbidden_calls[name]}{via}")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        attr = node.attr
        if attr in _DANGEROUS_ATTRS:
            self._report(node, f"Dunder/frame attribute '{attr}' ({_DANGEROUS_ATTRS[attr]}) is prohibited.")
        elif attr == "__class__" and isinstance(
            node.value, (ast.Constant, ast.Tuple, ast.List, ast.Dict, ast.Set, ast.JoinedStr)
        ):
            self._report(node, "Literal.__class__ access (object-graph walk) is prohibited.")
        elif attr == "__dict__":
            base = self._resolve(node.value)
            if base in ("__builtins__", "builtins"):
                self._report(node, "Access to builtins.__dict__ is prohibited.")
        elif attr == "modules" and self._resolve(node.value) == "sys":
            self._report(node, "Access to sys.modules is prohibited.")
        elif attr in _LEAKY_MODULE_ATTRS and not isinstance(node.value, ast.Name):
            self._report(node, f"Access to leaked internal module attribute '.{attr}' is prohibited.")

        if id(node) not in self._handled:
            dotted = self._resolve(node)
            reason = self._deny_reason(dotted)
            if reason:
                self._report(node, f"{reason} (reference: {dotted})")
                inner = node.value
                while isinstance(inner, ast.Attribute):
                    self._handled.add(id(inner))
                    inner = inner.value
            else:
                forbidden = self._forbidden_builtin(dotted) if dotted and dotted.startswith("builtins.") else None
                if forbidden:
                    self._report(node, self.forbidden_calls[forbidden])
        self.generic_visit(node)

    def visit_BinOp(self, node):
        # Path.home() / '.ssh' / 'id_rsa' style construction.
        if isinstance(node.op, ast.Div):
            for side in (node.left, node.right):
                if isinstance(side, ast.Constant) and isinstance(side.value, str):
                    self._check_secret_path(node, side.value)
            folded = self._fold(node)
            if folded:
                self._check_secret_path(node, folded)
        self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str) and _FORMAT_DUNDER_RE.search(node.value):
            self._report(node, "Format-string attribute traversal into dunder attributes is prohibited.")
        self.generic_visit(node)

    def visit_Call(self, node):
        dotted = self._resolve(node.func)
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # Direct / aliased / builtins-qualified forbidden calls.
        forbidden = self._forbidden_builtin(dotted)
        if forbidden:
            msg = self.forbidden_calls[forbidden]
            if isinstance(node.func, ast.Name) and node.func.id != forbidden:
                msg += f" (invoked via alias '{node.func.id}')"
            self._report(node, msg)
            self._handled.add(id(node.func))

        # Check os.system / subprocess.Popen with unsafe args (alias-aware)
        if dotted and "." in dotted:
            module_name, _, member = dotted.rpartition(".")
            if module_name == "os" and member in ("system", "popen", "execv", "execl"):
                if node.args and isinstance(node.args[0], ast.Constant):
                    arg_val = str(node.args[0].value)
                    if "rm -rf" in arg_val or "sudo " in arg_val or "> /dev/" in arg_val:
                        self._report(node, f"High-risk shell command in os.{member}: '{arg_val}'")
            elif module_name == "subprocess" and member in ("Popen", "call", "run"):
                for keyword in node.keywords:
                    if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                        self._report(node, "Subprocess invocation with shell=True is restricted under XORAS AST policy.")
            elif module_name == "shutil" and member in ("rmtree", "move"):
                self._report(node, f"Destructive filesystem operation shutil.{member}() is prohibited.")
            elif module_name == "asyncio" and member.startswith(("create_subprocess", "subprocess")):
                self._report(node, f"Process spawning via asyncio.{member}() is prohibited.")
            elif module_name in ("os.path",) or module_name.startswith("os.path"):
                pass
        elif dotted in ("rmtree",):
            self._report(node, "Destructive filesystem operation rmtree() is prohibited.")

        # getattr()/setattr()/delattr()/vars() reflection abuse.
        if dotted in ("getattr", "setattr", "delattr", "hasattr", "vars") and node.args:
            target = self._resolve(node.args[0])
            if target in ("__builtins__", "builtins") or self._deny_reason(target, use_allow=False):
                self._report(node, f"Reflection ({dotted}) on restricted object '{target}' is prohibited.")
            if dotted != "vars" and len(node.args) >= 2:
                name = self._fold(node.args[1])
                if name in _GETATTR_SUSPICIOUS:
                    self._report(node, f"Reflection ({dotted}) fetching sensitive attribute '{name}' is prohibited.")

        # Secret-bearing path arguments to file-ish calls.
        if func_name in _PATH_FUNCS:
            for arg in node.args:
                self._check_secret_path(node, self._fold(arg))
            for kw in node.keywords:
                self._check_secret_path(node, self._fold(kw.value))

        self.generic_visit(node)

    # ------------------------------------------------------------ imports / aliasing
    def _check_import(self, node, dotted: str, check_root_binding: bool = False) -> None:
        reason = self._deny_reason(dotted)
        if not reason and check_root_binding and "." in dotted:
            # ``import os.path`` still binds the full ``os`` module.
            reason = self._deny_reason(dotted.split(".")[0], use_allow=False)
        if reason:
            self._report(node, reason)

    def visit_Import(self, node):
        for alias in node.names:
            self._check_import(node, alias.name, check_root_binding=alias.asname is None)
            if alias.asname:
                self._aliases[alias.asname] = alias.name
            else:
                root = alias.name.split(".")[0]
                self._aliases[root] = root
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        if module and node.level == 0:
            module_reason = self._deny_reason(module)
            for alias in node.names:
                full = f"{module}.{alias.name}"
                reason = self._deny_reason(full)
                if reason is None and module_reason and alias.name == "*":
                    reason = module_reason
                if reason:
                    self._report(node, reason)
                local = alias.asname or alias.name
                if alias.name != "*":
                    self._aliases[local] = full
        self.generic_visit(node)

    def _bind(self, target, value) -> None:
        if isinstance(target, ast.Name):
            resolved = self._resolve(value)
            if resolved and resolved != target.id:
                self._aliases[target.id] = resolved
            folded = self._fold(value)
            if folded is not None:
                self._consts[target.id] = folded
        elif isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, (ast.Tuple, ast.List)):
            if len(target.elts) == len(value.elts):
                for t, v in zip(target.elts, value.elts):
                    self._bind(t, v)

    def visit_Assign(self, node):
        self.generic_visit(node)
        for target in node.targets:
            self._bind(target, node.value)

    def visit_AnnAssign(self, node):
        self.generic_visit(node)
        if node.value is not None:
            self._bind(node.target, node.value)

    def visit_NamedExpr(self, node):
        self.generic_visit(node)
        self._bind(node.target, node.value)


class ASTSecurityEngine:
    SECRET_PATTERNS = [
        (r'(?i)(?:aws_access_key_id|aws_secret_access_key|api_key|secret_key|private_key)\s*[:=]\s*["\']([^"\']{8,})["\']', "Hardcoded API / Secret Key"),
        (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID"),
        (r'sk_live_[0-9a-zA-Z]{24,}', "Stripe Live API Key"),
        (r'sk-(?:proj-)?[a-zA-Z0-9_-]{32,}', "OpenAI API Key"),
        (r'sk-ant-[a-zA-Z0-9_-]{32,}', "Anthropic API Key"),
        (r'AIzaSy[0-9a-zA-Z_-]{33}', "Google Gemini API Key"),
        (r'xox[baprs]-[0-9a-zA-Z]{10,48}', "Slack OAuth / Bot Token"),
        (r'ghp_[0-9a-zA-Z]{36}', "GitHub Personal Access Token"),
        (r'-----BEGIN\s+(?:RSA|EC|OPENSSH|PRIVATE)\s+KEY-----', "Private Cryptographic Key Block"),
    ]

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def scan_code(self, code_snippet: str) -> ASTScanResult:
        """Parses python AST syntax tree and runs regex secret scanning.

        NOTE: this is a denylist tripwire, not a sandbox. A clean result means
        "no known-bad pattern found", NOT "safe to execute". See module docstring.
        """
        violations: List[str] = []
        secrets_detected: List[str] = []

        # 1. Secret scanning across raw code
        for pattern, desc in self.SECRET_PATTERNS:
            matches = re.findall(pattern, code_snippet)
            if matches:
                secrets_detected.append(f"Secret Leak Warning: Detected {desc} pattern in code payload.")
                violations.append(f"Secret Scanner: High-entropy token matching '{desc}' found.")

        # 2. Syntax validation & AST parsing
        nodes_analyzed = 0
        try:
            tree = ast.parse(code_snippet)
            visitor = ASTSecurityVisitor()
            try:
                visitor.visit(tree)
            except RecursionError:
                visitor.violations.append("Analysis aborted: AST nesting too deep to verify (fail-closed).")
            violations.extend(visitor.violations)
            nodes_analyzed = visitor.nodes_analyzed
        except RecursionError:
            nodes_analyzed = len(code_snippet.splitlines())
            violations.append("Analysis aborted: source nesting too deep to parse (fail-closed).")
        except (SyntaxError, ValueError, MemoryError):
            # If not python syntax (e.g. bash script), fallback to regex heuristic scanner
            nodes_analyzed = len(code_snippet.splitlines())
            forbidden_heuristics = [
                (r'\beval\s*\(', "Dynamic eval() invocation"),
                (r'\bexec\s*\(', "Dynamic exec() invocation"),
                (r'rm\s+-rf\s+/', "Destructive root filesystem command 'rm -rf /'"),
                (r':\(\)\{\s*:\|:&\s*\};:', "Fork bomb pattern"),
            ]
            for pat, msg in forbidden_heuristics:
                if re.search(pat, code_snippet):
                    violations.append(f"Heuristic AST Fallback Violation: Detected forbidden pattern '{msg}'")

        is_safe = len(violations) == 0
        safety_score = max(0.0, 1.0 - (len(violations) * 0.35))

        return ASTScanResult(
            is_safe=is_safe,
            violations=violations,
            secrets_detected=secrets_detected,
            safety_score=round(safety_score, 4),
            nodes_analyzed=nodes_analyzed
        )
