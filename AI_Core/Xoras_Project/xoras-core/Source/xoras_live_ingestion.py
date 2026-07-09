import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

# Ensure local Source paths work — must precede local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xoras_langgraph_engine import XorasLangGraph  # noqa: E402
from xoras_vector_db import ingest_document  # noqa: E402


def fetch_live_swarm_intelligence():
    print("[Sovereign Core] Reaching out to external open-source grids (arXiv)...")
    url = (
        "http://export.arxiv.org/api/query"
        "?search_query=all:agent+swarm+intelligence&start=0&max_results=3"
    )
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)

        # arXiv atom namespace
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', ns)

        count = len(entries)
        print(f"[Sovereign Core] Successfully intercepted {count} live research nodes.")

        # Instantiate the Engine
        engine = XorasLangGraph()

        for idx, entry in enumerate(entries):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip()
            link = entry.find('atom:id', ns).text

            payload = (
                f"Process external intelligence node. "
                f"Title: {title}. Target: {summary}"
            )

            # Route through the Ghost Node Multiplexers via LangGraph
            state = engine.run(payload, ghost_execution=False)

            if state.get("blocked"):
                errors = state.get('errors')
                print(
                    f"[Sovereign Core] Payload {idx} BLOCKED by PromptGuard. "
                    f"Reason: {errors}"
                )
            else:
                # Synthesize into local file format for VectorDB ingestion
                temp_file = f"temp_live_ingest_{idx}.md"
                with open(temp_file, "w") as f:
                    f.write(
                        f"# {title}\n\n## Live Source\n{link}\n\n"
                        f"## Engine Analysis\n{state.get('output', '')}"
                        f"\n\n## Raw Intelligence\n{summary}"
                    )

                # Ingest into Semantic Memory
                ingest_document(temp_file, domain="live_open_source")
                short_title = title[:40]
                print(
                    f"[Sovereign Core] Intelligence Node "
                    f"'{short_title}...' ingested into Semantic Memory."
                )
                os.remove(temp_file)

    except Exception as e:
        print(f"[Sovereign Core] Network intercept failed: {e}")


if __name__ == "__main__":
    fetch_live_swarm_intelligence()
