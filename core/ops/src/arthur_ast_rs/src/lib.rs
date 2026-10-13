use std::collections::{HashMap, HashSet};
use tree_sitter::{Node, Parser};

pub const TAINT_EXTERNAL: &str = "__TAINT_EXTERNAL_POISON__";
pub const TAINT_SANITIZED: &str = "__TAINT_SANITIZED_ANTIDOTE__";

#[derive(Debug, Clone, PartialEq)]
pub enum TaintStatus {
    ExternalPoison,
    SanitizedAntidote,
    Literal(String),
    Unknown,
}

pub struct ArthurAstEngine {
    banned_targets: HashSet<&'static str>,
    banned_modules: HashSet<&'static str>,
    taint_sources: HashSet<&'static str>,
    antidote_casters: HashSet<&'static str>,
}

impl Default for ArthurAstEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl ArthurAstEngine {
    pub fn new() -> Self {
        let mut banned_targets = HashSet::new();
        for t in &[
            "eval", "exec", "compile", "__import__",
            "system", "popen", "execv", "execl", "spawn", "fork", "kill",
        ] {
            banned_targets.insert(*t);
        }

        let mut banned_modules = HashSet::new();
        for m in &["ctypes", "pty"] {
            banned_modules.insert(*m);
        }

        let mut taint_sources = HashSet::new();
        for s in &[
            "getenv", "read", "read_text", "read_bytes", "readline", "readlines",
            "recv", "recvfrom", "input",
        ] {
            taint_sources.insert(*s);
        }

        let mut antidote_casters = HashSet::new();
        for c in &["int", "float", "bool", "len", "ord"] {
            antidote_casters.insert(*c);
        }

        Self {
            banned_targets,
            banned_modules,
            taint_sources,
            antidote_casters,
        }
    }

    pub fn scan_source(&self, source_code: &str) -> Result<Vec<String>, String> {
        let mut parser = Parser::new();
        let language = tree_sitter_python::LANGUAGE;
        parser
            .set_language(&language.into())
            .map_err(|e| format!("Failed to set Python language: {}", e))?;

        let tree = parser
            .parse(source_code, None)
            .ok_or_else(|| "Failed to parse Python source".to_string())?;

        let root_node = tree.root_node();
        let mut violations = Vec::new();
        let mut env: HashMap<String, TaintStatus> = HashMap::new();
        let mut sanitized_vars: HashSet<String> = HashSet::new();

        // Pass 0: Discover Antidote Whitelist Guards (`if x in ALLOWED:`)
        self.collect_whitelist_guards(root_node, source_code.as_bytes(), &mut sanitized_vars);

        // Pass 1: Semantic AST Traversal with Taint & Antidote Evaluation
        self.walk_and_verify(
            root_node,
            source_code.as_bytes(),
            &mut env,
            &sanitized_vars,
            &mut violations,
        );

        Ok(violations)
    }

    fn collect_whitelist_guards(
        &self,
        node: Node,
        source: &[u8],
        sanitized_vars: &mut HashSet<String>,
    ) {
        if node.kind() == "if_statement" {
            // Find condition node
            if let Some(condition) = node.child_by_field_name("condition") {
                if condition.kind() == "comparison_operator" {
                    // Check for: variable "in" list/tuple/set
                    let mut has_in = false;
                    let mut left_var: Option<String> = None;
                    let mut cursor = condition.walk();
                    for child in condition.children(&mut cursor) {
                        let text = child.utf8_text(source).unwrap_or("");
                        if text == "in" {
                            has_in = true;
                        } else if child.kind() == "identifier" && left_var.is_none() {
                            left_var = Some(text.to_string());
                        }
                    }
                    if has_in {
                        if let Some(var_name) = left_var {
                            sanitized_vars.insert(var_name);
                        }
                    }
                }
            }
        }

        let mut cursor = node.walk();
        for child in node.children(&mut cursor) {
            self.collect_whitelist_guards(child, source, sanitized_vars);
        }
    }

    fn eval_expression(
        &self,
        node: Node,
        source: &[u8],
        env: &HashMap<String, TaintStatus>,
        sanitized_vars: &HashSet<String>,
    ) -> TaintStatus {
        match node.kind() {
            "identifier" => {
                let name = node.utf8_text(source).unwrap_or("");
                if sanitized_vars.contains(name) {
                    return TaintStatus::SanitizedAntidote;
                }
                if let Some(status) = env.get(name) {
                    return status.clone();
                }
                TaintStatus::Unknown
            }
            "string" => {
                let text = node.utf8_text(source).unwrap_or("");
                let stripped = text.trim_matches(|c| c == '"' || c == '\'');
                TaintStatus::Literal(stripped.to_string())
            }
            "integer" | "float" | "true" | "false" => TaintStatus::SanitizedAntidote,
            "call" => {
                let func_node = match node.child_by_field_name("function") {
                    Some(f) => f,
                    None => return TaintStatus::Unknown,
                };
                let func_text = func_node.utf8_text(source).unwrap_or("");

                // 1. Antidote Casts: int(x), float(x)
                if self.antidote_casters.contains(func_text) {
                    return TaintStatus::SanitizedAntidote;
                }

                // 2. Direct Taint Sources: os.getenv(), open().read(), etc.
                if let Some(attr) = func_node.child_by_field_name("attribute") {
                    let attr_name = attr.utf8_text(source).unwrap_or("");
                    if self.taint_sources.contains(attr_name) {
                        return TaintStatus::ExternalPoison;
                    }
                } else if self.taint_sources.contains(func_text) {
                    return TaintStatus::ExternalPoison;
                }

                // 3. String concatenation via format/join
                TaintStatus::Unknown
            }
            "subscript" => {
                let val_text = node
                    .child_by_field_name("value")
                    .and_then(|v| v.utf8_text(source).ok())
                    .unwrap_or("");
                if val_text == "os.environ" || val_text == "sys.argv" || val_text == "environ" {
                    return TaintStatus::ExternalPoison;
                }
                TaintStatus::Unknown
            }
            "binary_operator" => {
                let left = node
                    .child_by_field_name("left")
                    .map(|n| self.eval_expression(n, source, env, sanitized_vars));
                let right = node
                    .child_by_field_name("right")
                    .map(|n| self.eval_expression(n, source, env, sanitized_vars));

                if left == Some(TaintStatus::ExternalPoison) || right == Some(TaintStatus::ExternalPoison) {
                    return TaintStatus::ExternalPoison;
                }
                if let (Some(TaintStatus::Literal(l)), Some(TaintStatus::Literal(r))) = (left, right) {
                    return TaintStatus::Literal(format!("{}{}", l, r));
                }
                TaintStatus::Unknown
            }
            _ => TaintStatus::Unknown,
        }
    }

    fn walk_and_verify(
        &self,
        node: Node,
        source: &[u8],
        env: &mut HashMap<String, TaintStatus>,
        sanitized_vars: &HashSet<String>,
        violations: &mut Vec<String>,
    ) {
        let line = node.start_position().row + 1;

        match node.kind() {
            "assignment" => {
                let left = node.child_by_field_name("left");
                let right = node.child_by_field_name("right");
                if let (Some(l), Some(r)) = (left, right) {
                    if l.kind() == "identifier" {
                        let var_name = l.utf8_text(source).unwrap_or("").to_string();
                        let status = self.eval_expression(r, source, env, sanitized_vars);
                        env.insert(var_name, status);
                    }
                }
            }
            "call" => {
                if let Some(func_node) = node.child_by_field_name("function") {
                    let func_name = func_node.utf8_text(source).unwrap_or("");

                    // Rule 1: Direct Insecure Syscalls: eval(), exec(), compile()
                    if self.banned_targets.contains(func_name) {
                        violations.push(format!("DIRECT_INSECURE_CALL: {}() at line {}", func_name, line));
                    }

                    // Rule 2: Qualified Calls: os.system(), os.popen()
                    if func_node.kind() == "attribute" {
                        if let Some(attr) = func_node.child_by_field_name("attribute") {
                            let attr_name = attr.utf8_text(source).unwrap_or("");
                            if self.banned_targets.contains(attr_name) {
                                // Check if argument is poisoned
                                let arg0_status = node
                                    .child_by_field_name("arguments")
                                    .and_then(|args| args.named_child(0))
                                    .map(|arg| self.eval_expression(arg, source, env, sanitized_vars));

                                if arg0_status == Some(TaintStatus::ExternalPoison) {
                                    violations.push(format!(
                                        "TAINTED_SYSCALL_EXECUTION: os.{}(TAINT_EXTERNAL) at line {}",
                                        attr_name, line
                                    ));
                                } else {
                                    violations.push(format!(
                                        "QUALIFIED_INSECURE_CALL: .{}() at line {}",
                                        attr_name, line
                                    ));
                                }
                            }
                        }
                    }

                    // Rule 3: Reflection Sink: getattr(obj, target)
                    if func_name == "getattr" || func_name == "hasattr" {
                        if let Some(args) = node.child_by_field_name("arguments") {
                            if let Some(second_arg) = args.named_child(1) {
                                let status = self.eval_expression(second_arg, source, env, sanitized_vars);
                                match status {
                                    TaintStatus::ExternalPoison => {
                                        violations.push(format!(
                                            "TAINTED_GETATTR_REFLECTION: getattr() target derived from external state at line {}",
                                            line
                                        ));
                                    }
                                    TaintStatus::Literal(lit) => {
                                        if self.banned_targets.contains(lit.as_str()) {
                                            violations.push(format!(
                                                "MULTI_STAGE_GETATTR_INDIRECTION: getattr(..., '{}') at line {}",
                                                lit, line
                                            ));
                                        }
                                    }
                                    TaintStatus::SanitizedAntidote => {
                                        // Whitelist neutralized taint: admitted without alert!
                                    }
                                    TaintStatus::Unknown => {}
                                }
                            }
                        }
                    }

                    // Rule 4: Dynamic Import Injection: importlib.import_module()
                    if func_name.ends_with("import_module") {
                        if let Some(args) = node.child_by_field_name("arguments") {
                            if let Some(first_arg) = args.named_child(0) {
                                let status = self.eval_expression(first_arg, source, env, sanitized_vars);
                                match status {
                                    TaintStatus::ExternalPoison => {
                                        violations.push(format!(
                                            "TAINTED_IMPORTLIB_INJECTION: importlib.import_module() with external runtime input at line {}",
                                            line
                                        ));
                                    }
                                    TaintStatus::SanitizedAntidote => {}
                                    _ => {
                                        violations.push(format!(
                                            "DYNAMIC_IMPORTLIB_INJECTION: dynamic import at line {}",
                                            line
                                        ));
                                    }
                                }
                            }
                        }
                    }
                }
            }
            "import_statement" | "import_from_statement" => {
                let text = node.utf8_text(source).unwrap_or("");
                for m in &self.banned_modules {
                    if text.contains(m) {
                        violations.push(format!(
                            "RESTRICTED_MODULE_IMPORT: import '{}' restricted under NIST SP 800-218 at line {}",
                            m, line
                        ));
                    }
                }
            }
            _ => {}
        }

        let mut cursor = node.walk();
        for child in node.children(&mut cursor) {
            self.walk_and_verify(child, source, env, sanitized_vars, violations);
        }
    }
}
