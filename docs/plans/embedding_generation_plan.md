# Embedding Generation Plan

## Objective
Generate text embeddings using the Gemini API and store them in the existing LanceDB vector table `demo_vectors`.

## Steps
1. **Create a new script** `ops/scripts/generate_embeddings.py` that:
   - Loads a CSV file `data/sample_texts.csv` (must contain a `text` column).
   - Uses the Gemini Embedding API (`google.generativeai.embed_content`) to compute a vector for each row.
   - Connects to the LanceDB vault (`VAULT_DIR` from `zenith_env.sh`).
   - Upserts the vectors into the `demo_vectors` table with a schema `{id: int, text: str, embedding: list[float]}`.
2. **Add a sample data file** `data/sample_texts.csv` with a few example sentences if it does not already exist.
3. **Update README** (`README.md`) with a brief usage example and required environment variable `GEMINI_API_KEY`.

## Review Checklist
- [ ] All new files are under the canonical workspace `/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain`.
- [ ] No existing files are modified without prior review.
- [ ] The script uses only the Gemini API (no additional external dependencies beyond `google-generativeai` which is already in the environment).
- [ ] The script respects the `VAULT_DIR` environment variable defined in `zenith_env.sh`.
- [ ] Provides clear console output and error handling.

## Next Action
Await approval to create the script and sample data file.
