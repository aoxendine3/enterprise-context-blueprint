import os
import json
import ast

# XORAS SYSTEM: OMNI-INGESTOR
# Location: Sector 3 (Active Core)
# Purpose: Parse, extract, and compact proprietary architectures into active memory.

AUDIT_REPORT = (
    "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/"
    "Docs/omni_audit_report.md"
)
KNOWLEDGE_VAULT = (
    "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/"
    "Docs/XORAS_ACTIVE_KNOWLEDGE.json"
)


class XorasIngestor:
    def __init__(self):
        self.knowledge_graph = {
            "security_guards": [],
            "swarm_architectures": [],
            "proprietary_logic": [],
            "file_index": []
        }

    def _extract_paths_from_audit(self):
        paths = []
        if not os.path.exists(AUDIT_REPORT):
            print(f"[FATAL] Audit report not found at {AUDIT_REPORT}")
            return paths

        with open(AUDIT_REPORT, "r") as f:
            for line in f:
                if "Found: /" in line:
                    # Extract the absolute path
                    path = line.split("Found: ")[1].strip()
                    if (os.path.exists(path) and
                            not path.split("/")[-1].startswith("._")):
                        paths.append(path)
        return paths

    def _parse_python_file(self, path):
        """Uses AST to extract classes, functions, and docstrings

        without loading raw source.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)

            entities = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    entities.append({"type": "class", "name": node.name,
                                    "doc": ast.get_docstring(node)})
                elif isinstance(node, ast.FunctionDef):
                    entities.append({
                        "type": "function",
                        "name": node.name,
                        "doc": ast.get_docstring(node)
                    })

            return {
                "path": path,
                "summary": f"Contains {len(entities)} entities.",
                "entities": entities
            }
        except Exception as e:
            return {"path": path, "error": f"Failed to parse AST: {str(e)}"}

    def execute_ingestion(self):
        print("[OMNI-INGESTOR] Initializing ingestion sequence...")
        file_paths = self._extract_paths_from_audit()
        print(
            f"[OMNI-INGESTOR] Extracted {len(file_paths)} "
            "viable files from audit report."
        )

        for idx, path in enumerate(file_paths):
            category = "proprietary_logic"
            if "prompt_guard" in path.lower() or "security" in path.lower():
                category = "security_guards"
            elif ("swarm" in path.lower() or "agent" in path.lower()
                  or "multiplexer" in path.lower()):
                category = "swarm_architectures"

            if path.endswith(".py"):
                data = self._parse_python_file(path)
            else:
                data = {"path": path, "summary": "Non-Python asset registered."}

            self.knowledge_graph[category].append(data)
            self.knowledge_graph["file_index"].append(path)

            if idx % 500 == 0 and idx > 0:
                print(f"[OMNI-INGESTOR] Ingested {idx} files...")

        # Save to active vault
        with open(KNOWLEDGE_VAULT, "w") as f:
            json.dump(self.knowledge_graph, f, indent=2)

        print(
            f"[OMNI-INGESTOR] Ingestion Complete. Vault compacted to {KNOWLEDGE_VAULT}")


if __name__ == "__main__":
    ingestor = XorasIngestor()
    ingestor.execute_ingestion()
