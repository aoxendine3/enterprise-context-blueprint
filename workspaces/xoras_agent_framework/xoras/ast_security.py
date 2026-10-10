"""
XORAS Systems LLC — AST Security Engine & Secret Scanner
Performs strict Abstract Syntax Tree (AST) static analysis and entropy secret detection.
"""

import ast
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ASTScanResult:
    is_safe: bool
    violations: List[str] = field(default_factory=list)
    secrets_detected: List[str] = field(default_factory=list)
    safety_score: float = 1.0
    nodes_analyzed: int = 0

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
        }
        
        # Unsafe module imports
        self.dangerous_modules = {
            "ctypes": "Raw memory manipulation via ctypes is restricted.",
            "pty": "Pseudo-terminal creation via pty is prohibited.",
            "code": "Interactive interpreter via code module is restricted."
        }

    def visit(self, node):
        self.nodes_analyzed += 1
        super().visit(node)

    def visit_Call(self, node):
        # Inspect function call names
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            
        if func_name in self.forbidden_calls:
            self.violations.append(f"Line {getattr(node, 'lineno', '?')}: {self.forbidden_calls[func_name]}")
            
        # Check os.system / subprocess.Popen with unsafe args
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            module_name = node.func.value.id
            if module_name == "os" and func_name in ("system", "popen", "execv", "execl"):
                # Inspect string argument if available
                if node.args and isinstance(node.args[0], ast.Constant):
                    arg_val = str(node.args[0].value)
                    if "rm -rf" in arg_val or "sudo " in arg_val or "> /dev/" in arg_val:
                        self.violations.append(f"Line {getattr(node, 'lineno', '?')}: High-risk shell command in os.{func_name}: '{arg_val}'")
            elif module_name == "subprocess" and func_name in ("Popen", "call", "run"):
                # Check shell=True kwargs
                for keyword in node.keywords:
                    if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                        self.violations.append(f"Line {getattr(node, 'lineno', '?')}: Subprocess invocation with shell=True is restricted under XORAS AST policy.")

        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in self.dangerous_modules:
                self.violations.append(f"Line {getattr(node, 'lineno', '?')}: {self.dangerous_modules[alias.name]}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module in self.dangerous_modules:
            self.violations.append(f"Line {getattr(node, 'lineno', '?')}: {self.dangerous_modules[node.module]}")
        self.generic_visit(node)


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
        """Parses python AST syntax tree and runs regex secret scanning."""
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
            visitor.visit(tree)
            violations.extend(visitor.violations)
            nodes_analyzed = visitor.nodes_analyzed
        except SyntaxError as e:
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
