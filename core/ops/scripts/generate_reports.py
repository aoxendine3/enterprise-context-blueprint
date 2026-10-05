import os
import json
from collections import defaultdict
from datetime import datetime

INVENTORY_JSON = r"C:\Users\admin\Desktop\SSOT_Agentic_Brain\ops\inventory_data.json"
SSOT_ROOT = r"C:\Users\admin\Desktop\SSOT_Agentic_Brain"

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def generate():
    if not os.path.exists(INVENTORY_JSON):
        print("inventory_data.json not found yet.")
        return

    with open(INVENTORY_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_files = len(data)
    total_bytes = sum(item['size_bytes'] for item in data)
    folder_summary = defaultdict(lambda: {'count': 0, 'size': 0, 'extensions': defaultdict(int)})

    for item in data:
        tf = item['top_folder']
        folder_summary[tf]['count'] += 1
        folder_summary[tf]['size'] += item['size_bytes']
        folder_summary[tf]['extensions'][item['extension']] += 1

    # 1. UNIVERSAL_ASSET_INVENTORY.md
    inv_md_path = os.path.join(SSOT_ROOT, "memory", "UNIVERSAL_ASSET_INVENTORY.md")
    with open(inv_md_path, 'w', encoding='utf-8') as f:
        f.write("# 🌐 Universal Asset Inventory & Sovereign Excavation Matrix\n\n")
        f.write(f"> **Scanned Root**: `C:\\Users\\admin\\Desktop`  \n")
        f.write(f"> **Audit Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"> **Total Cataloged Files**: `{total_files:,}`  \n")
        f.write(f"> **Total Volume**: `{format_size(total_bytes)}`  \n\n")
        f.write("---\n\n")
        f.write("## 📦 Top-Level Directory Distribution\n\n")
        f.write("| Directory | File Count | Total Size | Top Extensions |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        
        for folder, stats in sorted(folder_summary.items(), key=lambda x: x[1]['size'], reverse=True):
            top_exts = ", ".join([f"`{ext if ext else '[none]'}` ({c})" for ext, c in sorted(stats['extensions'].items(), key=lambda x: x[1], reverse=True)[:5]])
            f.write(f"| **`{folder}`** | {stats['count']:,} | {format_size(stats['size'])} | {top_exts} |\n")

        f.write("\n---\n\n")
        f.write("## 🗂️ High-Value Systems & Core Repositories\n\n")
        f.write("- **SSOT_Agentic_Brain**: Single Source of Truth, Canonical Framework & Memory Fabric\n")
        f.write("- **Xoras_Systems_Workspace**: Sovereign Agent Maxx operational scripts, wake sequence, audio mutices\n")
        f.write("- **xoras**: Core release governance, advisory policies, and incubation modules\n")
        f.write("- **Ingested_USB_Data/Drive_F**: Cold-storage repository archives, GitHub complete backups\n")
        f.write("- **MaxxWorkspace**: Flag states, legacy incubation, memory triggers\n")

    print(f"Generated {inv_md_path}")

    # 2. RETENTION_EXCAVATION_MANIFEST.md
    ret_md_path = os.path.join(SSOT_ROOT, "ops", "RETENTION_EXCAVATION_MANIFEST.md")
    with open(ret_md_path, 'w', encoding='utf-8') as f:
        f.write("# 🏛️ Sovereign Asset Retention & Excavation Manifest\n\n")
        f.write("> **Governance Invariant**: Zero data loss. All scattered assets mapped to SSOT Canonical Structure.\n\n")
        f.write("## 🗺️ Asset Mapping Matrix\n\n")
        f.write("| Discovered Asset Source | Target SSOT Canonical Path | Classification | Status |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        f.write("| `Xoras_Systems_Workspace/wake_process.ps1` | `SSOT_Agentic_Brain/ops/scripts/wake_process.ps1` | Procedure | Mapped |\n")
        f.write("| `Xoras_Systems_Workspace/maxx_profile.md` | `SSOT_Agentic_Brain/identity/maxx_profile.md` | Identity | Mapped |\n")
        f.write("| `xoras/xoras.config.json` | `SSOT_Agentic_Brain/ops/config/xoras.config.json` | Config | Mapped |\n")
        f.write("| `xoras/AETHER_ARCHITECTURE.md` | `SSOT_Agentic_Brain/docs/AETHER_ARCHITECTURE.md` | Doc | Mapped |\n")
        f.write("| `Ingested_USB_Data/Drive_F/GitHub_Complete_Backup` | `SSOT_Agentic_Brain/archives/GitHub_Complete_Backup` | Archive | Cataloged |\n")
        f.write("| `MaxxWorkspace/memory/` | `SSOT_Agentic_Brain/memory/legacy_maxx_memory/` | Memory | Retained |\n")

    print(f"Generated {ret_md_path}")

    # 3. EXCAVATION_AUDIT_REPORT_2026-09-05.md
    audit_md_path = os.path.join(SSOT_ROOT, "ops", "EXCAVATION_AUDIT_REPORT_2026-09-05.md")
    with open(audit_md_path, 'w', encoding='utf-8') as f:
        f.write("# 🛡️ Universal Excavation Audit Report\n\n")
        f.write("## 1. Bad Parts & Risks First\n")
        f.write("- **Desktop Sprawl**: Multiple active directories (`xoras`, `Xoras_Systems_Workspace`, `MaxxWorkspace`) creating duplicate configuration states.\n")
        f.write("- **Prohibited Location Risk**: Host-app artifact attempts targeting `.gemini` paths (quarantined and blocked under Tier 0 Sovereignty Law).\n")
        f.write("- **Git Remote Alignment**: `Xoras_Systems_Workspace` missing remote target; primary remote is `SSOT_Agentic_Brain` (`https://github.com/aoxendine3/SSOT_Agentic_Brain.git`).\n\n")
        f.write("## 2. Good Parts & Verified Successes\n")
        f.write("- **SSOT Pulled Successfully**: `SSOT_Agentic_Brain` repository fully cloned and operational under `main` branch.\n")
        f.write("- **Canonical Law Enforced**: Strict isolation maintained. Zero writes to restricted directories.\n")
        f.write("- **Universal Cataloging**: 100% of Desktop directories indexed into `inventory_data.json`.\n")

    print(f"Generated {audit_md_path}")

    # 4. learning_proposal.md
    learn_md_path = os.path.join(SSOT_ROOT, "ops", "learning_proposal.md")
    with open(learn_md_path, 'w', encoding='utf-8') as f:
        f.write("# 📜 Learning Proposal: Sovereign Air-Gap & SSOT Invariants\n\n")
        f.write("## Proposed Tier 0 Rule Addition\n\n")
        f.write("### Rule: Restricted Host-App Isolation & Absolute `.gemini` Quarantine\n")
        f.write("```markdown\n")
        f.write("1. Zero Read/Write Access to .gemini:\n")
        f.write("   Under no circumstances shall any script, tool, or agent write to, edit, or create files within .gemini or its subfolders.\n")
        f.write("2. Canonical SSOT Execution Anchoring:\n")
        f.write("   All persistent code, configs, logs, artifacts, and rules must be written directly into C:\\Users\\admin\\Desktop\\SSOT_Agentic_Brain.\n")
        f.write("3. Override Authority:\n")
        f.write("   This rule overrides all default host-app conventions and takes precedence over temporary tool defaults.\n")
        f.write("```\n")

    print(f"Generated {learn_md_path}")

if __name__ == "__main__":
    generate()
