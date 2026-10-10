# Sovereign Publishing & Field Isolation Invariant

1. **Explicit Field Isolation**:
   - When populating web-based editors (DEV.to, Kaggle, GitHub Releases), NEVER dump raw unparsed markdown into default focused inputs.
   - Always clear existing field state, focus target inputs explicitly, and populate Title, Tags, Cover Image, and Body Markdown as isolated units.

2. **Zero Third-Party Branding Invariant**:
   - All public repositories, asset filenames, paper abstracts, and submission texts MUST use XORAS Systems / Lead 9 Council branding.
   - External tool/runtime names are strictly prohibited in public-facing URLs and documentation.

3. **Automated GUI Execution Standard**:
   - Web editor submissions must be automated via `ops/scripts/devto_gui_automator.py` or Playwright CDP scripting to prevent manual text-dump collisions and ensure reproducible end-to-end publishing.
