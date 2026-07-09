import sys
import traceback
import os
import requests
import logging
from pathlib import Path
from xoras_triplet_nexus import TripletNexus

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("XorasSelfHealer")

class XorasSelfHealer:
    """
    Tier 3 Autonomous Self-Healer. 
    Intercepts global python exceptions, queries the local Ollama LLM to generate 
    a patch, and passes the patch through the TripletNexus sandbox for validation.
    """
    def __init__(self, model="qwen3.5:4b", llm_endpoint="http://192.168.1.133:11434/api/generate"):
        self.model = model
        self.llm_endpoint = llm_endpoint
        self.nexus = TripletNexus()
        self.original_excepthook = sys.excepthook
        
        # Hook global sys exceptions
        sys.excepthook = self.handle_exception
        logger.info(f"Self-Healer initialized with local model: {self.model}")

    def generate_patch(self, file_path: Path, exception_str: str, source_code: str) -> Optional[str]:
        """Queries local Ollama to generate a clean syntax patch for the file."""
        prompt = f"""You are the Xoras Active Self-Healing Daemon. 
A critical runtime exception occurred in the following Python file: {file_path.name}

Exception Details:
{exception_str}

Source Code:
```python
{source_code}
```

Provide ONLY the completely rewritten, corrected Python source code. 
Do not include markdown formatting backticks or code blocks around the final output, just raw python code. 
Do not include explanations or comments. Just print the code."""

        logger.info(f"[HEALER] Querying local Ollama model '{self.model}' for patch...")
        try:
            response = requests.post(
                self.llm_endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=90.0
            )
            if response.status_code == 200:
                data = response.json()
                patched_code = data.get("response", "").strip()
                # Clean up markdown output blocks if the model included them
                if patched_code.startswith("```python"):
                    patched_code = patched_code[9:]
                if patched_code.startswith("```"):
                    patched_code = patched_code[3:]
                if patched_code.endswith("```"):
                    patched_code = patched_code[:-3]
                return patched_code.strip()
            else:
                logger.error(f"[HEALER] LLM API returned status {response.status_code}")
        except Exception as e:
            logger.error(f"[HEALER] Failed to query local LLM: {e}")
        return None

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        # Unhook temporarily to prevent recursive exception failures
        sys.excepthook = self.original_excepthook

        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.critical(f"[HEALER] CRITICAL FAULT DETECTED:\n{tb_str}")

        # Localize the failing frame/file
        tb = traceback.extract_tb(exc_traceback)
        target_file = None
        for frame in reversed(tb):
            if not frame.filename.startswith("<"):
                target_file = Path(frame.filename)
                break

        if not target_file or not target_file.exists():
            logger.error("[HEALER] Exception cannot be localized to a valid file. Halting.")
            sys.exit(1)

        logger.info(f"[HEALER] Fault localized to: {target_file.name}")

        try:
            with open(target_file, "r") as f:
                source_code = f.read()
        except Exception as e:
            logger.error(f"[HEALER] Failed to read source file: {e}")
            sys.exit(1)

        # Generate patch via local Ollama
        exception_str = f"Exception: {exc_type.__name__}: {exc_value}\n{tb_str}"
        patched_code = self.generate_patch(target_file, exception_str, source_code)

        if not patched_code:
            logger.error("[HEALER] Failed to generate patch. System halting.")
            sys.exit(1)

        # Route the patch through TripletNexus (AST checks, subprocess runtime test, atomic write)
        module_name = target_file.stem
        logger.info(f"[HEALER] Routing patch for '{module_name}' to TripletNexus verification sandbox...")
        
        success = self.nexus.execute_logic_mutation(module_name, patched_code)

        if success:
            logger.info(f"[HEALER] Target file '{target_file.name}' successfully healed and hot-swapped.")
            # Reboot the process to run the corrected file
            logger.info("[HEALER] Rebooting process to run the healed logic...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            logger.error(f"[HEALER] TripletNexus rejected the patch. Fault remains. Halting.")
            sys.exit(1)

if __name__ == "__main__":
    # Self-test demonstration
    healer = XorasSelfHealer()
    
    # We will trigger a synthetic exception to test the self-healing loop
    # Triggering ZeroDivisionError on purpose
    print("Triggering synthetic crash...")
    1 / 0
