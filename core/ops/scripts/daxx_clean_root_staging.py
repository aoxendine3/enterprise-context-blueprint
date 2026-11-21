import os
import shutil


def main():
    """Entry point. All side effects run only when invoked directly."""
    ROOT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"

    # Map of items to move and their canonical destinations
    MOVES = {
        # Reports & Audit Receipts -> memory/catch_log/ or docs/audits/
        "DAXX_report.md": "docs/audits/DAXX_report.md",
        "REMEDIATION_PLAN.md": "docs/plans/REMEDIATION_PLAN.md",
        "STRIPE_INTEGRATION_TODO.md": "docs/plans/STRIPE_INTEGRATION_TODO.md",
        "cleanroom_receipt_v2_arm64_1792111283.json": "memory/catch_log/cleanroom_receipt_v2_arm64_1792111283.json",
        "lean_differential_receipt.json": "memory/catch_log/lean_differential_receipt.json",
        "knowledge_base.json": "barn/identity/knowledge_base.json",
    
        # Diffs and patches -> scratch/
        "diff_before_reset.txt": "scratch/diff_before_reset.txt",
        "diff_windows.patch": "scratch/diff_windows.patch",
    
        # HTML mockups & assets -> workspaces/xoras_agent_framework/web/ or archives/
        "enterprise.html": "barn/legacy_web/enterprise.html",
        "index.html": "barn/legacy_web/index.html",
    
        # Docker, builds, gyps -> ops/deployment/
        "Dockerfile.upgp": "ops/docker/Dockerfile.upgp",
        "docker-compose.yml": "ops/docker/docker-compose.yml",
        "binding.gyp": "ops/native/binding.gyp",
        "upgp_simulator.wasm": "capabilities/upgp_simulator.wasm",
        "libsovra_simd.dylib": "ops/native/libsovra_simd.dylib",
    
        # Scripts dumped in root -> ops/scripts/
        "run_video.sh": "ops/scripts/run_video.sh",
        "video_creation.sh": "ops/scripts/video_creation.sh",
        "telemetry_server.py": "ops/scripts/telemetry_server.py",
    
        # Certificates / Keys -> ops/security/certs/
        "cert.pem": "ops/security/certs/cert.pem",
        "key.pem": "ops/security/certs/key.pem",
    
        # Personas package -> barn/identity/
        "Lekh AI Pro All Personas.kaila-persona-pack": "barn/identity/Lekh AI Pro All Personas.kaila-persona-pack",
    
        # Wan2.1 dead/unplugged model symlink -> barn/symlinks/
        "Wan2.1-T2V-1.3B": "barn/symlinks/Wan2.1-T2V-1.3B"
    }

    print("=== DAXX ROOT DIRECTORY CANONICAL RESTORATION ===")
    for src_name, dst_rel in MOVES.items():
        src_p = os.path.join(ROOT, src_name)
        dst_p = os.path.join(ROOT, dst_rel)
        if os.path.exists(src_p) or os.path.islink(src_p):
            os.makedirs(os.path.dirname(dst_p), exist_ok=True)
            shutil.move(src_p, dst_p)
            print(f"✅ Moved: {src_name} -> {dst_rel}")
        else:
            print(f"⏭️ Not in root: {src_name}")



if __name__ == "__main__":
    main()
