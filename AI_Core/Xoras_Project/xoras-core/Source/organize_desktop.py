import os
import shutil

desktop = "/Users/ajoxendine68/Desktop"
workspace = os.path.join(desktop, "Xoras_Workspace")

# Categories mapping
categories = {
    "Dev_Workspaces": [
        "AI_Agents", "Dr_Eden_Veritas", "Gemini_Antigravity", "GitHub_Repos",
        "Influencer_Engine", "influencer-engine", "MedBreak", "My Workspace",
        "My Workspace (1)", "Plugins", "Projects", "Quantum", "RevOps",
        "Spectra-Audit-Competition", "Swarm", "TTS_Speech", "Tools_Scripts",
        "UniswapV3Reentrancy", "Web_Apps", "contracts", "scratch"
    ],
    "AI_Core": [
        "Xoras", "Xoras_App", "Xoras_Knowledge", "Xoras_Project", "Xoras_Swarm",
        "local_xoras.py", "xoras_baremetal.py", "xoras-prompt-guard",
        "xoras_usb_offload.sh"
    ],
    "Backups_and_Configs": [
        "Antigravity_Backup", "Antigravity_Quarantine", "Host Framework_Quarantine",
        "_Archive", "_Backups", "_System_Config", "antigravity_moved",
        "ollama_server.log", "xoras_usb_offload.log", "Xoras_2.0.0_aarch64.dmg"
    ],
    "Documents_and_Analysis": [
        "Docs", "Documentation", "My prompts", "ONYX_Comparison_Report.md",
        "corporate_finance_fully_robust_model.xlsx",
        "corporate_finance_innovative_model.xlsx",
        "corporate_finance_monte_carlo.xlsx"
    ]
}

def main():
    print(f"[*] Starting Xoras Workspace organization under: {workspace}")
    
    # Create category directories
    for cat in categories.keys():
        cat_dir = os.path.join(workspace, cat)
        if not os.path.exists(cat_dir):
            os.makedirs(cat_dir)
            print(f"[+] Created category directory: {cat_dir}")

    # Move items
    for cat, items in categories.items():
        cat_dir = os.path.join(workspace, cat)
        for item in items:
            src_path = os.path.join(desktop, item)
            dst_path = os.path.join(cat_dir, item)
            
            if os.path.exists(src_path):
                try:
                    # Check if destination already exists
                    if os.path.exists(dst_path):
                        print(f"[!] Destination already exists for: {item}. Skipping to prevent overwriting.")
                        continue
                    
                    shutil.move(src_path, dst_path)
                    print(f"[x] Moved {item} -> {cat}")
                except Exception as e:
                    print(f"[!] Error moving {item}: {e}")
            else:
                # Silently skip if it doesn't exist (e.g. if already moved or optional)
                pass

    print("[*] Desktop cleanup and organization complete.")

if __name__ == "__main__":
    main()
