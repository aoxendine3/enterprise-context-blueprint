import asyncio
import aiohttp
import time

# --- XORAS ASCENSION OVERRIDE ---
# Bypassing the standard research subagents.
# Utilizing direct, asynchronous API sweeps via the Ghost Multiplexer pipeline.

BLUEPRINT_PATH = (
    "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/"
    "Docs/XORAS_ASCENSION_BLUEPRINT.md"
)


class AscensionOverride:
    def __init__(self):
        self.queries = {
            "Sovereign": "decentralized autonomous AI agents architecture self-hosting",
            "Forge": "LLM agent prompt injection defense stability self-healing",
            "Quantum": "ultra-fast LLM inference DeepSpeed vectorized reasoning",
            "Void": "1-bit LLM extreme quantization minimal agent memory"
        }
        self.intel = {}

    async def _fetch_openalex(self, session, division, query):
        """Direct, raw extraction from the OpenAlex academic database."""
        url = (
            "https://api.openalex.org/works?"
            f"search={query}&sort=publication_date:desc&per-page=3"
        )
        print(f"[OVERRIDE] {division} Division initiating direct extraction...")
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    for work in data.get('results', []):
                        title = work.get('title', 'Unknown Title')
                        abstract = work.get('abstract_inverted_index', {})
                        # Reconstruct abstract if available
                        # (OpenAlex returns it inverted)
                        if abstract:
                            words = [""] * (max([max(positions)
                                            for positions in abstract.values()]) + 1)
                            for word, positions in abstract.items():
                                for pos in positions:
                                    words[pos] = word
                            abstract_text = " ".join(words)[:500] + "..."
                        else:
                            abstract_text = "No abstract available."
                        results.append(f"### {title}\n{abstract_text}")
                    return division, "\n\n".join(results)
                else:
                    return division, f"Extraction failed with status {response.status}"
        except Exception as e:
            return division, f"Extraction error: {e}"

    def _compile_blueprint(self):
        print("\n[OVERRIDE] Synthesizing raw data streams into Ascension Blueprint...")
        content = (
            "# XORAS ASCENSION BLUEPRINT\n\n"
            "> **Compiled Intelligence via Direct Override Extraction**\n\n"
        )
        for division, data in self.intel.items():
            content += f"## {division} Division\n{data}\n\n"

        with open(BLUEPRINT_PATH, "w") as f:
            f.write(content)
        print(f"[OVERRIDE] Blueprint synthesized to {BLUEPRINT_PATH}")

    async def execute_strike(self):
        print("\n==========================================")
        print("    IGNITING ASCENSION OVERRIDE           ")
        print("==========================================\n")
        start = time.time()

        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_openalex(session, div, query)
                     for div, query in self.queries.items()]
            results = await asyncio.gather(*tasks)

            for division, data in results:
                self.intel[division] = data

        self._compile_blueprint()
        duration = time.time() - start
        print(f"\n[OVERRIDE] Strike complete in {duration:.2f} seconds.")


if __name__ == "__main__":
    override = AscensionOverride()
    asyncio.run(override.execute_strike())
