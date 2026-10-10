#!/usr/bin/env python3
"""
GitHub Fork Privatization & Governance Script
Finds all public forked repositories under the authenticated user account and sets visibility to PRIVATE.
"""
import subprocess
import json
import sys

def main():
    print("==========================================================================")
    print("  GITHUB REPOSITORY GOVERNANCE: PRIVATIZING FORKS & CLUTTER")
    print("==========================================================================")
    
    # 1. Fetch list of all public repositories
    cmd = ["gh", "repo", "list", "aoxendine3", "--visibility", "public", "--limit", "300", "--json", "name,nameWithOwner,isFork,visibility"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ Failed to fetch repos: {res.stderr}", file=sys.stderr)
        sys.exit(1)
        
    repos = json.loads(res.stdout)
    forked_repos = [r for r in repos if r.get("isFork")]
    
    print(f"Found {len(repos)} total public repositories, including {len(forked_repos)} forked repositories.\n")
    
    privatized_count = 0
    failed_count = 0
    
    for r in forked_repos:
        repo_name = r["nameWithOwner"]
        print(f"🔒 Setting {repo_name} to PRIVATE...")
        edit_cmd = ["gh", "repo", "edit", repo_name, "--visibility", "private", "--accept-visibility-change-consequences"]
        edit_res = subprocess.run(edit_cmd, capture_output=True, text=True)
        if edit_res.returncode == 0:
            print(f"    ✓ {repo_name} is now PRIVATE.")
            privatized_count += 1
        else:
            print(f"    ❌ Failed to privatize {repo_name}: {edit_res.stderr.strip()}", file=sys.stderr)
            failed_count += 1
            
    print("\n==========================================================================")
    print(f"  PRIVATIZATION COMPLETE: {privatized_count} privatized, {failed_count} failed.")
    print("==========================================================================")

if __name__ == "__main__":
    main()
