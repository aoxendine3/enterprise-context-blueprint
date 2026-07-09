import os

# XORAS ASCENSION AGGREGATOR
# Coordinator for the 4 Elite Sub-Divisions (Sovereign, Forge, Quantum, Void)
DOCS_ROOT = os.path.join(os.path.expanduser("~"), "Desktop",
                         "Xoras_Project", "xoras-core", "Docs")
BLUEPRINT_PATH = (
    "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/"
    "Docs/XORAS_ASCENSION_BLUEPRINT.md"
)
DKNOWLEDGE_VAULTS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "XORAS_ACTIVE_KNOWLEDGE.json"),
    os.path.join(DOCS_ROOT, "XORAS_ACTIVE_KNOWLEDGE.json"),
    os.path.join(DOCS_ROOT, "XORAS_ACTIVE_KNOWLEDGE.json")
]


class AscensionCoordinator:
    def __init__(self):
        self.intel_streams = {
            "Sovereign": None,
            "Forge": None,
            "Quantum": None,
            "Void": None
        }

    def _format_blueprint(self):
        print("\n[COORDINATOR] Synthesizing data streams into Ascension Blueprint...")
        blueprint_content = "# XORAS ASCENSION BLUEPRINT\n\n"
        blueprint_content += (
            "> **Compiled Intelligence from the "
            "Sovereign Ascension Deployment**\n\n"
        )

        for division, intel in self.intel_streams.items():
            blueprint_content += f"## {division} Division\n"
            if intel:
                blueprint_content += f"{intel}\n\n"
            else:
                blueprint_content += "> Awaiting telemetry...\n\n"

        with open(BLUEPRINT_PATH, "w") as f:
            f.write(blueprint_content)
        print(f"[COORDINATOR] Blueprint synthesized to {BLUEPRINT_PATH}")

    def ingest_report(self, division_name: str, report_data: str):
        """Called manually or via agent callback when a division returns."""
        if division_name in self.intel_streams:
            print(
                f"[COORDINATOR] Incoming burst from {division_name} "
                f"Division. Size: {len(report_data)} bytes."
            )
            self.intel_streams[division_name] = report_data
            self._format_blueprint()


if __name__ == "__main__":
    coordinator = AscensionCoordinator()
    print("[ASCENSION] Coordinator active. Standing by for Division telemetry.")
