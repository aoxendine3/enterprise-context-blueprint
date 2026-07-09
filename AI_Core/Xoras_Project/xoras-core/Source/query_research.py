from xoras_vector_db import ingest_document
from xoras_langgraph_engine import XorasLangGraph
import os
import sys
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def search_and_analyze(query_str: str, max_results: int = 2):
    print(
        f"\n[Sovereign Core] Initiating open-source intelligence scan for: '{query_str}'")
    encoded_query = urllib.parse.quote(query_str)
    url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', ns)

        if not entries:
            print("[Sovereign Core] No research nodes found for this query.")
            return

        print(
            f"[Sovereign Core] Intercepted {len(entries)} nodes. Processing through LangGraph engine...")
        engine = XorasLangGraph()

        for idx, entry in enumerate(entries):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip()
            link = entry.find('atom:id', ns).text

            print(f"\n--- Node [{idx+1}]: {title[:60]}... ---")
            payload = f"Extract core architectural innovations and cognitive mechanisms from: {summary}"

            # Run through engine
            state = engine.run(payload, ghost_execution=False)

            if state.get("blocked"):
                print(
                    f"[BLOCKED] PromptGuard intercepted threat. Reason: {state.get('errors')}")
            else:
                print(f"[ANALYSIS]:\n{state.get('output', '')}\n")

                # Write to temp file for semantic ingestion
                temp_filename = f"temp_research_{idx}.md"
                with open(temp_filename, "w", encoding="utf-8") as f:
                    f.write(
                        f"# {title}\n\n"
                        f"**Source:** {link}\n\n"
                        f"## Innovation Analysis\n{state.get('output', '')}\n\n"
                        f"## Abstract\n{summary}\n"
                    )

                # Ingest to VectorDB
                ingest_document(temp_filename, domain="research_intelligence")
                os.remove(temp_filename)
                print(f"[SUCCESS] Ingested node into local Semantic Memory.")

    except Exception as e:
        print(f"[Sovereign Core] Scan failed: {e}")


if __name__ == "__main__":
    # If query is passed, use it, otherwise default to cognitive routing
    query = sys.argv[1] if len(
        sys.argv) > 1 else "cognitive architectures memory routing"
    search_and_analyze(query)
